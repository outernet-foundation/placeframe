import logging
import logging.config
import os
import socket
import sys
import threading
import time
from logging.handlers import RotatingFileHandler
from pathlib import Path
from tempfile import mkdtemp

import usb1
from pythonjsonlogger.json import JsonFormatter

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

NUM_IN_TRANSFERS = 4
IN_BUFFER_SIZE = 256 * 1024
OUT_TIMEOUT_MS = 5000
EVENT_LOOP_TICK_S = 0.1
DRAIN_DEADLINE_S = 2.0

LOG_DIR = Path(os.environ.get("ZED_LOG_DIR", "/var/log/zed-capture"))
LOG_FILE_NAME = "aoa-bridge.jsonl"
LOG_MAX_BYTES = 50 * 1024 * 1024
LOG_BACKUP_COUNT = 5


def _resolve_log_dir(requested: Path) -> Path:
    try:
        requested.mkdir(parents=True, exist_ok=True)
        return requested
    except PermissionError:
        return Path(mkdtemp(prefix="aoa-bridge-logs-"))


_LOG_DIR = _resolve_log_dir(LOG_DIR)

logging.config.dictConfig({
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": JsonFormatter,
            "format": "%(levelname)s %(name)s %(message)s",
            "rename_fields": {"levelname": "level"},
            "timestamp": True,
        },
    },
    "handlers": {
        "file": {
            "()": RotatingFileHandler,
            "formatter": "json",
            "filename": str(_LOG_DIR / LOG_FILE_NAME),
            "maxBytes": LOG_MAX_BYTES,
            "backupCount": LOG_BACKUP_COUNT,
            "encoding": "utf-8",
        },
        "stream": {
            "class": "logging.StreamHandler",
            "formatter": "json",
            "stream": sys.stdout,
        },
    },
    "root": {
        "handlers": ["file", "stream"],
        "level": "INFO",
    },
})

logger = logging.getLogger(__name__)


class ShuttleState:
    def __init__(self, upstream: socket.socket) -> None:
        self.upstream = upstream
        self.socket_lock = threading.Lock()
        self.stop = threading.Event()
        self.failure: str | None = None
        self.bytes_from_phone = 0
        self.bytes_to_phone = 0
        self.started = time.monotonic()

    def fail(self, template: str, *args: object) -> None:
        if self.failure is None:
            self.failure = template % args if args else template
            logger.info(template, *args)
        self.stop.set()

    def summary_args(self) -> tuple[int, int, int]:
        elapsed = int(time.monotonic() - self.started)
        return self.bytes_to_phone, self.bytes_from_phone, elapsed

    def on_in_complete(self, transfer: usb1.USBTransfer) -> None:
        if self.stop.is_set():
            return

        status = transfer.getStatus()
        if status == usb1.TRANSFER_CANCELLED:
            return

        if status != usb1.TRANSFER_COMPLETED:
            self.fail("IN transfer status=%s", status)
            return

        length = transfer.getActualLength()
        if length > 0:
            try:
                with self.socket_lock:
                    self.upstream.sendall(bytes(transfer.getBuffer()[:length]))
            except OSError as exception:
                self.fail("upstream write error: %s", exception)
                return

            self.bytes_from_phone += length

        try:
            transfer.submit()
        except usb1.USBError as exception:
            self.fail("resubmit IN failed: %s", exception)


def main() -> None:
    logger.info("aoa-bridge starting; upstream=%s:%s", UPSTREAM_HOST, UPSTREAM_PORT)
    while True:
        try:
            _run_once()
        except Exception as exception:
            logger.info("loop error: %s: %s", type(exception).__name__, exception)
        finally:
            time.sleep(POLL_INTERVAL)


def _run_once() -> None:
    with usb1.USBContext() as context:
        handle = _ensure_accessory(context)
        if handle is None:
            return

        device = handle.getDevice()
        logger.info(
            "accessory ready vid=%04x pid=%04x; opening pipe",
            device.getVendorID(),
            device.getProductID(),
        )

        endpoints = _open_bulk_endpoints(handle)
        if endpoints is None:
            return
        endpoint_in, endpoint_out = endpoints

        upstream = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        upstream.connect((UPSTREAM_HOST, UPSTREAM_PORT))
        logger.info(
            "upstream connected; piping (in_ep=0x%02x, out_ep=0x%02x)",
            endpoint_in,
            endpoint_out,
        )

        try:
            _shuttle(context, handle, endpoint_in, endpoint_out, upstream)
        finally:
            _shutdown_quietly(upstream)
            upstream.close()
            _reset_device(handle)
            logger.info("accessory pipe closed")


