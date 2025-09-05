from piccolo.columns import UUID, Timestamp, Varchar
from piccolo.columns.defaults.timestamp import TimestampNow

from ..piccolo_shims import Table


# require=true
# https://github.com/piccolo-orm/piccolo/issues/1132
class Node(Table):
    id = UUID(primary_key=True, required=True)

    filename = Varchar(length=255, unique=True, required=True)

    created_at = Timestamp(default=TimestampNow(), required=True)

    uploaded_at = Timestamp(null=True)
