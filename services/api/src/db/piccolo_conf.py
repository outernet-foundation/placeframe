from piccolo.conf.apps import AppRegistry

from src.db.piccolo_shims import PostgresEngine
from src.settings import get_settings

DB = PostgresEngine(
    config={
        "dsn": str(get_settings().postgres_dsn),
    },
    extensions=("uuid-ossp",),
)

APP_REGISTRY = AppRegistry(apps=["src.db.app"])
