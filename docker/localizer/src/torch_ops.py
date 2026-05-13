from __future__ import annotations

from collections.abc import Sequence
from typing import Literal, overload

from numpy import dtype, generic, ndarray
from torch import Tensor
from torch import from_numpy as _from_numpy  # pyright: ignore[reportUnknownVariableType]
from torch import stack as _stack

from core.tensor_types import TT


@overload
def from_numpy[A: int, T: generic](array: ndarray[tuple[A], dtype[T]]) -> TT[A]: ...
@overload
def from_numpy[A: int, B: int, T: generic](array: ndarray[tuple[A, B], dtype[T]]) -> TT[A, B]: ...
@overload
def from_numpy[A: int, B: int, C: int, T: generic](array: ndarray[tuple[A, B, C], dtype[T]]) -> TT[A, B, C]: ...
def from_numpy(array: ndarray[tuple[int, ...], dtype[generic]]) -> Tensor:
    return _from_numpy(array)


@overload
def to[A: int](tensor: TT[A], device: str) -> TT[A]: ...
@overload
def to[A: int, B: int](tensor: TT[A, B], device: str) -> TT[A, B]: ...
@overload
def to[A: int, B: int, C: int](tensor: TT[A, B, C], device: str) -> TT[A, B, C]: ...
def to(tensor: Tensor, device: str) -> Tensor:
    return tensor.to(device)


@overload
def stack[N: int, D: int](tensors: Sequence[TT[D]], dim: Literal[0]) -> TT[N, D]: ...
@overload
def stack[N: int, A: int, B: int](tensors: Sequence[TT[A, B]], dim: Literal[0]) -> TT[N, A, B]: ...
def stack(tensors: Sequence[Tensor], dim: int) -> Tensor:
    return _stack(list(tensors), dim=dim)


@overload
def permute[A: int, B: int, C: int](
    tensor: TT[A, B, C], dims: tuple[Literal[0], Literal[1], Literal[2]]
) -> TT[A, B, C]: ...
@overload
def permute[A: int, B: int, C: int](
    tensor: TT[A, B, C], dims: tuple[Literal[0], Literal[2], Literal[1]]
) -> TT[A, C, B]: ...
@overload
def permute[A: int, B: int, C: int](
    tensor: TT[A, B, C], dims: tuple[Literal[1], Literal[0], Literal[2]]
) -> TT[B, A, C]: ...
@overload
def permute[A: int, B: int, C: int](
    tensor: TT[A, B, C], dims: tuple[Literal[1], Literal[2], Literal[0]]
) -> TT[B, C, A]: ...
@overload
def permute[A: int, B: int, C: int](
    tensor: TT[A, B, C], dims: tuple[Literal[2], Literal[0], Literal[1]]
) -> TT[C, A, B]: ...
@overload
def permute[A: int, B: int, C: int](
    tensor: TT[A, B, C], dims: tuple[Literal[2], Literal[1], Literal[0]]
) -> TT[C, B, A]: ...
def permute(tensor: Tensor, dims: tuple[int, ...]) -> Tensor:
    return tensor.permute(*dims)


@overload
def transpose[A: int, B: int](tensor: TT[A, B], dim0: Literal[0], dim1: Literal[1]) -> TT[B, A]: ...
@overload
def transpose[A: int, B: int](tensor: TT[A, B], dim0: Literal[1], dim1: Literal[0]) -> TT[B, A]: ...
@overload
def transpose[A: int, B: int, C: int](tensor: TT[A, B, C], dim0: Literal[0], dim1: Literal[1]) -> TT[B, A, C]: ...
@overload
def transpose[A: int, B: int, C: int](tensor: TT[A, B, C], dim0: Literal[1], dim1: Literal[0]) -> TT[B, A, C]: ...
@overload
def transpose[A: int, B: int, C: int](tensor: TT[A, B, C], dim0: Literal[0], dim1: Literal[2]) -> TT[C, B, A]: ...
@overload
def transpose[A: int, B: int, C: int](tensor: TT[A, B, C], dim0: Literal[2], dim1: Literal[0]) -> TT[C, B, A]: ...
@overload
def transpose[A: int, B: int, C: int](tensor: TT[A, B, C], dim0: Literal[1], dim1: Literal[2]) -> TT[A, C, B]: ...
@overload
def transpose[A: int, B: int, C: int](tensor: TT[A, B, C], dim0: Literal[2], dim1: Literal[1]) -> TT[A, C, B]: ...
def transpose(tensor: Tensor, dim0: int, dim1: int) -> Tensor:
    return tensor.transpose(dim0, dim1)


@overload
def matmul[A: int, B: int, C: int](a: TT[A, B], b: TT[B, C]) -> TT[A, C]: ...
@overload
def matmul[I: int, A: int, B: int, C: int](a: TT[A, B], b: TT[I, B, C]) -> TT[I, A, C]: ...
def matmul(a: Tensor, b: Tensor) -> Tensor:
    return a @ b


@overload
def amax[A: int, B: int, C: int](tensor: TT[A, B, C], dim: Literal[0]) -> TT[B, C]: ...
@overload
def amax[A: int, B: int, C: int](tensor: TT[A, B, C], dim: Literal[1]) -> TT[A, C]: ...
@overload
def amax[A: int, B: int, C: int](tensor: TT[A, B, C], dim: Literal[2]) -> TT[A, B]: ...
@overload
def amax[A: int, B: int, C: int](tensor: TT[A, B, C], dim: tuple[Literal[0], Literal[1]]) -> TT[C]: ...
@overload
def amax[A: int, B: int, C: int](tensor: TT[A, B, C], dim: tuple[Literal[0], Literal[2]]) -> TT[B]: ...
@overload
def amax[A: int, B: int, C: int](tensor: TT[A, B, C], dim: tuple[Literal[1], Literal[2]]) -> TT[A]: ...
def amax(tensor: Tensor, dim: int | tuple[int, ...]) -> Tensor:
    return tensor.amax(dim=dim)
