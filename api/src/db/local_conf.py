from piccolo.conf.apps import AppRegistry

from .piccolo_stub_engine import StubEngine

DB = StubEngine()

APP_REGISTRY = AppRegistry(apps=["src.db.app"])
