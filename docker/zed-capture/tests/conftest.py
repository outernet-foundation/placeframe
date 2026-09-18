import os
import tempfile

# Set before `src.main` or `src.logging_config` can be imported by any test module.
os.environ.setdefault("CODEGEN", "1")
os.environ.setdefault("ZED_LOG_DIR", tempfile.mkdtemp(prefix="zed-capture-logs-"))
