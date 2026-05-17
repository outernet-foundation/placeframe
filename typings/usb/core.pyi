# Hand-written partial stubs for pyusb. Covers the surface used by
# docker/aoa-bridge/src/aoa_bridge/main.py. pyusb ships no upstream
# stubs and there is no types-pyusb / pyusb-stubs on pypi.

import array
from collections.abc import Iterator
from typing import Any, Literal, overload

class USBError(IOError):
    errno: int | None
    backend_error_code: int | None

class USBTimeoutError(USBError): ...

class Endpoint:
    bEndpointAddress: int
    wMaxPacketSize: int
    bmAttributes: int
    bInterval: int

class Interface:
    bInterfaceNumber: int
    bAlternateSetting: int
    bInterfaceClass: int

class Configuration:
    bConfigurationValue: int
    def __getitem__(self, key: tuple[int, int]) -> Interface: ...

class Device:
    idVendor: int
    idProduct: int
    bDeviceClass: int
    bcdDevice: int
    bus: int
    address: int

    @overload
    def ctrl_transfer(
        self,
        bmRequestType: int,
        bRequest: int,
        wValue: int = ...,
        wIndex: int = ...,
        *,
        data_or_wLength: int,
        timeout: int | None = ...,
    ) -> array.array[int]: ...
    @overload
    def ctrl_transfer(
        self,
        bmRequestType: int,
        bRequest: int,
        wValue: int = ...,
        wIndex: int = ...,
        *,
        data_or_wLength: bytes | bytearray | None = ...,
        timeout: int | None = ...,
    ) -> int: ...
    def read(self, endpoint: int, size_or_buffer: int, timeout: int | None = ...) -> array.array[int]: ...
    def write(self, endpoint: int, data: bytes | bytearray, timeout: int | None = ...) -> int: ...
    def set_configuration(self, configuration: int | None = ...) -> None: ...
    def get_active_configuration(self) -> Configuration: ...
    def is_kernel_driver_active(self, interface: int) -> bool: ...
    def detach_kernel_driver(self, interface: int) -> None: ...
    def attach_kernel_driver(self, interface: int) -> None: ...
    def reset(self) -> None: ...

@overload
def find(*, find_all: Literal[True], **kwargs: Any) -> Iterator[Device]: ...
@overload
def find(*, find_all: Literal[False] = ..., **kwargs: Any) -> Device | None: ...
@overload
def find(**kwargs: Any) -> Device | None: ...
