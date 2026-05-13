from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, Field
from sqlalchemy import inspect as sa_inspect

from .public_tables import (
    CaptureSession,
    DeviceType,
    Group,
    LabelType,
    Layer,
    LinkType,
    LocalizationEvaluation,
    LocalizationMap,
    LocalizationMapCameraPosition,
    LocalizationSession,
    Node,
    Reconstruction,
    ReconstructionStatus,
    SpatialRefSy,
    Tenant,
)


class Model(BaseModel):
    pass


class GroupCreate(BaseModel):
    id: UUID | None = Field(None, title="Id")
    name: str = Field(..., title="Name")
    parent_id: UUID | None = Field(None, title="Parent Id")


class GroupBatchCreate(BaseModel):
    id: UUID = Field(..., title="Id")
    name: str = Field(..., title="Name")
    parent_id: UUID | None = Field(None, title="Parent Id")


class GroupUpdate(BaseModel):
    name: str | None = Field(None, title="Name")
    parent_id: UUID | None = Field(None, title="Parent Id")


class GroupBatchUpdate(BaseModel):
    id: UUID = Field(..., title="Id")
    name: str | None = Field(None, title="Name")
    parent_id: UUID | None = Field(None, title="Parent Id")


class GroupRead(BaseModel):
    id: UUID = Field(..., title="Id")
    created_at: AwareDatetime = Field(..., title="Created At")
    updated_at: AwareDatetime = Field(..., title="Updated At")
    name: str = Field(..., title="Name")
    parent_id: UUID | None = Field(None, title="Parent Id")


class LayerCreate(BaseModel):
    id: UUID | None = Field(None, title="Id")
    name: str = Field(..., title="Name")


class LayerBatchCreate(BaseModel):
    id: UUID = Field(..., title="Id")
    name: str = Field(..., title="Name")


class LayerUpdate(BaseModel):
    name: str | None = Field(None, title="Name")


class LayerBatchUpdate(BaseModel):
    id: UUID = Field(..., title="Id")
    name: str | None = Field(None, title="Name")


class LayerRead(BaseModel):
    id: UUID = Field(..., title="Id")
    created_at: AwareDatetime = Field(..., title="Created At")
    updated_at: AwareDatetime = Field(..., title="Updated At")
    name: str = Field(..., title="Name")


class LocalizationEvaluationCreate(BaseModel):
    reconstruction_id: UUID = Field(..., title="Reconstruction Id")
    id: UUID | None = Field(None, title="Id")
    ransac_threshold: float = Field(..., title="Ransac Threshold")
    frame_timestamp: int = Field(..., title="Frame Timestamp")
    inlier_coverage: float = Field(..., title="Inlier Coverage")
    query_image_diagonal_px: float = Field(..., title="Query Image Diagonal Px")
    reproj_error_median: float = Field(..., title="Reproj Error Median")
    inlier_ratio: float = Field(..., title="Inlier Ratio")
    retrieval_top_k: int = Field(..., title="Retrieval Top K")
    num_inliers: int = Field(..., title="Num Inliers")
    num_matches: int = Field(..., title="Num Matches")
    num_correspondences: int = Field(..., title="Num Correspondences")
    succeeded: bool = Field(..., title="Succeeded")
    pipeline_version: str = Field(..., title="Pipeline Version")
    err_r_deg: float | None = Field(None, title="Err R Deg")
    err_t_m: float | None = Field(None, title="Err T M")
    pnp_covariance: list[Any] | None = Field(None, title="Pnp Covariance")
    se3_residual: list[Any] | None = Field(None, title="Se3 Residual")


class LocalizationEvaluationBatchCreate(BaseModel):
    reconstruction_id: UUID = Field(..., title="Reconstruction Id")
    id: UUID = Field(..., title="Id")
    ransac_threshold: float = Field(..., title="Ransac Threshold")
    frame_timestamp: int = Field(..., title="Frame Timestamp")
    inlier_coverage: float = Field(..., title="Inlier Coverage")
    query_image_diagonal_px: float = Field(..., title="Query Image Diagonal Px")
    reproj_error_median: float = Field(..., title="Reproj Error Median")
    inlier_ratio: float = Field(..., title="Inlier Ratio")
    retrieval_top_k: int = Field(..., title="Retrieval Top K")
    num_inliers: int = Field(..., title="Num Inliers")
    num_matches: int = Field(..., title="Num Matches")
    num_correspondences: int = Field(..., title="Num Correspondences")
    succeeded: bool = Field(..., title="Succeeded")
    pipeline_version: str = Field(..., title="Pipeline Version")
    err_r_deg: float | None = Field(None, title="Err R Deg")
    err_t_m: float | None = Field(None, title="Err T M")
    pnp_covariance: list[Any] | None = Field(None, title="Pnp Covariance")
    se3_residual: list[Any] | None = Field(None, title="Se3 Residual")


