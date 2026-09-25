from __future__ import annotations

from typing import cast, overload

from numpy import bool_, dtype, generic, intp, ndarray
from numpy import compress as _compress
from numpy import nonzero as _nonzero
from numpy import zeros as _zeros


@overload
def zeros[A: int, T: generic](shape: tuple[A], dtype: type[T]) -> ndarray[tuple[A], dtype[T]]: ...
@overload
def zeros[A: int, B: int, T: generic](shape: tuple[A, B], dtype: type[T]) -> ndarray[tuple[A, B], dtype[T]]: ...
@overload
def zeros[A: int, B: int, C: int, T: generic](
    shape: tuple[A, B, C], dtype: type[T]
) -> ndarray[tuple[A, B, C], dtype[T]]: ...
def zeros(shape: tuple[int, ...], dtype: type[generic]) -> ndarray[tuple[int, ...], dtype[generic]]:
    return _zeros(shape, dtype=dtype)


def nonzero[A: int, B: int](
    array: ndarray[tuple[A], dtype[generic]],
) -> tuple[ndarray[tuple[B], dtype[intp]]]:
    return cast("tuple[ndarray[tuple[B], dtype[intp]]]", _nonzero(array))


def compress[A: int, B: int, T: generic](
    condition: ndarray[tuple[A], dtype[bool_]],
    array: ndarray[tuple[A], dtype[T]],
) -> ndarray[tuple[B], dtype[T]]:
    return cast("ndarray[tuple[B], dtype[T]]", _compress(condition, array))
