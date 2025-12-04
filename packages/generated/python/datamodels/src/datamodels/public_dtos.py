from __future__ import annotations

from enum import StrEnum
from pydantic import AwareDatetime, BaseModel, Field
from typing import Optional
from uuid import UUID

from sqlalchemy import inspect as sa_inspect

from .public_tables import CaptureSession, Group, Layer, LocalizationMap, LocalizationSession, Node, Reconstruction, Tenant



class Model(BaseModel):
    pass


class GroupCreate(BaseModel):
    id: Optional[UUID] = Field(None, title='Id')
    name: str = Field(..., title='Name')
    parent_id: Optional[UUID] = Field(None, title='Parent Id')


class GroupUpdate(BaseModel):
    name: Optional[str] = Field(None, title='Name')
    parent_id: Optional[UUID] = Field(None, title='Parent Id')


class GroupBatchUpdate(BaseModel):
    id: UUID = Field(..., title='Id')
    name: Optional[str] = Field(None, title='Name')
    parent_id: Optional[UUID] = Field(None, title='Parent Id')


class GroupRead(BaseModel):
    id: UUID = Field(..., title='Id')
    created_at: AwareDatetime = Field(..., title='Created At')
    updated_at: AwareDatetime = Field(..., title='Updated At')
    name: str = Field(..., title='Name')
    parent_id: Optional[UUID] = Field(None, title='Parent Id')


class LayerCreate(BaseModel):
    id: Optional[UUID] = Field(None, title='Id')
    name: str = Field(..., title='Name')


class LayerUpdate(BaseModel):
    name: Optional[str] = Field(None, title='Name')


class LayerBatchUpdate(BaseModel):
    id: UUID = Field(..., title='Id')
    name: Optional[str] = Field(None, title='Name')


class LayerRead(BaseModel):
    id: UUID = Field(..., title='Id')
    created_at: AwareDatetime = Field(..., title='Created At')
    updated_at: AwareDatetime = Field(..., title='Updated At')
    name: str = Field(..., title='Name')


class LocalizationMapCreate(BaseModel):
    reconstruction_id: UUID = Field(..., title='Reconstruction Id')
    id: Optional[UUID] = Field(None, title='Id')
    rotation_y: float = Field(..., title='Rotation Y')
    position_x: float = Field(..., title='Position X')
    position_y: float = Field(..., title='Position Y')
    position_z: float = Field(..., title='Position Z')
    rotation_x: float = Field(..., title='Rotation X')
    rotation_z: float = Field(..., title='Rotation Z')
    rotation_w: float = Field(..., title='Rotation W')
    color: int = Field(..., title='Color')
    active: Optional[bool] = Field(None, title='Active')
    lighting: Optional[int] = Field(None, title='Lighting')
    name: Optional[str] = Field(None, title='Name')


class LocalizationMapUpdate(BaseModel):
    reconstruction_id: Optional[UUID] = Field(None, title='Reconstruction Id')
    rotation_y: Optional[float] = Field(None, title='Rotation Y')
    position_x: Optional[float] = Field(None, title='Position X')
    position_y: Optional[float] = Field(None, title='Position Y')
    position_z: Optional[float] = Field(None, title='Position Z')
    rotation_x: Optional[float] = Field(None, title='Rotation X')
    rotation_z: Optional[float] = Field(None, title='Rotation Z')
    rotation_w: Optional[float] = Field(None, title='Rotation W')
    color: Optional[int] = Field(None, title='Color')
    active: Optional[bool] = Field(None, title='Active')
    lighting: Optional[int] = Field(None, title='Lighting')
    name: Optional[str] = Field(None, title='Name')