class LocalizationEvaluationUpdate(BaseModel):
    reconstruction_id: UUID | None = Field(None, title="Reconstruction Id")
    ransac_threshold: float | None = Field(None, title="Ransac Threshold")
    frame_timestamp: int | None = Field(None, title="Frame Timestamp")
    inlier_coverage: float | None = Field(None, title="Inlier Coverage")
    query_image_diagonal_px: float | None = Field(None, title="Query Image Diagonal Px")
    reproj_error_median: float | None = Field(None, title="Reproj Error Median")
    inlier_ratio: float | None = Field(None, title="Inlier Ratio")
    retrieval_top_k: int | None = Field(None, title="Retrieval Top K")
    num_inliers: int | None = Field(None, title="Num Inliers")
    num_matches: int | None = Field(None, title="Num Matches")
    num_correspondences: int | None = Field(None, title="Num Correspondences")
    succeeded: bool | None = Field(None, title="Succeeded")
    pipeline_version: str | None = Field(None, title="Pipeline Version")
    err_r_deg: float | None = Field(None, title="Err R Deg")
    err_t_m: float | None = Field(None, title="Err T M")
    pnp_covariance: list[Any] | None = Field(None, title="Pnp Covariance")
    se3_residual: list[Any] | None = Field(None, title="Se3 Residual")


class LocalizationEvaluationBatchUpdate(BaseModel):
    reconstruction_id: UUID | None = Field(None, title="Reconstruction Id")
    id: UUID = Field(..., title="Id")
    ransac_threshold: float | None = Field(None, title="Ransac Threshold")
    frame_timestamp: int | None = Field(None, title="Frame Timestamp")
    inlier_coverage: float | None = Field(None, title="Inlier Coverage")
    query_image_diagonal_px: float | None = Field(None, title="Query Image Diagonal Px")
    reproj_error_median: float | None = Field(None, title="Reproj Error Median")
    inlier_ratio: float | None = Field(None, title="Inlier Ratio")
    retrieval_top_k: int | None = Field(None, title="Retrieval Top K")
    num_inliers: int | None = Field(None, title="Num Inliers")
    num_matches: int | None = Field(None, title="Num Matches")
    num_correspondences: int | None = Field(None, title="Num Correspondences")
    succeeded: bool | None = Field(None, title="Succeeded")
    pipeline_version: str | None = Field(None, title="Pipeline Version")
    err_r_deg: float | None = Field(None, title="Err R Deg")
    err_t_m: float | None = Field(None, title="Err T M")
    pnp_covariance: list[Any] | None = Field(None, title="Pnp Covariance")
    se3_residual: list[Any] | None = Field(None, title="Se3 Residual")


class LocalizationEvaluationRead(BaseModel):
    reconstruction_id: UUID = Field(..., title="Reconstruction Id")
    id: UUID = Field(..., title="Id")
    ransac_threshold: float = Field(..., title="Ransac Threshold")
    frame_timestamp: int = Field(..., title="Frame Timestamp")
    updated_at: AwareDatetime = Field(..., title="Updated At")
    inlier_coverage: float = Field(..., title="Inlier Coverage")
    created_at: AwareDatetime = Field(..., title="Created At")
    query_image_diagonal_px: float = Field(..., title="Query Image Diagonal Px")
    reproj_error_median: float = Field(..., title="Reproj Error Median")
    inlier_ratio: float = Field(..., title="Inlier Ratio")
    retrieval_top_k: int = Field(..., title="Retrieval Top K")
    num_inliers: int = Field(..., title="Num Inliers")
    num_matches: int = Field(..., title="Num Matches")
    num_correspondences: int = Field(..., title="Num Correspondences")
    succeeded: bool = Field(..., title="Succeeded")
    pipeline_version: str = Field(..., title="Pipeline Version")
    err_r_deg: float | None = Field(None, title="Err R Deg")
    err_t_m: float | None = Field(None, title="Err T M")
    pnp_covariance: list[Any] | None = Field(None, title="Pnp Covariance")
    se3_residual: list[Any] | None = Field(None, title="Se3 Residual")


