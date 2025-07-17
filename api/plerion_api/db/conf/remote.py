# from db.util.stub_engine import StubEngine
from piccolo.conf.apps import AppRegistry

from plerion_api.db.util.stub_engine import StubEngine

# DB = PostgresEngine(
#     config={
#         "dsn": str(get_settings().postgres_dsn),
#         "timeout": 0.5,
#     },
#     extensions=(),
# )

DB = StubEngine()

APP_REGISTRY = AppRegistry(apps=["api.db.piccolo_app", "piccolo_admin.piccolo_app"])
