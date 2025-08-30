import random
import time
from pathlib import Path

from common.batch_client import create_batch_client

from settings import get_settings

settings = get_settings()


def main():
    print("Submitting job")
    client = create_batch_client(
        settings.backend, Path("../docker-compose.yml").resolve()
    )
    job_id = client.submit_job(
        f"reconstruction-features-{settings.capture_id}",
        settings.job_queue_arn,
        settings.features_job_definition_arn_prefix,
        array_size=2,
        environment_variables={
            "BACKEND": settings.backend,
            "CAPTURE_ID": settings.capture_id,
        },
    )

    print("Awaiting job completion")
    while True:
        status = client.get_job_status(job_id)
        print(f"Job {job_id} status: {status}")
        if status in ["SUCCEEDED", "FAILED"]:
            break
        time.sleep(1 + random.random())

    print(f"Job completed with status {status}")


if __name__ == "__main__":
    main()