class LocalizationMapBatchUpdate(BaseModel):
    reconstruction_id: Optional[UUID] = Field(None, title='Reconstruction Id')
    id: UUID = Field(..., title='Id')
    rotation_y: Optional[float] = Field(None, title='Rotation Y')
    position_x: Optional[float] = Field(None, title='Position X')
    position_y: Optional[float] = Field(None, title='Position Y')
    position_z: Optional[float] = Field(None, title='Position Z')
    rotation_x: Optional[float] = Field(None, title='Rotation X')
    rotation_z: Optional[float] = Field(None, title='Rotation Z')
    rotation_w: Optional[float] = Field(None, title='Rotation W')
    color: Optional[int] = Field(None, title='Color')
    active: Optional[bool] = Field(None, title='Active')
    lighting: Optional[int] = Field(None, title='Lighting')
    name: Optional[str] = Field(None, title='Name')


class LocalizationMapRead(BaseModel):
    reconstruction_id: UUID = Field(..., title='Reconstruction Id')
    id: UUID = Field(..., title='Id')
    rotation_y: float = Field(..., title='Rotation Y')
    position_x: float = Field(..., title='Position X')
    position_y: float = Field(..., title='Position Y')
    position_z: float = Field(..., title='Position Z')
    rotation_x: float = Field(..., title='Rotation X')
    updated_at: AwareDatetime = Field(..., title='Updated At')
    rotation_z: float = Field(..., title='Rotation Z')
    rotation_w: float = Field(..., title='Rotation W')
    color: int = Field(..., title='Color')
    created_at: AwareDatetime = Field(..., title='Created At')
    active: bool = Field(..., title='Active')
    lighting: Optional[int] = Field(None, title='Lighting')
    name: Optional[str] = Field(None, title='Name')


class LocalizationSessionCreate(BaseModel):
    id: Optional[UUID] = Field(None, title='Id')


class LocalizationSessionUpdate(BaseModel):
    pass


class LocalizationSessionBatchUpdate(BaseModel):
    id: UUID = Field(..., title='Id')


class LocalizationSessionRead(BaseModel):
    id: UUID = Field(..., title='Id')
    created_at: AwareDatetime = Field(..., title='Created At')
    container_id: str = Field(..., title='Container Id')
    container_url: str = Field(..., title='Container Url')


class NodeCreate(BaseModel):
    id: Optional[UUID] = Field(None, title='Id')
    rotation_z: float = Field(..., title='Rotation Z')
    position_y: float = Field(..., title='Position Y')
    position_z: float = Field(..., title='Position Z')
    rotation_x: float = Field(..., title='Rotation X')
    rotation_y: float = Field(..., title='Rotation Y')
    rotation_w: float = Field(..., title='Rotation W')
    position_x: float = Field(..., title='Position X')
    active: Optional[bool] = Field(None, title='Active')
    name: str = Field(..., title='Name')
    layer_id: Optional[UUID] = Field(None, title='Layer Id')
    parent_id: Optional[UUID] = Field(None, title='Parent Id')
    label_width: Optional[float] = Field(None, title='Label Width')
    label_height: Optional[float] = Field(None, title='Label Height')
    label_scale: Optional[float] = Field(None, title='Label Scale')
    link_type: Optional[int] = Field(None, title='Link Type')
    label_type: Optional[int] = Field(None, title='Label Type')
    link: Optional[str] = Field(None, title='Link')
    label: Optional[str] = Field(None, title='Label')


class NodeUpdate(BaseModel):
    rotation_z: Optional[float] = Field(None, title='Rotation Z')
    position_y: Optional[float] = Field(None, title='Position Y')
    position_z: Optional[float] = Field(None, title='Position Z')
    rotation_x: Optional[float] = Field(None, title='Rotation X')
    rotation_y: Optional[float] = Field(None, title='Rotation Y')
    rotation_w: Optional[float] = Field(None, title='Rotation W')
    position_x: Optional[float] = Field(None, title='Position X')
    active: Optional[bool] = Field(None, title='Active')
    name: Optional[str] = Field(None, title='Name')
    layer_id: Optional[UUID] = Field(None, title='Layer Id')
    parent_id: Optional[UUID] = Field(None, title='Parent Id')
    label_width: Optional[float] = Field(None, title='Label Width')
    label_height: Optional[float] = Field(None, title='Label Height')
    label_scale: Optional[float] = Field(None, title='Label Scale')
    link_type: Optional[int] = Field(None, title='Link Type')
    label_type: Optional[int] = Field(None, title='Label Type')
    link: Optional[str] = Field(None, title='Link')
    label: Optional[str] = Field(None, title='Label')


