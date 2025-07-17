# from db.util.stub_engine import StubEngine
from piccolo.conf.apps import AppRegistry

from ...settings import get_settings
from ..util.shims import PostgresEngine

DB = PostgresEngine(
    config={
        "dsn": str(get_settings().postgres_dsn),
        "timeout": 0.5,
    },
    extensions=(),
)

APP_REGISTRY = AppRegistry(
    apps=["plerion_api.db.piccolo_app", "piccolo_admin.piccolo_app"]
)
