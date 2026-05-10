# Reconstructor holds capture tar entirely in RAM

**Severity**: medium — fine for current capture sizes, will OOM as captures scale.

**Location**: `docker/reconstructor/`'s download path for `dev-captures/<capture_session_id>.tar`.

**Symptom**: A capture tar that fits today (a few hundred MB) does not stress the worker. As captures grow (longer sessions, higher-resolution sensors), the worker OOMs at download time before the pipeline begins. The crash looks like a generic OOM kill; nothing in the failure surface points at "the tar is the cause."

**Mechanism**: The download reads the entire tar into a `bytes` buffer, then untars to disk. Peak memory = full tar size. The worker also holds GPU model weights and pipeline intermediates resident, so headroom is small relative to phone-side capture sizes.

**Fix sketch**: Stream the MinIO object to disk via `boto3` `download_fileobj` with a chunked iterator into a `tempfile.NamedTemporaryFile`, then `tarfile.open(path)`. Pipeline code already operates on the unpacked directory, so only the download step changes. RAM for the download path drops to a few MB.

**Verification**: Run a synthetic capture of e.g. 4 GB and assert RSS during download stays bounded (~100 MB or less excluding model weights).
