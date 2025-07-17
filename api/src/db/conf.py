from piccolo.conf.apps import AppRegistry

from ..settings import get_settings
from .piccolo_shims import PostgresEngine

DB = PostgresEngine(
    config={
        "dsn": str(get_settings().postgres_dsn),
    },
    extensions=("uuid-ossp",),
)

APP_REGISTRY = AppRegistry(apps=["src.db.app", "piccolo_admin.piccolo_app"])