class LocalizationMapCreate(BaseModel):
    reconstruction_id: UUID = Field(..., title="Reconstruction Id")
    id: UUID | None = Field(None, title="Id")
    rotation_y: float = Field(..., title="Rotation Y")
    position_x: float = Field(..., title="Position X")
    position_y: float = Field(..., title="Position Y")
    position_z: float = Field(..., title="Position Z")
    rotation_x: float = Field(..., title="Rotation X")
    rotation_z: float = Field(..., title="Rotation Z")
    rotation_w: float = Field(..., title="Rotation W")
    color: int = Field(..., title="Color")
    active: bool | None = Field(None, title="Active")
    lighting: int | None = Field(None, title="Lighting")
    name: str | None = Field(None, title="Name")


class LocalizationMapBatchCreate(BaseModel):
    reconstruction_id: UUID = Field(..., title="Reconstruction Id")
    id: UUID = Field(..., title="Id")
    rotation_y: float = Field(..., title="Rotation Y")
    position_x: float = Field(..., title="Position X")
    position_y: float = Field(..., title="Position Y")
    position_z: float = Field(..., title="Position Z")
    rotation_x: float = Field(..., title="Rotation X")
    rotation_z: float = Field(..., title="Rotation Z")
    rotation_w: float = Field(..., title="Rotation W")
    color: int = Field(..., title="Color")
    active: bool | None = Field(None, title="Active")
    lighting: int | None = Field(None, title="Lighting")
    name: str | None = Field(None, title="Name")


class LocalizationMapUpdate(BaseModel):
    reconstruction_id: UUID | None = Field(None, title="Reconstruction Id")
    rotation_y: float | None = Field(None, title="Rotation Y")
    position_x: float | None = Field(None, title="Position X")
    position_y: float | None = Field(None, title="Position Y")
    position_z: float | None = Field(None, title="Position Z")
    rotation_x: float | None = Field(None, title="Rotation X")
    rotation_z: float | None = Field(None, title="Rotation Z")
    rotation_w: float | None = Field(None, title="Rotation W")
    color: int | None = Field(None, title="Color")
    active: bool | None = Field(None, title="Active")
    lighting: int | None = Field(None, title="Lighting")
    name: str | None = Field(None, title="Name")


class LocalizationMapBatchUpdate(BaseModel):
    reconstruction_id: UUID | None = Field(None, title="Reconstruction Id")
    id: UUID = Field(..., title="Id")
    rotation_y: float | None = Field(None, title="Rotation Y")
    position_x: float | None = Field(None, title="Position X")
    position_y: float | None = Field(None, title="Position Y")
    position_z: float | None = Field(None, title="Position Z")
    rotation_x: float | None = Field(None, title="Rotation X")
    rotation_z: float | None = Field(None, title="Rotation Z")
    rotation_w: float | None = Field(None, title="Rotation W")
    color: int | None = Field(None, title="Color")
    active: bool | None = Field(None, title="Active")
    lighting: int | None = Field(None, title="Lighting")
    name: str | None = Field(None, title="Name")


class LocalizationMapRead(BaseModel):
    reconstruction_id: UUID = Field(..., title="Reconstruction Id")
    id: UUID = Field(..., title="Id")
    rotation_y: float = Field(..., title="Rotation Y")
    position_x: float = Field(..., title="Position X")
    position_y: float = Field(..., title="Position Y")
    position_z: float = Field(..., title="Position Z")
    rotation_x: float = Field(..., title="Rotation X")
    updated_at: AwareDatetime = Field(..., title="Updated At")
    rotation_z: float = Field(..., title="Rotation Z")
    rotation_w: float = Field(..., title="Rotation W")
    color: int = Field(..., title="Color")
    created_at: AwareDatetime = Field(..., title="Created At")
    active: bool = Field(..., title="Active")
    lighting: int | None = Field(None, title="Lighting")
    name: str | None = Field(None, title="Name")


