import socket
import threading
import time

import usb1

# AOA host: handshakes a connected Android phone into accessory mode,
# pipes its bulk endpoints to a local TCP socket.
# https://source.android.com/docs/core/interaction/accessories/aoa

AOA_VID = 0x18D1  # Google
AOA_PIDS = (0x2D00, 0x2D01, 0x2D04, 0x2D05)  # accessory variants (with/without ADB, with/without audio)

AOA_GET_PROTOCOL = 51
AOA_SEND_STRING = 52
AOA_START = 53

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

# Multiple in-flight transfers + 256 KB envelopes keep the USB controller
# pipelined across kernel→userspace syscalls.
NUM_IN_TRANSFERS = 4
IN_BUFFER_SIZE = 256 * 1024
OUT_TIMEOUT_MS = 5000
EVENT_LOOP_TICK_S = 0.1
DRAIN_DEADLINE_S = 2.0


class ShuttleState:
    def __init__(self, upstream: socket.socket) -> None:
        self.upstream = upstream
        self.socket_lock = threading.Lock()
        self.stop = threading.Event()
        self.failure: str | None = None
        self.bytes_from_phone = 0
        self.bytes_to_phone = 0
        self.started = time.monotonic()

    def fail(self, message: str) -> None:
        if self.failure is None:
            self.failure = message
            log(message)
        self.stop.set()

    def summary(self) -> str:
        elapsed = int(time.monotonic() - self.started)
        return f"pipe done: to_phone={self.bytes_to_phone}B from_phone={self.bytes_from_phone}B uptime={elapsed}s"

    def on_in_complete(self, transfer: usb1.USBTransfer) -> None:
        if self.stop.is_set():
            return

        status = transfer.getStatus()
        if status == usb1.TRANSFER_CANCELLED:
            return

        if status != usb1.TRANSFER_COMPLETED:
            self.fail(f"IN transfer status={status}")
            return

        length = transfer.getActualLength()
        if length > 0:
            try:
                with self.socket_lock:
                    self.upstream.sendall(bytes(transfer.getBuffer()[:length]))
            except OSError as exception:
                self.fail(f"upstream write error: {exception}")
                return

            self.bytes_from_phone += length

        try:
            transfer.submit()
        except usb1.USBError as exception:
            self.fail(f"resubmit IN failed: {exception}")


def main() -> None:
    log(f"aoa-bridge starting; upstream={UPSTREAM_HOST}:{UPSTREAM_PORT}")
    while True:
        try:
            _run_once()
        except Exception as exception:
            log(f"loop error: {type(exception).__name__}: {exception}")
        finally:
            time.sleep(POLL_INTERVAL)


def _run_once() -> None:
    with usb1.USBContext() as context:
        handle = _ensure_accessory(context)
        if handle is None:
            return

        device = handle.getDevice()
        log(f"accessory ready vid={device.getVendorID():04x} pid={device.getProductID():04x}; opening pipe")

        endpoints = _open_bulk_endpoints(handle)
        if endpoints is None:
            return
        endpoint_in, endpoint_out = endpoints

        upstream = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        upstream.connect((UPSTREAM_HOST, UPSTREAM_PORT))
        log(f"upstream connected; piping (in_ep=0x{endpoint_in:02x}, out_ep=0x{endpoint_out:02x})")

        try:
            _shuttle(context, handle, endpoint_in, endpoint_out, upstream)
        finally:
            _shutdown_quietly(upstream)
            upstream.close()
            log("accessory pipe closed")


def _ensure_accessory(context: usb1.USBContext) -> usb1.USBDeviceHandle | None:
    handle = _open_accessory(context)
    if handle is not None:
        return handle

    candidate = _find_handshake_candidate(context)
    if candidate is None:
        return None

    log(f"handshaking candidate vid={candidate.getVendorID():04x} pid={candidate.getProductID():04x}")
    candidate_handle = candidate.open()
    success = _do_handshake(candidate_handle)
    candidate_handle.close()

    if not success:
        return None

    # Phone re-enumerates with the AOA pid. Slow phones (Pixels in low-power)
    # can take >3 s; bounded retry rather than a fixed sleep.
    deadline = time.monotonic() + POST_HANDSHAKE_TIMEOUT_S
    while time.monotonic() < deadline:
        time.sleep(POST_HANDSHAKE_POLL_S)
        handle = _open_accessory(context)
        if handle is not None:
            return handle

    log(f"post-handshake accessory not found within {POST_HANDSHAKE_TIMEOUT_S}s")
    return None


def _open_accessory(context: usb1.USBContext) -> usb1.USBDeviceHandle | None:
    for product_id in AOA_PIDS:
        handle = context.openByVendorIDAndProductID(AOA_VID, product_id, skip_on_error=True)
        if handle is not None:
            return handle
    return None


def _find_handshake_candidate(context: usb1.USBContext) -> usb1.USBDevice | None:
    for device in context.getDeviceList(skip_on_error=True):
        try:
            vendor = device.getVendorID()
            product = device.getProductID()
            device_class = device.getDeviceClass()
        except usb1.USBError as exception:
            log(f"could not inspect device: {exception}")
            continue

        if vendor == AOA_VID and product in AOA_PIDS:
            continue
        if device_class == 0x09:
            continue

        return device
    return None


