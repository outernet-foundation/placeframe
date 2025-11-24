#!/usr/bin/env python3
import json
from os import environ

# Prevent pydantic settings from running validation
environ["CODEGEN"] = "1"

from .main import app

if __name__ == "__main__":
    print(json.dumps(app.openapi(), indent=2))