class LocalizationMapCameraPositionCreate(BaseModel):
    localization_map_id: UUID = Field(..., title="Localization Map Id")
    id: UUID | None = Field(None, title="Id")
    position_x: float = Field(..., title="Position X")
    position_y: float = Field(..., title="Position Y")
    position_z: float = Field(..., title="Position Z")


class LocalizationMapCameraPositionBatchCreate(BaseModel):
    localization_map_id: UUID = Field(..., title="Localization Map Id")
    id: UUID = Field(..., title="Id")
    position_x: float = Field(..., title="Position X")
    position_y: float = Field(..., title="Position Y")
    position_z: float = Field(..., title="Position Z")


class LocalizationMapCameraPositionUpdate(BaseModel):
    localization_map_id: UUID | None = Field(None, title="Localization Map Id")
    position_x: float | None = Field(None, title="Position X")
    position_y: float | None = Field(None, title="Position Y")
    position_z: float | None = Field(None, title="Position Z")


class LocalizationMapCameraPositionBatchUpdate(BaseModel):
    localization_map_id: UUID | None = Field(None, title="Localization Map Id")
    id: UUID = Field(..., title="Id")
    position_x: float | None = Field(None, title="Position X")
    position_y: float | None = Field(None, title="Position Y")
    position_z: float | None = Field(None, title="Position Z")


class LocalizationMapCameraPositionRead(BaseModel):
    localization_map_id: UUID = Field(..., title="Localization Map Id")
    id: UUID = Field(..., title="Id")
    position_x: float = Field(..., title="Position X")
    position_y: float = Field(..., title="Position Y")
    position_z: float = Field(..., title="Position Z")


class LocalizationSessionCreate(BaseModel):
    id: UUID | None = Field(None, title="Id")


class LocalizationSessionBatchCreate(BaseModel):
    id: UUID = Field(..., title="Id")


class LocalizationSessionUpdate(BaseModel):
    pass


class LocalizationSessionBatchUpdate(BaseModel):
    id: UUID = Field(..., title="Id")


class LocalizationSessionRead(BaseModel):
    id: UUID = Field(..., title="Id")
    created_at: AwareDatetime = Field(..., title="Created At")
    container_id: str = Field(..., title="Container Id")
    container_url: str = Field(..., title="Container Url")


class ReconstructionCreate(BaseModel):
    capture_session_id: UUID = Field(..., title="Capture Session Id")
    id: UUID | None = Field(None, title="Id")


class ReconstructionBatchCreate(BaseModel):
    capture_session_id: UUID = Field(..., title="Capture Session Id")
    id: UUID = Field(..., title="Id")


class ReconstructionUpdate(BaseModel):
    capture_session_id: UUID | None = Field(None, title="Capture Session Id")


class ReconstructionBatchUpdate(BaseModel):
    capture_session_id: UUID | None = Field(None, title="Capture Session Id")
    id: UUID = Field(..., title="Id")


class SpatialRefSyCreate(BaseModel):
    srid: int = Field(..., title="Srid")
    auth_name: str | None = Field(None, title="Auth Name")
    auth_srid: int | None = Field(None, title="Auth Srid")
    srtext: str | None = Field(None, title="Srtext")
    proj4text: str | None = Field(None, title="Proj4Text")


class SpatialRefSyBatchCreate(BaseModel):
    srid: int = Field(..., title="Srid")
    auth_name: str | None = Field(None, title="Auth Name")
    auth_srid: int | None = Field(None, title="Auth Srid")
    srtext: str | None = Field(None, title="Srtext")
    proj4text: str | None = Field(None, title="Proj4Text")


class SpatialRefSyUpdate(BaseModel):
    auth_name: str | None = Field(None, title="Auth Name")
    auth_srid: int | None = Field(None, title="Auth Srid")
    srtext: str | None = Field(None, title="Srtext")
    proj4text: str | None = Field(None, title="Proj4Text")


class SpatialRefSyBatchUpdate(BaseModel):
    srid: int = Field(..., title="Srid")
    auth_name: str | None = Field(None, title="Auth Name")
    auth_srid: int | None = Field(None, title="Auth Srid")
    srtext: str | None = Field(None, title="Srtext")
    proj4text: str | None = Field(None, title="Proj4Text")


