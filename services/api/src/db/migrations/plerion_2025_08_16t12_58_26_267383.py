from piccolo.apps.migrations.auto.migration_manager import MigrationManager


ID = "2025-08-16T12:58:26:267383"
VERSION = "1.27.1"
DESCRIPTION = ""


async def forwards():
    manager = MigrationManager(
        migration_id=ID, app_name="plerion", description=DESCRIPTION
    )

    manager.drop_column(
        table_class_name="Capture",
        tablename="capture",
        column_name="deleted_at",
        db_column_name="deleted_at",
        schema=None,
    )

    return manager
