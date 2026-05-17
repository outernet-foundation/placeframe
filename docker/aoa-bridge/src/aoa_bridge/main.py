import errno
import select
import socket
import struct
import time

import usb.core
import usb.util

# AOA host: handshakes a connected Android phone into accessory mode,
# pipes its bulk endpoints to a local TCP socket.
# https://source.android.com/docs/core/interaction/accessories/aoa

AOA_VID = 0x18D1  # Google
AOA_PIDS = (0x2D00, 0x2D01, 0x2D04, 0x2D05)  # accessory variants (with/without ADB, with/without audio)

AOA_GET_PROTOCOL = 51
AOA_SEND_STRING = 52
AOA_START = 53

STRING_MANUFACTURER = 0
STRING_MODEL = 1
STRING_DESCRIPTION = 2
STRING_VERSION = 3
STRING_URI = 4
STRING_SERIAL = 5

# Must match accessory_filter.xml; mismatch = no app dispatch.
MANUFACTURER = "Placeframe"
MODEL = "ZED-Box"
DESCRIPTION = "Placeframe ZED capture rig"
VERSION = "1"
URI = "https://placeframe.io"
SERIAL = "0"

UPSTREAM_HOST = "127.0.0.1"
UPSTREAM_PORT = 9000

POLL_INTERVAL = 1.0
POST_HANDSHAKE_TIMEOUT_S = 10.0
POST_HANDSHAKE_POLL_S = 0.25


def log(msg: str) -> None:
    print(msg, flush=True)


def main() -> None:
    log(f"aoa-bridge starting; upstream={UPSTREAM_HOST}:{UPSTREAM_PORT}")
    while True:
        try:
            accessory = _ensure_accessory()
            if accessory is None:
                continue

            log(f"accessory ready vid={accessory.idVendor:04x} pid={accessory.idProduct:04x}; opening pipe")
            endpoints = _open_endpoints(accessory)
            if endpoints is None:
                continue
            ep_in, ep_out = endpoints

            upstream = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            upstream.connect((UPSTREAM_HOST, UPSTREAM_PORT))
            log(
                f"upstream connected; piping (in_ep=0x{ep_in.bEndpointAddress:02x}, out_ep=0x{ep_out.bEndpointAddress:02x})"
            )

            try:
                _shuttle(accessory, ep_in, ep_out, upstream)
            finally:
                try:
                    upstream.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass
                upstream.close()
                usb.util.dispose_resources(accessory)
                log("accessory pipe closed")
        except Exception as e:
            log(f"loop error: {type(e).__name__}: {e}")
        finally:
            time.sleep(POLL_INTERVAL)


def _ensure_accessory() -> usb.core.Device | None:
    accessory = _find_accessory()
    if accessory is not None:
        return accessory

    candidate = _find_handshake_candidate()
    if candidate is None:
        return None

    log(f"handshaking candidate vid={candidate.idVendor:04x} pid={candidate.idProduct:04x}")
    if not _do_handshake(candidate):
        return None

    # Phone re-enumerates with the AOA pid. Slow phones (Pixels in low-power)
    # can take >3 s; bounded retry rather than a fixed sleep.
    deadline = time.monotonic() + POST_HANDSHAKE_TIMEOUT_S
    while time.monotonic() < deadline:
        time.sleep(POST_HANDSHAKE_POLL_S)
        accessory = _find_accessory()
        if accessory is not None:
            return accessory

    log(f"post-handshake accessory not found within {POST_HANDSHAKE_TIMEOUT_S}s")
    return None


def _find_accessory() -> usb.core.Device | None:
    for pid in AOA_PIDS:
        device = usb.core.find(idVendor=AOA_VID, idProduct=pid)
        if device is not None:
            return device
    return None


def _find_handshake_candidate() -> usb.core.Device | None:
    for device in usb.core.find(find_all=True):
        # Skip devices already flipped into accessory mode (would have been
        # found by _find_accessory above); skip hubs. Stock-mode Android
        # phones — including Pixels at vid=0x18D1 with MTP/PTP pids — are
        # valid candidates.
        if device.idVendor == AOA_VID and device.idProduct in AOA_PIDS:
            continue
        try:
            is_hub = device.bDeviceClass == 0x09
        except Exception as e:
            log(f"could not inspect device class: {e}")
            continue
        if is_hub:
            continue
        return device
    return None


