# interfaces/batch.py
from __future__ import annotations

from typing import Dict, Protocol


class BatchClient(Protocol):
    def submit_job_array(
        self,
        name: str,
        queue_name: str,
        job_definition_name: str,
        *,
        environment_variables: Dict[str, str] | None = None,
        array_size: int | None = None,
    ) -> str: ...

    def get_job_status(self, job_id: str) -> str: ...
