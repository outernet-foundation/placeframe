import os

# database.py resolves settings at import time; these placeholder values let the
# test modules import without a live stack. The api tests set the same names via
# monkeypatch, which overrides these within their own tests.
_TEST_ENV = {
    "POSTGRES_HOST": "pf-postgres",
    "DATABASE_NAME": "placeframe",
    "DATABASE_ORCHESTRATION_USER": "placeframe_orchestration_user",
    "DATABASE_ORCHESTRATION_USER_PASSWORD": "password",
}

for _name, _value in _TEST_ENV.items():
    os.environ.setdefault(_name, _value)
