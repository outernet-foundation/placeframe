from __future__ import annotations

from enum import Enum
from pydantic import AwareDatetime, BaseModel, Field
from typing import Optional
from uuid import UUID

from sqlalchemy import inspect as sa_inspect

from .public_tables import Capture, Reconstruction, Tenant



class Model(BaseModel):
    pass


class TenantCreate(BaseModel):
    id: Optional[UUID] = Field(None, title='Id')


class TenantUpdate(BaseModel):
    pass


class TenantBatchUpdate(BaseModel):
    id: UUID = Field(..., title='Id')


class TenantRead(BaseModel):
    id: UUID = Field(..., title='Id')
    created_at: AwareDatetime = Field(..., title='Created At')


class DeviceType(Enum):
    ARFoundation = 'ARFoundation'
    Zed = 'Zed'


class ReconstructionStatus(Enum):
    queued = 'queued'
    running = 'running'
    succeeded = 'succeeded'
    cancelled = 'cancelled'
    failed = 'failed'


class CaptureCreate(BaseModel):
    id: Optional[UUID] = Field(None, title='Id')
    device_type: DeviceType
    filename: str = Field(..., title='Filename')


class CaptureUpdate(BaseModel):
    device_type: Optional[DeviceType] = None
    filename: Optional[str] = Field(None, title='Filename')


class CaptureBatchUpdate(BaseModel):
    id: UUID = Field(..., title='Id')
    device_type: Optional[DeviceType] = None
    filename: Optional[str] = Field(None, title='Filename')


class CaptureRead(BaseModel):
    tenant_id: UUID = Field(..., title='Tenant Id')
    id: UUID = Field(..., title='Id')
    created_at: AwareDatetime = Field(..., title='Created At')
    updated_at: AwareDatetime = Field(..., title='Updated At')
    device_type: DeviceType
    filename: str = Field(..., title='Filename')


class ReconstructionCreate(BaseModel):
    capture_id: UUID = Field(..., title='Capture Id')
    id: Optional[UUID] = Field(None, title='Id')
    status: Optional[ReconstructionStatus] = None


class ReconstructionUpdate(BaseModel):
    capture_id: Optional[UUID] = Field(None, title='Capture Id')
    status: Optional[ReconstructionStatus] = None


class ReconstructionBatchUpdate(BaseModel):
    capture_id: Optional[UUID] = Field(None, title='Capture Id')
    id: UUID = Field(..., title='Id')
    status: Optional[ReconstructionStatus] = None


class ReconstructionRead(BaseModel):
    tenant_id: UUID = Field(..., title='Tenant Id')
    capture_id: UUID = Field(..., title='Capture Id')
    id: UUID = Field(..., title='Id')
    created_at: AwareDatetime = Field(..., title='Created At')
    updated_at: AwareDatetime = Field(..., title='Updated At')
    status: ReconstructionStatus

def capture_from_dto(create: CaptureCreate) -> Capture:
    data = create.model_dump(exclude_unset=True, mode="json")
    return Capture(**data)

def capture_from_dto_overwrite(instance: Capture, create: CaptureCreate) -> Capture:
    for field, value in create.model_dump(exclude_unset=True, mode="json").items():
        setattr(instance, field, value)
    return instance

def capture_to_dto(instance: Capture) -> CaptureRead:
    column_keys = tuple(attr.key for attr in sa_inspect(Capture).mapper.column_attrs)
    data = {k: getattr(instance, k) for k in column_keys}
    return CaptureRead.model_validate(data)

def capture_apply_dto(instance: Capture, update: CaptureUpdate) -> Capture:
    for field, value in update.model_dump(exclude_unset=True, mode="json").items():
        setattr(instance, field, value)
    return instance

def capture_apply_batch_update_dto(instance: Capture, update: CaptureBatchUpdate) -> Capture:
    for field, value in update.model_dump(exclude_unset=True, mode="json").items():
        setattr(instance, field, value)
    return instance

def reconstruction_from_dto(create: ReconstructionCreate) -> Reconstruction:
    data = create.model_dump(exclude_unset=True, mode="json")
    return Reconstruction(**data)

def reconstruction_from_dto_overwrite(instance: Reconstruction, create: ReconstructionCreate) -> Reconstruction:
    for field, value in create.model_dump(exclude_unset=True, mode="json").items():
        setattr(instance, field, value)
    return instance

def reconstruction_to_dto(instance: Reconstruction) -> ReconstructionRead:
    column_keys = tuple(attr.key for attr in sa_inspect(Reconstruction).mapper.column_attrs)
    data = {k: getattr(instance, k) for k in column_keys}
    return ReconstructionRead.model_validate(data)

def reconstruction_apply_dto(instance: Reconstruction, update: ReconstructionUpdate) -> Reconstruction:
    for field, value in update.model_dump(exclude_unset=True, mode="json").items():
        setattr(instance, field, value)
    return instance

def reconstruction_apply_batch_update_dto(instance: Reconstruction, update: ReconstructionBatchUpdate) -> Reconstruction:
    for field, value in update.model_dump(exclude_unset=True, mode="json").items():
        setattr(instance, field, value)
    return instance

def tenant_from_dto(create: TenantCreate) -> Tenant:
    data = create.model_dump(exclude_unset=True, mode="json")
    return Tenant(**data)

def tenant_from_dto_overwrite(instance: Tenant, create: TenantCreate) -> Tenant:
    for field, value in create.model_dump(exclude_unset=True, mode="json").items():
        setattr(instance, field, value)
    return instance

def tenant_to_dto(instance: Tenant) -> TenantRead:
    column_keys = tuple(attr.key for attr in sa_inspect(Tenant).mapper.column_attrs)
    data = {k: getattr(instance, k) for k in column_keys}
    return TenantRead.model_validate(data)

def tenant_apply_dto(instance: Tenant, update: TenantUpdate) -> Tenant:
    for field, value in update.model_dump(exclude_unset=True, mode="json").items():
        setattr(instance, field, value)
    return instance

def tenant_apply_batch_update_dto(instance: Tenant, update: TenantBatchUpdate) -> Tenant:
    for field, value in update.model_dump(exclude_unset=True, mode="json").items():
        setattr(instance, field, value)
    return instance