class NodeBatchUpdate(BaseModel):
    id: UUID = Field(..., title='Id')
    rotation_z: Optional[float] = Field(None, title='Rotation Z')
    position_y: Optional[float] = Field(None, title='Position Y')
    position_z: Optional[float] = Field(None, title='Position Z')
    rotation_x: Optional[float] = Field(None, title='Rotation X')
    rotation_y: Optional[float] = Field(None, title='Rotation Y')
    rotation_w: Optional[float] = Field(None, title='Rotation W')
    position_x: Optional[float] = Field(None, title='Position X')
    active: Optional[bool] = Field(None, title='Active')
    name: Optional[str] = Field(None, title='Name')
    layer_id: Optional[UUID] = Field(None, title='Layer Id')
    parent_id: Optional[UUID] = Field(None, title='Parent Id')
    label_width: Optional[float] = Field(None, title='Label Width')
    label_height: Optional[float] = Field(None, title='Label Height')
    label_scale: Optional[float] = Field(None, title='Label Scale')
    link_type: Optional[int] = Field(None, title='Link Type')
    label_type: Optional[int] = Field(None, title='Label Type')
    link: Optional[str] = Field(None, title='Link')
    label: Optional[str] = Field(None, title='Label')


class NodeRead(BaseModel):
    id: UUID = Field(..., title='Id')
    rotation_z: float = Field(..., title='Rotation Z')
    position_y: float = Field(..., title='Position Y')
    position_z: float = Field(..., title='Position Z')
    rotation_x: float = Field(..., title='Rotation X')
    rotation_y: float = Field(..., title='Rotation Y')
    created_at: AwareDatetime = Field(..., title='Created At')
    rotation_w: float = Field(..., title='Rotation W')
    updated_at: AwareDatetime = Field(..., title='Updated At')
    position_x: float = Field(..., title='Position X')
    active: bool = Field(..., title='Active')
    name: str = Field(..., title='Name')
    layer_id: Optional[UUID] = Field(None, title='Layer Id')
    parent_id: Optional[UUID] = Field(None, title='Parent Id')
    label_width: Optional[float] = Field(None, title='Label Width')
    label_height: Optional[float] = Field(None, title='Label Height')
    label_scale: Optional[float] = Field(None, title='Label Scale')
    link_type: Optional[int] = Field(None, title='Link Type')
    label_type: Optional[int] = Field(None, title='Label Type')
    link: Optional[str] = Field(None, title='Link')
    label: Optional[str] = Field(None, title='Label')


class TenantCreate(BaseModel):
    id: Optional[UUID] = Field(None, title='Id')


class TenantUpdate(BaseModel):
    pass


class TenantBatchUpdate(BaseModel):
    id: UUID = Field(..., title='Id')


class TenantRead(BaseModel):
    id: UUID = Field(..., title='Id')
    created_at: AwareDatetime = Field(..., title='Created At')


class DeviceType(StrEnum):
    ARFoundation = 'ARFoundation'
    Zed = 'Zed'


class OrchestrationStatus(StrEnum):
    queued = 'queued'
    pending = 'pending'
    running = 'running'
    succeeded = 'succeeded'
    cancelled = 'cancelled'
    failed = 'failed'


class CaptureSessionCreate(BaseModel):
    id: Optional[UUID] = Field(None, title='Id')
    device_type: DeviceType
    name: str = Field(..., title='Name')


class CaptureSessionUpdate(BaseModel):
    device_type: Optional[DeviceType] = None
    name: Optional[str] = Field(None, title='Name')


class CaptureSessionBatchUpdate(BaseModel):
    id: UUID = Field(..., title='Id')
    device_type: Optional[DeviceType] = None
    name: Optional[str] = Field(None, title='Name')


