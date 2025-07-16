from piccolo.conf.apps import AppRegistry

from db.piccolo_shims import PostgresEngine
from settings import get_settings

DB = PostgresEngine(
    config={"dsn": str(get_settings().postgres_dsn)},
    extensions=(),
)

APP_REGISTRY = AppRegistry(apps=["db.app", "piccolo_admin.piccolo_app"])
