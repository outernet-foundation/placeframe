from bashrun.bash import bash

bash("uv run --locked preflight-python")
bash("uv run --locked preflight")
bash("uv run --locked generate-clients --config openapi-client-codegen.yaml --check")
