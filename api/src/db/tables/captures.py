import uuid

from api.src.db.piccolo_shims import Table
from piccolo.columns import UUID, Timestamp, Varchar
from piccolo.columns.defaults.timestamp import TimestampNow


class Capture(Table):
    id = UUID(
        primary_key=True,
        default=uuid.uuid4,
    )

    filename = Varchar(
        length=255,
        unique=True,
    )

    created_at = Timestamp(
        default=TimestampNow(),
    )

    uploaded_at = Timestamp(
        null=True,
    )
