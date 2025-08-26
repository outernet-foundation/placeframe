import random
import time

import boto3
from mypy_boto3_batch import BatchClient

from settings import get_settings

settings = get_settings()


def main():
    print(f"Starting reconstruction for capture id {settings.capture_id}")

    client: BatchClient = boto3.client("batch", region_name="us-east-1")  # type: ignore[call-arg]

    response = client.submit_job(
        jobName=f"reconstruction-{settings.capture_id}",
        jobQueue=settings.job_queue_arn,
        jobDefinition=settings.job_definition_arn,
        arrayProperties={"size": 2},
        containerOverrides={
            "environment": [
                {"name": "CAPTURE_ID", "value": settings.capture_id},
            ]
        },
    )

    job_id = response["jobId"]
    print(f"Submitted job {job_id}")

    while True:
        status = client.describe_jobs(jobs=[job_id])["jobs"][0]["status"]
        print(f"Job {job_id} status: {status}")
        if status in ["SUCCEEDED", "FAILED"]:
            break
        time.sleep(1 + random.random())


if __name__ == "__main__":
    main()
