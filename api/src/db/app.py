import importlib
import os
import pkgutil

from piccolo.conf.apps import AppConfig, table_finder

tables = importlib.import_module("db.tables")

APP_CONFIG = AppConfig(
    app_name="db",
    migrations_folder_path=os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "migrations"
    ),
    table_classes=table_finder(
        modules=[
            f"{tables.__name__}.{name}"
            for _, name, _ in pkgutil.iter_modules(tables.__path__)
        ]
    ),
    migration_dependencies=[],
    commands=[],
)