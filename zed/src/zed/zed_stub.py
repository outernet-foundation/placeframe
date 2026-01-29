from pathlib import Path
from threading import Thread


class InvalidStateException(Exception):
    pass


class Zed(Thread):
    def __init__(self, output_directory: Path):
        self._exception = None

    def start_capture(self, capture_interval: float):
        pass

    def stop_capture(self):
        pass
