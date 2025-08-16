from piccolo.apps.migrations.auto.migration_manager import MigrationManager


ID = "2025-08-16T15:33:08:013425"
VERSION = "1.27.1"
DESCRIPTION = ""


async def forwards():
    manager = MigrationManager(
        migration_id=ID, app_name="plerion", description=DESCRIPTION
    )

    manager.drop_column(
        table_class_name="Capture",
        tablename="capture",
        column_name="deleteasdfd_at",
        db_column_name="deleteasdfd_at",
        schema=None,
    )

    return manager
