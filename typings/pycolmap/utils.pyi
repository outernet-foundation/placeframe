from __future__ import annotations
from builtins import module as ModuleType
from collections.abc import MutableSequence
from typing import Any
__all__: list[str] = ['Any', 'ModuleType', 'MutableSequence', 'import_module_symbols']
def import_module_symbols(dst_vars: dict[str, typing.Any], src_module: module, exclude: typing.Optional[set[str]] = None) -> collections.abc.MutableSequence[str]:
    ...