class CaptureSessionRead(BaseModel):
    id: UUID = Field(..., title='Id')
    created_at: AwareDatetime = Field(..., title='Created At')
    updated_at: AwareDatetime = Field(..., title='Updated At')
    device_type: DeviceType
    name: str = Field(..., title='Name')


class ReconstructionCreate(BaseModel):
    capture_session_id: UUID = Field(..., title='Capture Session Id')
    id: Optional[UUID] = Field(None, title='Id')
    orchestration_status: Optional[OrchestrationStatus] = None


class ReconstructionUpdate(BaseModel):
    capture_session_id: Optional[UUID] = Field(None, title='Capture Session Id')
    orchestration_status: Optional[OrchestrationStatus] = None


class ReconstructionBatchUpdate(BaseModel):
    capture_session_id: Optional[UUID] = Field(None, title='Capture Session Id')
    id: UUID = Field(..., title='Id')
    orchestration_status: Optional[OrchestrationStatus] = None


class ReconstructionRead(BaseModel):
    capture_session_id: UUID = Field(..., title='Capture Session Id')
    id: UUID = Field(..., title='Id')
    created_at: AwareDatetime = Field(..., title='Created At')
    updated_at: AwareDatetime = Field(..., title='Updated At')
    orchestration_status: OrchestrationStatus

def capture_session_from_dto(create: CaptureSessionCreate) -> CaptureSession:
    data = create.model_dump(exclude_unset=True, mode="json")
    return CaptureSession(**data)

def capture_session_from_dto_overwrite(instance: CaptureSession, create: CaptureSessionCreate) -> CaptureSession:
    for field, value in create.model_dump(exclude_unset=True, mode="json").items():
        setattr(instance, field, value)
    return instance

def capture_session_to_dto(instance: CaptureSession) -> CaptureSessionRead:
    column_keys = tuple(attr.key for attr in sa_inspect(CaptureSession).mapper.column_attrs)
    data = {k: getattr(instance, k) for k in column_keys}
    return CaptureSessionRead.model_validate(data)

def capture_session_apply_dto(instance: CaptureSession, update: CaptureSessionUpdate) -> CaptureSession:
    for field, value in update.model_dump(exclude_unset=True, mode="json").items():
        setattr(instance, field, value)
    return instance

def capture_session_apply_batch_update_dto(instance: CaptureSession, update: CaptureSessionBatchUpdate) -> CaptureSession:
    for field, value in update.model_dump(exclude_unset=True, mode="json").items():
        setattr(instance, field, value)
    return instance

def group_from_dto(create: GroupCreate) -> Group:
    data = create.model_dump(exclude_unset=True, mode="json")
    return Group(**data)

def group_from_dto_overwrite(instance: Group, create: GroupCreate) -> Group:
    for field, value in create.model_dump(exclude_unset=True, mode="json").items():
        setattr(instance, field, value)
    return instance

def group_to_dto(instance: Group) -> GroupRead:
    column_keys = tuple(attr.key for attr in sa_inspect(Group).mapper.column_attrs)
    data = {k: getattr(instance, k) for k in column_keys}
    return GroupRead.model_validate(data)

def group_apply_dto(instance: Group, update: GroupUpdate) -> Group:
    for field, value in update.model_dump(exclude_unset=True, mode="json").items():
        setattr(instance, field, value)
    return instance

def group_apply_batch_update_dto(instance: Group, update: GroupBatchUpdate) -> Group:
    for field, value in update.model_dump(exclude_unset=True, mode="json").items():
        setattr(instance, field, value)
    return instance

def layer_from_dto(create: LayerCreate) -> Layer:
    data = create.model_dump(exclude_unset=True, mode="json")
    return Layer(**data)

def layer_from_dto_overwrite(instance: Layer, create: LayerCreate) -> Layer:
    for field, value in create.model_dump(exclude_unset=True, mode="json").items():
        setattr(instance, field, value)
    return instance

