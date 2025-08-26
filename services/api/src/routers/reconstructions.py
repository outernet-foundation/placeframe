import os
from uuid import UUID

import boto3
from fastapi import APIRouter, HTTPException, status
from mypy_boto3_batch import BatchClient

from db.tables.captures import Capture
from settings import get_settings

router = APIRouter(prefix="/reconstructions", tags=["reconstructions"])

settings = get_settings()


@router.post("")
async def create_reconstruction(capture_id: UUID):
    # Validate capture id exists
    if not await Capture.objects().get(Capture.id == capture_id):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Capture with id {capture_id} not found",
        )

    job_queue = settings.reconstruction_job_queue
    job_definition = settings.reconstruction_job_definition

    batch: BatchClient = boto3.client(  # type: ignore[call-arg]
        "batch", region_name=os.getenv("AWS_REGION", "us-east-1")
    )

    batch.submit_job(
        jobName=f"reconstruction-{capture_id}",
        jobQueue=job_queue,
        jobDefinition=job_definition,
        containerOverrides={
            "environment": [
                {"name": "CAPTURE_ID", "value": str(capture_id)},
            ]
        },
    )

    pass
