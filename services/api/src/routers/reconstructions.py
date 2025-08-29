from uuid import UUID

from common.batch_client import create_batch_client
from fastapi import APIRouter, HTTPException, status

from ..db.tables.captures import Capture
from ..settings import get_api_settings

router = APIRouter(prefix="/reconstructions", tags=["reconstructions"])

settings = get_api_settings()


#
@router.post("")
async def create_reconstruction(capture_id: UUID):
    # Validate capture id exists
    if not await Capture.objects().get(Capture.id == capture_id):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Capture with id {capture_id} not found",
        )

    print("Creating AWS Batch client...")
    client = create_batch_client(settings.backend)

    print("Submitting reconstruction job to AWS Batch...")
    client.submit_job_array(
        f"reconstruction-{capture_id}",
        settings.job_queue_arn,
        settings.reconstruction_job_definition_arn_prefix,
        1,
        {
            "BACKEND": settings.backend,
            "CAPTURE_ID": str(capture_id),
            "JOB_QUEUE_ARN": settings.job_queue_arn,
            "FEATURES_JOB_DEFINITION_ARN_PREFIX": settings.features_job_definition_arn_prefix,
        },
    )
    print("Reconstruction job submitted.")

    pass
