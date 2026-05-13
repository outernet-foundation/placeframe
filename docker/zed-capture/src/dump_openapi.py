#!/usr/bin/env python3
import json
import os

os.environ["CODEGEN"] = "1"

from .main import app

if __name__ == "__main__":
    print(json.dumps(app.openapi_schema.to_schema(), indent=2))