def _do_handshake(candidate: usb.core.Device) -> bool:
    try:
        protocol_bytes = candidate.ctrl_transfer(
            bmRequestType=0xC0,
            bRequest=AOA_GET_PROTOCOL,
            wValue=0,
            wIndex=0,
            data_or_wLength=2,
            timeout=1000,
        )
    except usb.core.USBError as e:
        log(f"GET_PROTOCOL failed: {e}")
        return False

    if len(protocol_bytes) != 2:
        log(f"GET_PROTOCOL returned {len(protocol_bytes)} bytes")
        return False
    protocol = struct.unpack("<H", bytes(protocol_bytes))[0]
    if protocol < 1:
        log(f"device does not support AOA (protocol={protocol})")
        return False
    log(f"device supports AOA protocol v{protocol}")

    try:
        for index, value in (
            (STRING_MANUFACTURER, MANUFACTURER),
            (STRING_MODEL, MODEL),
            (STRING_DESCRIPTION, DESCRIPTION),
            (STRING_VERSION, VERSION),
            (STRING_URI, URI),
            (STRING_SERIAL, SERIAL),
        ):
            candidate.ctrl_transfer(
                bmRequestType=0x40,
                bRequest=AOA_SEND_STRING,
                wValue=0,
                wIndex=index,
                data_or_wLength=value.encode("utf-8") + b"\x00",
                timeout=1000,
            )
        candidate.ctrl_transfer(
            bmRequestType=0x40,
            bRequest=AOA_START,
            wValue=0,
            wIndex=0,
            data_or_wLength=None,
            timeout=1000,
        )
    except usb.core.USBError as e:
        log(f"AOA setup failed: {e}")
        return False

    return True


def _open_endpoints(accessory: usb.core.Device) -> tuple[usb.core.Endpoint, usb.core.Endpoint] | None:
    # Detach any kernel driver auto-bound to interface 0 so pyusb can claim
    # it on first read/write. No explicit set_configuration() — the kernel
    # already configures the device at enumeration, and an extra
    # SET_CONFIGURATION control transfer trips an EIO on accessory+ADB
    # variants (pid 0x2d01 / 0x2d05) where interface 1 is also live.
    try:
        if accessory.is_kernel_driver_active(0):
            accessory.detach_kernel_driver(0)
    except (usb.core.USBError, NotImplementedError):
        pass

    interface = accessory.get_active_configuration()[(0, 0)]
    ep_in = usb.util.find_descriptor(
        interface,
        custom_match=lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_IN,
    )
    ep_out = usb.util.find_descriptor(
        interface,
        custom_match=lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_OUT,
    )

    if ep_in is None or ep_out is None:
        log("could not find bulk IN/OUT endpoints on accessory interface")
        return None
    return ep_in, ep_out


def _shuttle(
    accessory: usb.core.Device,
    ep_in: usb.core.Endpoint,
    ep_out: usb.core.Endpoint,
    upstream: socket.socket,
) -> None:
    # select on TCP + short USB read timeout interleaves both directions
    # in one loop (pyusb has no async).
    upstream.setblocking(False)
    buf_size = ep_in.wMaxPacketSize * 16
    bytes_from_phone = 0
    bytes_to_phone = 0
    pipe_started = time.monotonic()
    last_read = pipe_started
    last_write = pipe_started

    def context() -> str:
        now = time.monotonic()
        return (
            f"to_phone={bytes_to_phone}B from_phone={bytes_from_phone}B "
            f"since_last_write={int((now - last_write) * 1000)}ms "
            f"since_last_read={int((now - last_read) * 1000)}ms "
            f"uptime={int(now - pipe_started)}s"
        )

    while True:
        try:
            chunk = accessory.read(ep_in.bEndpointAddress, buf_size, timeout=50)
        except usb.core.USBTimeoutError:
            chunk = None
        except usb.core.USBError as e:
            log(f"USB read error: {e} [{context()}]")
            return

        if chunk is not None and len(chunk) > 0:
            bytes_from_phone += len(chunk)
            last_read = time.monotonic()
            try:
                upstream.sendall(bytes(chunk))
            except OSError as e:
                log(f"upstream write error: {e} [{context()}]")
                return

        try:
            ready, _, _ = select.select([upstream], [], [], 0.0)
        except OSError as e:
            log(f"select error: {e} [{context()}]")
            return

        if not ready:
            continue

        try:
            data = upstream.recv(buf_size)
        except OSError as e:
            if e.errno == errno.EAGAIN:
                data = b""
            else:
                log(f"upstream read error: {e} [{context()}]")
                return

        if len(data) == 0:
            log(f"upstream closed [{context()}]")
            return

        try:
            accessory.write(ep_out.bEndpointAddress, data, timeout=5000)
        except usb.core.USBError as e:
            log(f"USB write error: {e} [{context()}]")
            return

        bytes_to_phone += len(data)
        last_write = time.monotonic()