def _do_handshake(handle: usb1.USBDeviceHandle) -> bool:
    try:
        protocol_bytes = handle.controlRead(
            request_type=0xC0,
            request=AOA_GET_PROTOCOL,
            value=0,
            index=0,
            length=2,
            timeout=1000,
        )
    except usb1.USBError as exception:
        log(f"GET_PROTOCOL failed: {exception}")
        return False

    if len(protocol_bytes) != 2:
        log(f"GET_PROTOCOL returned {len(protocol_bytes)} bytes")
        return False

    protocol = int.from_bytes(protocol_bytes, "little")
    if protocol < 1:
        log(f"device does not support AOA (protocol={protocol})")
        return False

    log(f"device supports AOA protocol v{protocol}")

    try:
        for index, value in enumerate([MANUFACTURER, MODEL, DESCRIPTION, VERSION, URI, SERIAL]):
            handle.controlWrite(
                request_type=0x40,
                request=AOA_SEND_STRING,
                value=0,
                index=index,
                data=value.encode("utf-8") + b"\x00",
                timeout=1000,
            )
        handle.controlWrite(
            request_type=0x40,
            request=AOA_START,
            value=0,
            index=0,
            data=b"",
            timeout=1000,
        )
    except usb1.USBError as exception:
        log(f"AOA setup failed: {exception}")
        return False

    return True


def _open_bulk_endpoints(handle: usb1.USBDeviceHandle) -> tuple[int, int] | None:
    # Detach any kernel driver auto-bound to interface 0 before claiming.
    # No explicit setConfiguration() — the kernel already configures the
    # device at enumeration, and an extra SET_CONFIGURATION trips an EIO
    # on accessory+ADB variants (pid 0x2d01 / 0x2d05) where interface 1
    # is also live.
    if handle.kernelDriverActive(0):
        handle.detachKernelDriver(0)

    try:
        handle.claimInterface(0)
    except usb1.USBError as exception:
        log(f"claimInterface(0) failed: {exception}")
        return None

    device = handle.getDevice()
    configuration = next(iter(device.iterConfigurations()))
    interface = configuration[0]
    setting = interface[0]

    endpoint_in: int | None = None
    endpoint_out: int | None = None
    for endpoint in setting.iterEndpoints():
        address = endpoint.getAddress()
        if address & 0x80:
            endpoint_in = address
        else:
            endpoint_out = address

    if endpoint_in is None or endpoint_out is None:
        log("could not find bulk IN/OUT endpoints on accessory interface")
        return None

    return endpoint_in, endpoint_out


def _shuttle(
    context: usb1.USBContext,
    handle: usb1.USBDeviceHandle,
    endpoint_in: int,
    endpoint_out: int,
    upstream: socket.socket,
) -> None:
    state = ShuttleState(upstream=upstream)

    in_transfers: list[usb1.USBTransfer] = []
    for _ in range(NUM_IN_TRANSFERS):
        transfer = handle.getTransfer()
        transfer.setBulk(endpoint_in, IN_BUFFER_SIZE, callback=state.on_in_complete)
        transfer.submit()
        in_transfers.append(transfer)

    event_thread = threading.Thread(target=_event_loop, args=(context, state), daemon=True, name="libusb-events")
    event_thread.start()

    try:
        _pump_upstream_to_usb(handle, endpoint_out, state)
    finally:
        _drain_and_join(in_transfers, event_thread, state)
        log(state.summary())


def _event_loop(context: usb1.USBContext, state: ShuttleState) -> None:
    while not state.stop.is_set():
        try:
            context.handleEventsTimeout(EVENT_LOOP_TICK_S)
        except usb1.USBError as exception:
            state.fail(f"event loop error: {exception}")
            return


def _pump_upstream_to_usb(handle: usb1.USBDeviceHandle, endpoint_out: int, state: ShuttleState) -> None:
    # ZED → phone is mostly small HTTP response framing, so a synchronous
    # bulkWrite per recv is fine here — the throughput cap is the other
    # direction. Short socket timeout so the loop checks state.stop on
    # idle and exits promptly when the IN side fails.
    state.upstream.settimeout(EVENT_LOOP_TICK_S)
    while not state.stop.is_set():
        try:
            data = state.upstream.recv(IN_BUFFER_SIZE)
        except TimeoutError:
            continue
        except OSError as exception:
            state.fail(f"upstream read error: {exception}")
            return

        if not data:
            state.fail("upstream closed")
            return

        try:
            handle.bulkWrite(endpoint_out, data, timeout=OUT_TIMEOUT_MS)
        except usb1.USBError as exception:
            state.fail(f"USB write error: {exception}")
            return

        state.bytes_to_phone += len(data)


def _drain_and_join(
    in_transfers: list[usb1.USBTransfer],
    event_thread: threading.Thread,
    state: ShuttleState,
) -> None:
    # Cancel in-flight IN transfers; their callbacks fire with status
    # TRANSFER_CANCELLED on the event thread. Wait for that to drain
    # before stopping the event loop, otherwise libusb logs warnings at
    # context teardown about transfers still in flight.
    for transfer in in_transfers:
        try:
            if transfer.isSubmitted():
                transfer.cancel()
        except usb1.USBError:
            pass

    deadline = time.monotonic() + DRAIN_DEADLINE_S
    while time.monotonic() < deadline:
        if all(not transfer.isSubmitted() for transfer in in_transfers):
            break

        time.sleep(0.05)

    state.stop.set()
    event_thread.join(timeout=DRAIN_DEADLINE_S)


def _shutdown_quietly(connection: socket.socket) -> None:
    try:
        connection.shutdown(socket.SHUT_RDWR)
    except OSError:
        pass


def log(message: str) -> None:
    print(message, flush=True)
