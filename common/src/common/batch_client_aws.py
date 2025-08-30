from typing import TYPE_CHECKING, Any, Dict

import boto3

if TYPE_CHECKING:
    from mypy_boto3_batch import BatchClient as AwsBatchClient
    from mypy_boto3_batch.type_defs import SubmitJobRequestTypeDef
else:
    BatchClient = Any


class BatchClient:
    def __init__(self):
        self.client: AwsBatchClient = boto3.client("batch", region_name="us-east-1")  # type: ignore[call-arg]

    def submit_job_array(
        self,
        name: str,
        queue_name: str,
        job_definition_name: str,
        *,
        environment_variables: Dict[str, str] | None = None,
        array_size: int | None = None,
    ):
        job: SubmitJobRequestTypeDef = {
            "jobName": name,
            "jobQueue": queue_name,
            "jobDefinition": job_definition_name,
        }

        if environment_variables is not None:
            job["containerOverrides"] = {
                "environment": [
                    {"name": key, "value": value}
                    for key, value in environment_variables.items()
                ]
            }

        if array_size is not None:
            job["arrayProperties"] = {"size": array_size}

        return self.client.submit_job(**job)["jobId"]

    def get_job_status(self, job_id: str):
        return self.client.describe_jobs(jobs=[job_id])["jobs"][0]["status"]
