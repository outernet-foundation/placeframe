from typing import Callable, cast

import torch
from cv2.typing import MatLike

tensor_from_numpy: Callable[[MatLike], torch.Tensor] = cast(Callable[[MatLike], torch.Tensor], torch.from_numpy)
