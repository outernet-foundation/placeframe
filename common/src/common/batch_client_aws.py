from typing import TYPE_CHECKING, Dict

from common.boto_clients import create_batch_client

if TYPE_CHECKING:
    from mypy_boto3_batch.type_defs import SubmitJobRequestTypeDef


class AwsBatchClient:
    def __init__(self):
        self.client = create_batch_client()

    def submit_job(
        self,
        name: str,
        queue_name: str,
        job_definition_name: str,
        *,
        array_size: int | None = None,
        environment: Dict[str, str] | None = None,
    ) -> str:
        job: SubmitJobRequestTypeDef = {"jobName": name, "jobQueue": queue_name, "jobDefinition": job_definition_name}

        if environment is not None:
            job["containerOverrides"] = {
                "environment": [{"name": key, "value": value} for key, value in environment.items()]
            }

        if array_size is not None:
            job["arrayProperties"] = {"size": array_size}

        return self.client.submit_job(**job)["jobId"]

    def get_job_status(self, job_id: str):
        return self.client.describe_jobs(jobs=[job_id])["jobs"][0]["status"]
