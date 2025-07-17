from piccolo.conf.apps import AppRegistry

from src.db.util.stub_engine import StubEngine

# DB = PostgresEngine(
#     config={
#         "dsn": str(get_settings().postgres_dsn),
#         "timeout": 0.5,
#     },
#     extensions=(),
# )

DB = StubEngine()

APP_REGISTRY = AppRegistry(apps=["src.db.piccolo_app", "piccolo_admin.piccolo_app"])
