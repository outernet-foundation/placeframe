from piccolo.conf.apps import AppRegistry

from src.db.piccolo_shims import PostgresEngine
from src.settings import get_database_settings

settings = get_database_settings()

DB = PostgresEngine(
    config={
        "dsn": f"postgresql://{settings.postgres_user}:{settings.postgres_password}@{settings.postgres_host}:5432/postgres"
    },
    extensions=("uuid-ossp",),
)

APP_REGISTRY = AppRegistry(apps=["src.db.app"])
