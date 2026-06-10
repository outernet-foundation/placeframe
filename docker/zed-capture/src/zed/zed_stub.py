from dataclasses import dataclass
from pathlib import Path
from threading import Thread
from uuid import UUID, uuid4


class InvalidStateException(Exception):
    pass


@dataclass(frozen=True)
class State:
    capture_id: UUID | None
    tracking_state: str
    stabilizing: bool
    last_exception: str | None


class Zed(Thread):
    def __init__(self, output_directory: Path):
        self._exception = None

    def start_capture(self, interval: float) -> UUID:
        return uuid4()

    def stop_capture(self) -> None:
        pass

    def state(self) -> State:
        return State(capture_id=None, tracking_state="OFF", stabilizing=False, last_exception=None)
