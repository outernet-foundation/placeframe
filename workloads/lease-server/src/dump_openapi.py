#!/usr/bin/env python3
import json

# The codegen config's global spec_command runs python -m src.dump_openapi in every
# project; the service itself lives in the lease_server package.
from lease_server.main import app

if __name__ == "__main__":
    print(json.dumps(app.openapi_schema.to_schema(), indent=2))
