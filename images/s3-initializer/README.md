# s3-initializer

One-shot bring-up container that converges the stack's required S3 buckets on the SeaweedFS endpoint: each declared bucket is verified if it already exists and created if missing, retrying until the S3 endpoint accepts connections. Exits 0 only when every bucket is verified owned.
