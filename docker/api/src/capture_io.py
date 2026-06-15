from __future__ import annotations

import tarfile
from collections.abc import Iterable, Iterator
from uuid import UUID

from datamodels.public_dtos import CaptureSessionCreate, CaptureSessionRead, capture_session_from_dto
from datamodels.public_tables import CaptureSession

from .storage import Storage

CAPTURES_BUCKET = "dev-captures"

# A capture session's stored tar, nested verbatim as one member inside an export archive (a capture
# export or a reconstruction bundle). Kept distinct from the metadata member so a reader can stream
# it straight back to storage without unpacking.
CAPTURE_MEMBER = "capture.tar"

TAR_BLOCK = 512
ARTIFACT_CHUNK = 1024 * 1024


# Frames one tar member by hand (not tarfile.addfile, which buffers a whole member) so a large
# artifact never lands in memory. The caller concatenates members and appends the two-block end
# marker (b"\x00" * TAR_BLOCK * 2) to close the archive.
def tar_member(name: str, size: int, chunks: Iterable[bytes]) -> Iterator[bytes]:
    info = tarfile.TarInfo(name)
    info.size = size
    info.mtime = 0

    yield info.tobuf(format=tarfile.GNU_FORMAT)
    yield from chunks

    remainder = size % TAR_BLOCK
    if remainder:
        yield b"\x00" * (TAR_BLOCK - remainder)


# Streams a capture session's stored tar as a single named member, so an export can nest a capture
# verbatim inside a larger archive without unpacking or buffering it.
def iter_capture_member(storage: Storage, capture_id: UUID, member_name: str = CAPTURE_MEMBER) -> Iterator[bytes]:
    key = f"{capture_id}.tar"
    size = storage.head_object_size(CAPTURES_BUCKET, key)
    body = storage.get_object(CAPTURES_BUCKET, key)["Body"]
    yield from tar_member(member_name, size, body.iter_chunks(ARTIFACT_CHUNK))


# Builds an unsaved CaptureSession row from a read DTO, preserving the source backend's id, name,
# device type, recording time and size so an imported capture keeps its original identity and the
# reconstruction foreign key that points at it.
def capture_row_from_read(capture: CaptureSessionRead) -> CaptureSession:
    return capture_session_from_dto(
        CaptureSessionCreate(
            id=capture.id,
            name=capture.name,
            device_type=capture.device_type,
            recorded_at=capture.recorded_at,
            size_bytes=capture.size_bytes,
        )
    )
