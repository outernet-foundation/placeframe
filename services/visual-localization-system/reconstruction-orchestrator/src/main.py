from __future__ import annotations

import time

from common.batch_client import create_batch_client
from common.boto_clients import create_s3_client
from common.reconstruction_manifest import ReconstructionManifest
from models.public_tables import Reconstruction
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from .settings import get_settings

settings = get_settings()

engine = create_engine(
    f"postgresql+psycopg://{settings.database_user}:{settings.database_user_password}@{settings.postgres_host}:5432/{settings.database_name}",
    pool_pre_ping=True,
    future=True,
)

batch_client = create_batch_client(settings.backend)

s3_client = create_s3_client(
    s3_endpoint_url=settings.s3_endpoint_url, s3_access_key=settings.s3_access_key, s3_secret_key=settings.s3_secret_key
)


def main() -> None:
    while True:
        reconcile()
        start_next_reconstruction()
        time.sleep(3)


def start_next_reconstruction() -> None:
    with Session(engine) as session, session.begin():
        queued_reconstruction = session.execute(
            select(Reconstruction.id)
            .where(Reconstruction.orchestration_status == "queued")
            .order_by(Reconstruction.created_at)
            .with_for_update(skip_locked=True)
            .limit(1)
        ).fetchone()

        if queued_reconstruction is None:
            return

        queued_reconstruction = session.get(Reconstruction, queued_reconstruction.id)
        assert queued_reconstruction is not None

        print(
            f"Starting reconstruction {queued_reconstruction.id} for capture {queued_reconstruction.capture_session_id}"
        )

        batch_client.submit_job(
            name=str(queued_reconstruction.id),
            queue_name=settings.batch_job_queue,
            job_definition_name=settings.batch_job_definition,
            environment={
                "S3_ENDPOINT_URL": str(settings.s3_endpoint_url),
                "S3_ACCESS_KEY": str(settings.s3_access_key),
                "S3_SECRET_KEY": str(settings.s3_secret_key),
                "CAPTURES_BUCKET": settings.captures_bucket,
                "RECONSTRUCTIONS_BUCKET": settings.reconstructions_bucket,
                "CAPTURE_ID": str(queued_reconstruction.capture_session_id),
                "RECONSTRUCTION_ID": str(queued_reconstruction.id),
            },
        )

        # https://github.com/agronholm/sqlacodegen/issues/408
        # TODO: sqlacodegen currently generates strings for enums, which sucks
        queued_reconstruction.orchestration_status = "pending"
        session.add(queued_reconstruction)


def reconcile(max_rows: int = 50) -> None:
    print("Reconciling running reconstructions")

    with Session(engine) as session:
        running = (
            session.execute(
                select(Reconstruction.id)
                .where(Reconstruction.orchestration_status.in_(["pending", "running"]))
                .order_by(Reconstruction.created_at)
                .limit(max_rows)
            )
            .scalars()
            .all()
        )

    for reconstruction_id in running:
        print(f"Checking reconstruction {reconstruction_id}")

        try:
            manifest = ReconstructionManifest.model_validate_json(
                s3_client.get_object(Bucket=settings.reconstructions_bucket, Key=f"{reconstruction_id}/manifest.json")[
                    "Body"
                ].read()
            )
        except Exception as e:
            print(f"No manifest.json found for reconstruction {reconstruction_id}, skipping: {e}")
            continue

        print(f"Reconstruction {reconstruction_id} status: {manifest.status}")

        with Session(engine) as session, session.begin():
            row = session.get(Reconstruction, reconstruction_id, with_for_update=False)
            assert row is not None

            if manifest.status == "succeeded":
                row.orchestration_status = "succeeded"
            elif manifest.status == "failed":
                row.orchestration_status = "failed"
            elif manifest.status != "pending":
                row.orchestration_status = "running"

            session.add(row)
            session.flush()


if __name__ == "__main__":
    main()