class SpatialRefSyRead(BaseModel):
    srid: int = Field(..., title="Srid")
    auth_name: str | None = Field(None, title="Auth Name")
    auth_srid: int | None = Field(None, title="Auth Srid")
    srtext: str | None = Field(None, title="Srtext")
    proj4text: str | None = Field(None, title="Proj4Text")


class TenantCreate(BaseModel):
    id: UUID | None = Field(None, title="Id")


class TenantBatchCreate(BaseModel):
    id: UUID = Field(..., title="Id")


class TenantUpdate(BaseModel):
    pass


class TenantBatchUpdate(BaseModel):
    id: UUID = Field(..., title="Id")


class TenantRead(BaseModel):
    id: UUID = Field(..., title="Id")
    created_at: AwareDatetime = Field(..., title="Created At")


class CaptureSessionCreate(BaseModel):
    id: UUID | None = Field(None, title="Id")
    recorded_at: AwareDatetime | None = Field(None, title="Recorded At")
    device_type: DeviceType
    name: str | None = Field(None, title="Name")


class CaptureSessionBatchCreate(BaseModel):
    id: UUID = Field(..., title="Id")
    recorded_at: AwareDatetime | None = Field(None, title="Recorded At")
    device_type: DeviceType
    name: str | None = Field(None, title="Name")


class CaptureSessionUpdate(BaseModel):
    recorded_at: AwareDatetime | None = Field(None, title="Recorded At")
    device_type: DeviceType | None = None
    name: str | None = Field(None, title="Name")


class CaptureSessionBatchUpdate(BaseModel):
    id: UUID = Field(..., title="Id")
    recorded_at: AwareDatetime | None = Field(None, title="Recorded At")
    device_type: DeviceType | None = None
    name: str | None = Field(None, title="Name")


class CaptureSessionRead(BaseModel):
    id: UUID = Field(..., title="Id")
    created_at: AwareDatetime = Field(..., title="Created At")
    updated_at: AwareDatetime = Field(..., title="Updated At")
    recorded_at: AwareDatetime = Field(..., title="Recorded At")
    device_type: DeviceType
    name: str | None = Field(None, title="Name")


class NodeCreate(BaseModel):
    id: UUID | None = Field(None, title="Id")
    rotation_z: float = Field(..., title="Rotation Z")
    position_y: float = Field(..., title="Position Y")
    position_z: float = Field(..., title="Position Z")
    rotation_x: float = Field(..., title="Rotation X")
    rotation_y: float = Field(..., title="Rotation Y")
    rotation_w: float = Field(..., title="Rotation W")
    position_x: float = Field(..., title="Position X")
    link_type: LinkType
    label_type: LabelType
    active: bool | None = Field(None, title="Active")
    layer_id: UUID | None = Field(None, title="Layer Id")
    parent_id: UUID | None = Field(None, title="Parent Id")
    label_width: float | None = Field(None, title="Label Width")
    label_height: float | None = Field(None, title="Label Height")
    label_scale: float | None = Field(None, title="Label Scale")
    link: str | None = Field(None, title="Link")
    label: str | None = Field(None, title="Label")
    name: str | None = Field(None, title="Name")


class NodeBatchCreate(BaseModel):
    id: UUID = Field(..., title="Id")
    rotation_z: float = Field(..., title="Rotation Z")
    position_y: float = Field(..., title="Position Y")
    position_z: float = Field(..., title="Position Z")
    rotation_x: float = Field(..., title="Rotation X")
    rotation_y: float = Field(..., title="Rotation Y")
    rotation_w: float = Field(..., title="Rotation W")
    position_x: float = Field(..., title="Position X")
    link_type: LinkType
    label_type: LabelType
    active: bool | None = Field(None, title="Active")
    layer_id: UUID | None = Field(None, title="Layer Id")
    parent_id: UUID | None = Field(None, title="Parent Id")
    label_width: float | None = Field(None, title="Label Width")
    label_height: float | None = Field(None, title="Label Height")
    label_scale: float | None = Field(None, title="Label Scale")
    link: str | None = Field(None, title="Link")
    label: str | None = Field(None, title="Label")
    name: str | None = Field(None, title="Name")


