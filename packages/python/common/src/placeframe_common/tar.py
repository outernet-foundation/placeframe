from __future__ import annotations

import tarfile
from collections.abc import Iterator
from io import RawIOBase
from typing import IO

from litestar.exceptions import HTTPException
from litestar.status_codes import HTTP_422_UNPROCESSABLE_ENTITY


# A stream-mode tar member's backing object is tarfile's internal _Stream, which lacks seekable().
# Consumers that probe the file interface (boto3's upload_fileobj calls seekable() to choose an upload
# manager) hit an AttributeError on it. Wrapping the member in a RawIOBase gives a real non-seekable
# binary stream: IOBase.seekable() already returns False, so a bare read() over the source is enough.
class _NonSeekableTarMember(RawIOBase):
    def __init__(self, source: IO[bytes]) -> None:
        self._source = source

    def readable(self) -> bool:
        return True

    def read(self, size: int | None = -1) -> bytes:
        return self._source.read(-1 if size is None else size)


# Streams a tar's regular-file members as (name, fileobj) pairs in stream mode, so it works for both
# seekable uploads and non-seekable storage bodies and never loads the whole tar into memory. The
# caller positions the fileobj at the start; each yielded fileobj is valid only until the next
# iteration, so read it before advancing. A malformed tar surfaces as a 422.
def iter_tar_file_members(fileobj: IO[bytes]) -> Iterator[tuple[str, RawIOBase]]:
    try:
        with tarfile.open(fileobj=fileobj, mode="r|*") as tar:
            for member in tar:
                if not member.isfile():
                    continue

                extracted = tar.extractfile(member)
                if extracted is None:
                    continue

                yield member.name, _NonSeekableTarMember(extracted)
    except tarfile.ReadError as error:
        raise HTTPException(status_code=HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Invalid tar file: {error}") from error