def _ensure_accessory(context: usb1.USBContext) -> usb1.USBDeviceHandle | None:
    handle = _open_accessory(context)
    if handle is not None:
        return handle

    candidate = _find_handshake_candidate(context)
    if candidate is None:
        return None

    logger.info(
        "handshaking candidate vid=%04x pid=%04x",
        candidate.getVendorID(),
        candidate.getProductID(),
    )
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

    logger.info("post-handshake accessory not found within %ss", POST_HANDSHAKE_TIMEOUT_S)
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
            logger.info("could not inspect device: %s", exception)
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
        logger.info("GET_PROTOCOL failed: %s", exception)
        return False

    if len(protocol_bytes) != 2:
        logger.info("GET_PROTOCOL returned %d bytes", len(protocol_bytes))
        return False

    protocol = int.from_bytes(protocol_bytes, "little")
    if protocol < 1:
        logger.info("device does not support AOA (protocol=%s)", protocol)
        return False

    logger.info("device supports AOA protocol v%s", protocol)

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
        logger.info("AOA setup failed: %s", exception)
        return False

    return True


def _open_bulk_endpoints(handle: usb1.USBDeviceHandle) -> tuple[int, int] | None:
    # Detach any kernel driver auto-bound to interface 0 before claiming. No explicit
    # setConfiguration() — the kernel configures the device at enumeration, and an extra
    # SET_CONFIGURATION trips EIO on the accessory+ADB variants (pid 0x2d01 / 0x2d05).
    if handle.kernelDriverActive(0):
        handle.detachKernelDriver(0)

    try:
        handle.claimInterface(0)
    except usb1.USBError as exception:
        logger.info("claimInterface(0) failed: %s", exception)
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
        logger.info("could not find bulk IN/OUT endpoints on accessory interface")
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
        to_phone, from_phone, uptime = state.summary_args()
        logger.info(
            "pipe done: to_phone=%dB from_phone=%dB uptime=%ds",
            to_phone,
            from_phone,
            uptime,
        )


def _event_loop(context: usb1.USBContext, state: ShuttleState) -> None:
    while not state.stop.is_set():
        try:
            context.handleEventsTimeout(EVENT_LOOP_TICK_S)
        except usb1.USBError as exception:
            state.fail("event loop error: %s", exception)
            return


def _pump_upstream_to_usb(handle: usb1.USBDeviceHandle, endpoint_out: int, state: ShuttleState) -> None:
    # ZED → phone is mostly small HTTP response framing, so a synchronous bulkWrite per recv
    # is fine. Short socket timeout so the loop polls state.stop and exits when the IN side fails.
    state.upstream.settimeout(EVENT_LOOP_TICK_S)
    while not state.stop.is_set():
        try:
            data = state.upstream.recv(IN_BUFFER_SIZE)
        except TimeoutError:
            continue
        except OSError as exception:
            state.fail("upstream read error: %s", exception)
            return

        if not data:
            state.fail("upstream closed")
            return

        try:
            handle.bulkWrite(endpoint_out, data, timeout=OUT_TIMEOUT_MS)
        except usb1.USBError as exception:
            state.fail("USB write error: %s", exception)
            return

        state.bytes_to_phone += len(data)


def _drain_and_join(
    in_transfers: list[usb1.USBTransfer],
    event_thread: threading.Thread,
    state: ShuttleState,
) -> None:
    # Cancel in-flight IN transfers and wait for their TRANSFER_CANCELLED callbacks to drain
    # before stopping the event loop, else libusb warns about transfers still in flight at teardown.
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


def _reset_device(handle: usb1.USBDeviceHandle) -> None:
    # USB port reset invalidates the phone-side accessory FD; without this
    # OkHttp's pooled h2c session survives an upstream TCP tear-down and
    # desyncs with the next upstream connection, causing a protocol-error
    # feedback loop.
    try:
        handle.resetDevice()
    except usb1.USBError as exception:
        logger.info("device reset failed: %s", exception)
