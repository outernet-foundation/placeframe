from pathlib import Path
from threading import Thread
from uuid import UUID, uuid4


class InvalidStateException(Exception):
    pass


class Zed(Thread):
    def __init__(self, output_directory: Path):
        self._exception = None

    def start_capture(self, capture_interval: float) -> UUID:
        return uuid4()

    def stop_capture(self) -> None:
        pass
