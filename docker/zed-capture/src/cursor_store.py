from json import dumps, loads
from os import environ
from pathlib import Path
from tempfile import mkdtemp
from threading import Lock

# Cursor state lives on a separate volume from logs so a "clear logs" operation
# (or rotation past backupCount) doesn't accidentally reset delivery progress.
_requested_state_dir = Path(environ.get("ZED_STATE_DIR", "/var/lib/zed-capture"))


def _resolve_state_dir(requested: Path) -> Path:
    # Match logging_config's tmp-dir fallback so the OpenAPI dump works on dev
    # machines without /var write access.
    try:
        requested.mkdir(parents=True, exist_ok=True)
        return requested
    except PermissionError:
        return Path(mkdtemp(prefix="zed-capture-state-"))


STATE_DIR = _resolve_state_dir(_requested_state_dir)
CURSOR_FILE = STATE_DIR / "cursor.json"


class CursorStore:
    def __init__(self) -> None:
        self._lock = Lock()
        self._committed = self._load()
        # Pending == last cursor handed to a client but not yet acked. Reset to
        # committed on box restart, which means the next ack from a client may
        # be ignored as stale — at-least-once delivery, accepted by design.
        self._pending = self._committed

    def _load(self) -> str:
        if not CURSOR_FILE.exists():
            return ""
        try:
            return loads(CURSOR_FILE.read_text()).get("cursor", "")
        except (ValueError, OSError):
            return ""

    def _persist(self, cursor: str) -> None:
        # Atomic replace so a partial write can't corrupt the state.
        tmp = CURSOR_FILE.with_suffix(".tmp")
        tmp.write_text(dumps({"cursor": cursor}))
        tmp.replace(CURSOR_FILE)

    @property
    def committed(self) -> str:
        with self._lock:
            return self._committed

    def ack_and_get_committed(self, ack: str) -> str:
        # Commit the ack iff it matches what we last handed out and isn't
        # already committed. A non-matching ack is silently ignored — caller
        # may be retrying after a forward failure, in which case re-reading
        # from committed is exactly what we want.
        with self._lock:
            if ack and ack == self._pending and ack != self._committed:
                self._persist(ack)
                self._committed = ack
            return self._committed

    def set_pending(self, cursor: str) -> None:
        with self._lock:
            self._pending = cursor


cursor_store = CursorStore()
