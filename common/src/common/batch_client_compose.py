from typing import Dict


class BatchClient:
    def __init__(self): ...

    def submit_job_array(
        self,
        name: str,
        queue_name: str,
        job_definition_name: str,
        array_size: int,
        environment_variables: Dict[str, str],
    ):
        return 0

    def get_job_status(self, job_id: str):
        return "SUCCEEDED"
