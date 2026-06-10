from __future__ import annotations

import tarfile
from collections.abc import Iterator
from typing import IO

from litestar.exceptions import HTTPException
from litestar.status_codes import HTTP_422_UNPROCESSABLE_ENTITY


# Streams a tar's regular-file members as (name, fileobj) pairs in stream mode, so it works for both
# seekable uploads and non-seekable storage bodies and never loads the whole tar into memory. The
# caller positions the fileobj at the start; each yielded fileobj is valid only until the next
# iteration, so read it before advancing. A malformed tar surfaces as a 422.
def iter_tar_file_members(fileobj: IO[bytes]) -> Iterator[tuple[str, IO[bytes]]]:
    try:
        with tarfile.open(fileobj=fileobj, mode="r|*") as tar:
            for member in tar:
                if not member.isfile():
                    continue

                extracted = tar.extractfile(member)
                if extracted is None:
                    continue

                yield member.name, extracted
    except tarfile.ReadError as error:
        raise HTTPException(status_code=HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Invalid tar file: {error}") from error