class NodeUpdate(BaseModel):
    rotation_z: float | None = Field(None, title="Rotation Z")
    position_y: float | None = Field(None, title="Position Y")
    position_z: float | None = Field(None, title="Position Z")
    rotation_x: float | None = Field(None, title="Rotation X")
    rotation_y: float | None = Field(None, title="Rotation Y")
    rotation_w: float | None = Field(None, title="Rotation W")
    position_x: float | None = Field(None, title="Position X")
    link_type: LinkType | None = None
    label_type: LabelType | None = None
    active: bool | None = Field(None, title="Active")
    layer_id: UUID | None = Field(None, title="Layer Id")
    parent_id: UUID | None = Field(None, title="Parent Id")
    label_width: float | None = Field(None, title="Label Width")
    label_height: float | None = Field(None, title="Label Height")
    label_scale: float | None = Field(None, title="Label Scale")
    link: str | None = Field(None, title="Link")
    label: str | None = Field(None, title="Label")
    name: str | None = Field(None, title="Name")


class NodeBatchUpdate(BaseModel):
    id: UUID = Field(..., title="Id")
    rotation_z: float | None = Field(None, title="Rotation Z")
    position_y: float | None = Field(None, title="Position Y")
    position_z: float | None = Field(None, title="Position Z")
    rotation_x: float | None = Field(None, title="Rotation X")
    rotation_y: float | None = Field(None, title="Rotation Y")
    rotation_w: float | None = Field(None, title="Rotation W")
    position_x: float | None = Field(None, title="Position X")
    link_type: LinkType | None = None
    label_type: LabelType | None = None
    active: bool | None = Field(None, title="Active")
    layer_id: UUID | None = Field(None, title="Layer Id")
    parent_id: UUID | None = Field(None, title="Parent Id")
    label_width: float | None = Field(None, title="Label Width")
    label_height: float | None = Field(None, title="Label Height")
    label_scale: float | None = Field(None, title="Label Scale")
    link: str | None = Field(None, title="Link")
    label: str | None = Field(None, title="Label")
    name: str | None = Field(None, title="Name")


class NodeRead(BaseModel):
    id: UUID = Field(..., title="Id")
    rotation_z: float = Field(..., title="Rotation Z")
    position_y: float = Field(..., title="Position Y")
    position_z: float = Field(..., title="Position Z")
    rotation_x: float = Field(..., title="Rotation X")
    rotation_y: float = Field(..., title="Rotation Y")
    created_at: AwareDatetime = Field(..., title="Created At")
    rotation_w: float = Field(..., title="Rotation W")
    updated_at: AwareDatetime = Field(..., title="Updated At")
    position_x: float = Field(..., title="Position X")
    link_type: LinkType
    label_type: LabelType
    active: bool = Field(..., title="Active")
    layer_id: UUID | None = Field(None, title="Layer Id")
    parent_id: UUID | None = Field(None, title="Parent Id")
    label_width: float | None = Field(None, title="Label Width")
    label_height: float | None = Field(None, title="Label Height")
    label_scale: float | None = Field(None, title="Label Scale")
    link: str | None = Field(None, title="Link")
    label: str | None = Field(None, title="Label")
    name: str | None = Field(None, title="Name")


class ReconstructionRead(BaseModel):
    capture_session_id: UUID = Field(..., title="Capture Session Id")
    id: UUID = Field(..., title="Id")
    created_at: AwareDatetime = Field(..., title="Created At")
    updated_at: AwareDatetime = Field(..., title="Updated At")
    status: ReconstructionStatus
    manifest_version: int = Field(..., title="Manifest Version")
    manifest: dict[str, Any] = Field(..., title="Manifest")
    progress_current: int | None = Field(None, title="Progress Current")
    progress_total: int | None = Field(None, title="Progress Total")
    progress_attempt: int | None = Field(None, title="Progress Attempt")
    error: str | None = Field(None, title="Error")


def capture_session_from_dto(create: CaptureSessionCreate) -> CaptureSession:
    data = create.model_dump(exclude_unset=True, mode="json")
    return CaptureSession(**data)


def capture_session_from_batch_create_dto(create: CaptureSessionBatchCreate) -> CaptureSession:
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


