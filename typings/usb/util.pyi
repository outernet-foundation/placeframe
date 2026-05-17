from collections.abc import Callable

from usb.core import Configuration, Device, Endpoint, Interface

ENDPOINT_IN: int
ENDPOINT_OUT: int

def endpoint_direction(address: int) -> int: ...
def find_descriptor(
    container: Configuration | Interface,
    custom_match: Callable[[Endpoint], bool] | None = ...,
) -> Endpoint | None: ...
def dispose_resources(device: Device) -> None: ...