def layer_to_dto(instance: Layer) -> LayerRead:
    column_keys = tuple(attr.key for attr in sa_inspect(Layer).mapper.column_attrs)
    data = {k: getattr(instance, k) for k in column_keys}
    return LayerRead.model_validate(data)

def layer_apply_dto(instance: Layer, update: LayerUpdate) -> Layer:
    for field, value in update.model_dump(exclude_unset=True, mode="json").items():
        setattr(instance, field, value)
    return instance

def layer_apply_batch_update_dto(instance: Layer, update: LayerBatchUpdate) -> Layer:
    for field, value in update.model_dump(exclude_unset=True, mode="json").items():
        setattr(instance, field, value)
    return instance

def localization_map_from_dto(create: LocalizationMapCreate) -> LocalizationMap:
    data = create.model_dump(exclude_unset=True, mode="json")
    return LocalizationMap(**data)

def localization_map_from_dto_overwrite(instance: LocalizationMap, create: LocalizationMapCreate) -> LocalizationMap:
    for field, value in create.model_dump(exclude_unset=True, mode="json").items():
        setattr(instance, field, value)
    return instance

def localization_map_to_dto(instance: LocalizationMap) -> LocalizationMapRead:
    column_keys = tuple(attr.key for attr in sa_inspect(LocalizationMap).mapper.column_attrs)
    data = {k: getattr(instance, k) for k in column_keys}
    return LocalizationMapRead.model_validate(data)

def localization_map_apply_dto(instance: LocalizationMap, update: LocalizationMapUpdate) -> LocalizationMap:
    for field, value in update.model_dump(exclude_unset=True, mode="json").items():
        setattr(instance, field, value)
    return instance

def localization_map_apply_batch_update_dto(instance: LocalizationMap, update: LocalizationMapBatchUpdate) -> LocalizationMap:
    for field, value in update.model_dump(exclude_unset=True, mode="json").items():
        setattr(instance, field, value)
    return instance

def localization_session_from_dto(create: LocalizationSessionCreate) -> LocalizationSession:
    data = create.model_dump(exclude_unset=True, mode="json")
    return LocalizationSession(**data)

def localization_session_from_dto_overwrite(instance: LocalizationSession, create: LocalizationSessionCreate) -> LocalizationSession:
    for field, value in create.model_dump(exclude_unset=True, mode="json").items():
        setattr(instance, field, value)
    return instance

def localization_session_to_dto(instance: LocalizationSession) -> LocalizationSessionRead:
    column_keys = tuple(attr.key for attr in sa_inspect(LocalizationSession).mapper.column_attrs)
    data = {k: getattr(instance, k) for k in column_keys}
    return LocalizationSessionRead.model_validate(data)

def localization_session_apply_dto(instance: LocalizationSession, update: LocalizationSessionUpdate) -> LocalizationSession:
    for field, value in update.model_dump(exclude_unset=True, mode="json").items():
        setattr(instance, field, value)
    return instance

def localization_session_apply_batch_update_dto(instance: LocalizationSession, update: LocalizationSessionBatchUpdate) -> LocalizationSession:
    for field, value in update.model_dump(exclude_unset=True, mode="json").items():
        setattr(instance, field, value)
    return instance

def node_from_dto(create: NodeCreate) -> Node:
    data = create.model_dump(exclude_unset=True, mode="json")
    return Node(**data)

def node_from_dto_overwrite(instance: Node, create: NodeCreate) -> Node:
    for field, value in create.model_dump(exclude_unset=True, mode="json").items():
        setattr(instance, field, value)
    return instance

def node_to_dto(instance: Node) -> NodeRead:
    column_keys = tuple(attr.key for attr in sa_inspect(Node).mapper.column_attrs)
    data = {k: getattr(instance, k) for k in column_keys}
    return NodeRead.model_validate(data)

def node_apply_dto(instance: Node, update: NodeUpdate) -> Node:
    for field, value in update.model_dump(exclude_unset=True, mode="json").items():
        setattr(instance, field, value)
    return instance

def node_apply_batch_update_dto(instance: Node, update: NodeBatchUpdate) -> Node:
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