def capture_session_apply_batch_update_dto(
    instance: CaptureSession, update: CaptureSessionBatchUpdate
) -> CaptureSession:
    for field, value in update.model_dump(exclude_unset=True, mode="json").items():
        setattr(instance, field, value)
    return instance


def group_from_dto(create: GroupCreate) -> Group:
    data = create.model_dump(exclude_unset=True, mode="json")
    return Group(**data)


def group_from_batch_create_dto(create: GroupBatchCreate) -> Group:
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


def layer_from_batch_create_dto(create: LayerBatchCreate) -> Layer:
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


def localization_evaluation_from_dto(create: LocalizationEvaluationCreate) -> LocalizationEvaluation:
    data = create.model_dump(exclude_unset=True, mode="json")
    return LocalizationEvaluation(**data)


def localization_evaluation_from_batch_create_dto(create: LocalizationEvaluationBatchCreate) -> LocalizationEvaluation:
    data = create.model_dump(exclude_unset=True, mode="json")
    return LocalizationEvaluation(**data)


def localization_evaluation_from_dto_overwrite(
    instance: LocalizationEvaluation, create: LocalizationEvaluationCreate
) -> LocalizationEvaluation:
    for field, value in create.model_dump(exclude_unset=True, mode="json").items():
        setattr(instance, field, value)
    return instance


def localization_evaluation_to_dto(instance: LocalizationEvaluation) -> LocalizationEvaluationRead:
    column_keys = tuple(attr.key for attr in sa_inspect(LocalizationEvaluation).mapper.column_attrs)
    data = {k: getattr(instance, k) for k in column_keys}
    return LocalizationEvaluationRead.model_validate(data)


def localization_evaluation_apply_dto(
    instance: LocalizationEvaluation, update: LocalizationEvaluationUpdate
) -> LocalizationEvaluation:
    for field, value in update.model_dump(exclude_unset=True, mode="json").items():
        setattr(instance, field, value)
    return instance


def localization_evaluation_apply_batch_update_dto(
    instance: LocalizationEvaluation, update: LocalizationEvaluationBatchUpdate
) -> LocalizationEvaluation:
    for field, value in update.model_dump(exclude_unset=True, mode="json").items():
        setattr(instance, field, value)
    return instance


def localization_map_from_dto(create: LocalizationMapCreate) -> LocalizationMap:
    data = create.model_dump(exclude_unset=True, mode="json")
    return LocalizationMap(**data)


def localization_map_from_batch_create_dto(create: LocalizationMapBatchCreate) -> LocalizationMap:
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


def localization_map_apply_batch_update_dto(
    instance: LocalizationMap, update: LocalizationMapBatchUpdate
) -> LocalizationMap:
    for field, value in update.model_dump(exclude_unset=True, mode="json").items():
        setattr(instance, field, value)
    return instance


def localization_map_camera_position_from_dto(
    create: LocalizationMapCameraPositionCreate,
) -> LocalizationMapCameraPosition:
    data = create.model_dump(exclude_unset=True, mode="json")
    return LocalizationMapCameraPosition(**data)


def localization_map_camera_position_from_batch_create_dto(
    create: LocalizationMapCameraPositionBatchCreate,
) -> LocalizationMapCameraPosition:
    data = create.model_dump(exclude_unset=True, mode="json")
    return LocalizationMapCameraPosition(**data)


def localization_map_camera_position_from_dto_overwrite(
    instance: LocalizationMapCameraPosition, create: LocalizationMapCameraPositionCreate
) -> LocalizationMapCameraPosition:
    for field, value in create.model_dump(exclude_unset=True, mode="json").items():
        setattr(instance, field, value)
    return instance


def localization_map_camera_position_to_dto(
    instance: LocalizationMapCameraPosition,
) -> LocalizationMapCameraPositionRead:
    column_keys = tuple(attr.key for attr in sa_inspect(LocalizationMapCameraPosition).mapper.column_attrs)
    data = {k: getattr(instance, k) for k in column_keys}
    return LocalizationMapCameraPositionRead.model_validate(data)


def localization_map_camera_position_apply_dto(
    instance: LocalizationMapCameraPosition, update: LocalizationMapCameraPositionUpdate
) -> LocalizationMapCameraPosition:
    for field, value in update.model_dump(exclude_unset=True, mode="json").items():
        setattr(instance, field, value)
    return instance


