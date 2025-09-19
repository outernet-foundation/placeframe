from __future__ import annotations

import json
import time

from common.batch_client import create_batch_client
from common.boto_clients import create_s3_client
from models.public_tables import Reconstruction
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from settings import get_settings

settings = get_settings()

captures_bucket = settings.s3_captures_bucket_name
reconstructions_bucket = settings.s3_reconstructions_bucket_name

engine = create_engine(settings.database_url, pool_pre_ping=True, future=True)
batch_client = create_batch_client(settings.backend)
s3_client = create_s3_client()


def start_next_reconstruction() -> None:
    with Session(engine) as session, session.begin():
        queued_reconstruction = session.execute(
            select(Reconstruction.id)
            .where(Reconstruction.status == "queued")
            .order_by(Reconstruction.created_at)
            .with_for_update(skip_locked=True)
            .limit(1)
        ).fetchone()

        if queued_reconstruction is None:
            return

        queued_reconstruction = session.get(Reconstruction, queued_reconstruction.id)
        assert queued_reconstruction is not None

        job_id = batch_client.submit_job(
            name=str(queued_reconstruction.id),
            queue_name=settings.batch_job_queue,
            job_definition_name=settings.batch_job_definition,
            environment={
                "CAPTURE_ID": str(queued_reconstruction.capture_id),
                "RECONSTRUCTION_ID": str(queued_reconstruction.id),
            },
        )

        s3_client.put_object(
            Bucket=reconstructions_bucket,
            Key=f"{queued_reconstruction.id}/run.json",
            Body=json.dumps({"job_id": job_id}).encode("utf-8"),
            ContentType="application/json",
        )


def main() -> None:
    while True:
        time.sleep(15)


if __name__ == "__main__":
    main()
