#!/usr/bin/env python3
import json

from .main import app

if __name__ == "__main__":
    print(json.dumps(app.openapi(), indent=2))