def localization_map_camera_position_apply_batch_update_dto(
    instance: LocalizationMapCameraPosition, update: LocalizationMapCameraPositionBatchUpdate
) -> LocalizationMapCameraPosition:
    for field, value in update.model_dump(exclude_unset=True, mode="json").items():
        setattr(instance, field, value)
    return instance


def localization_session_from_dto(create: LocalizationSessionCreate) -> LocalizationSession:
    data = create.model_dump(exclude_unset=True, mode="json")
    return LocalizationSession(**data)


def localization_session_from_batch_create_dto(create: LocalizationSessionBatchCreate) -> LocalizationSession:
    data = create.model_dump(exclude_unset=True, mode="json")
    return LocalizationSession(**data)


def localization_session_from_dto_overwrite(
    instance: LocalizationSession, create: LocalizationSessionCreate
) -> LocalizationSession:
    for field, value in create.model_dump(exclude_unset=True, mode="json").items():
        setattr(instance, field, value)
    return instance


def localization_session_to_dto(instance: LocalizationSession) -> LocalizationSessionRead:
    column_keys = tuple(attr.key for attr in sa_inspect(LocalizationSession).mapper.column_attrs)
    data = {k: getattr(instance, k) for k in column_keys}
    return LocalizationSessionRead.model_validate(data)


def localization_session_apply_dto(
    instance: LocalizationSession, update: LocalizationSessionUpdate
) -> LocalizationSession:
    for field, value in update.model_dump(exclude_unset=True, mode="json").items():
        setattr(instance, field, value)
    return instance


def localization_session_apply_batch_update_dto(
    instance: LocalizationSession, update: LocalizationSessionBatchUpdate
) -> LocalizationSession:
    for field, value in update.model_dump(exclude_unset=True, mode="json").items():
        setattr(instance, field, value)
    return instance


def node_from_dto(create: NodeCreate) -> Node:
    data = create.model_dump(exclude_unset=True, mode="json")
    return Node(**data)


def node_from_batch_create_dto(create: NodeBatchCreate) -> Node:
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


def reconstruction_from_batch_create_dto(create: ReconstructionBatchCreate) -> Reconstruction:
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


def reconstruction_apply_batch_update_dto(
    instance: Reconstruction, update: ReconstructionBatchUpdate
) -> Reconstruction:
    for field, value in update.model_dump(exclude_unset=True, mode="json").items():
        setattr(instance, field, value)
    return instance


def spatial_ref_sy_from_dto(create: SpatialRefSyCreate) -> SpatialRefSy:
    data = create.model_dump(exclude_unset=True, mode="json")
    return SpatialRefSy(**data)


def spatial_ref_sy_from_batch_create_dto(create: SpatialRefSyBatchCreate) -> SpatialRefSy:
    data = create.model_dump(exclude_unset=True, mode="json")
    return SpatialRefSy(**data)


def spatial_ref_sy_from_dto_overwrite(instance: SpatialRefSy, create: SpatialRefSyCreate) -> SpatialRefSy:
    for field, value in create.model_dump(exclude_unset=True, mode="json").items():
        setattr(instance, field, value)
    return instance


def spatial_ref_sy_to_dto(instance: SpatialRefSy) -> SpatialRefSyRead:
    column_keys = tuple(attr.key for attr in sa_inspect(SpatialRefSy).mapper.column_attrs)
    data = {k: getattr(instance, k) for k in column_keys}
    return SpatialRefSyRead.model_validate(data)


def spatial_ref_sy_apply_dto(instance: SpatialRefSy, update: SpatialRefSyUpdate) -> SpatialRefSy:
    for field, value in update.model_dump(exclude_unset=True, mode="json").items():
        setattr(instance, field, value)
    return instance


def spatial_ref_sy_apply_batch_update_dto(instance: SpatialRefSy, update: SpatialRefSyBatchUpdate) -> SpatialRefSy:
    for field, value in update.model_dump(exclude_unset=True, mode="json").items():
        setattr(instance, field, value)
    return instance


def tenant_from_dto(create: TenantCreate) -> Tenant:
    data = create.model_dump(exclude_unset=True, mode="json")
    return Tenant(**data)


def tenant_from_batch_create_dto(create: TenantBatchCreate) -> Tenant:
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
