import os
from uuid import UUID

import boto3
from fastapi import APIRouter, HTTPException, status
from mypy_boto3_batch import BatchClient

from ..db.tables.captures import Capture
from ..settings import get_api_settings

router = APIRouter(prefix="/reconstructions", tags=["reconstructions"])

settings = get_api_settings()


@router.post("")
async def create_reconstruction(capture_id: UUID):
    # Validate capture id exists
    if not await Capture.objects().get(Capture.id == capture_id):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Capture with id {capture_id} not found",
        )

    print("Creating AWS Batch client...")
    batch: BatchClient = boto3.client(  # type: ignore[call-arg]
        "batch", region_name=os.getenv("AWS_REGION", "us-east-1")
    )

    print("Submitting reconstruction job to AWS Batch...")
    batch.submit_job(
        jobName=f"reconstruction-{capture_id}",
        jobQueue=settings.job_queue_arn,
        jobDefinition=settings.reconstruction_job_definition_arn,
        containerOverrides={
            "environment": [
                {"name": "CAPTURE_ID", "value": str(capture_id)},
                {"name": "JOB_QUEUE_ARN", "value": settings.job_queue_arn},
                {
                    "name": "FEATURES_JOB_DEFINITION_ARN",
                    "value": settings.features_job_definition_arn,
                },
            ]
        },
    )
    print("Reconstruction job submitted.")

    pass
