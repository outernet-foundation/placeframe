from __future__ import annotations

from typing import TYPE_CHECKING

import torch

if TYPE_CHECKING:

    class TT[*Shape](torch.Tensor): ...

else:
    # PEP 695 generic-class syntax is type-checker only. At runtime, TT[Shape...]
    # must evaluate (e.g. inside cast() and module-level tuple[...] aliases),
    # so collapse subscription to plain torch.Tensor.
    class TT:
        def __class_getitem__(cls, _params: object) -> type[torch.Tensor]:
            return torch.Tensor
