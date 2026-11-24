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
    name: str = Field(..., title="Name")
    id: UUID | None = Field(default=None, title="Id")
    parent_id: UUID | None = Field(default=None, title="Parent Id")


class GroupBatchCreate(BaseModel):
    name: str = Field(..., title="Name")
    id: UUID = Field(..., title="Id")
    parent_id: UUID | None = Field(default=None, title="Parent Id")


class GroupUpdate(BaseModel):
    name: str | None = Field(default=None, title="Name")
    parent_id: UUID | None = Field(default=None, title="Parent Id")


class GroupBatchUpdate(BaseModel):
    name: str | None = Field(default=None, title="Name")
    id: UUID = Field(..., title="Id")
    parent_id: UUID | None = Field(default=None, title="Parent Id")


class GroupRead(BaseModel):
    created_at: AwareDatetime = Field(..., title="Created At")
    updated_at: AwareDatetime = Field(..., title="Updated At")
    name: str = Field(..., title="Name")
    id: UUID = Field(..., title="Id")
    parent_id: UUID | None = Field(default=None, title="Parent Id")


class LayerCreate(BaseModel):
    name: str = Field(..., title="Name")
    id: UUID | None = Field(default=None, title="Id")


class LayerBatchCreate(BaseModel):
    name: str = Field(..., title="Name")
    id: UUID = Field(..., title="Id")


class LayerUpdate(BaseModel):
    name: str | None = Field(default=None, title="Name")


class LayerBatchUpdate(BaseModel):
    name: str | None = Field(default=None, title="Name")
    id: UUID = Field(..., title="Id")


class LayerRead(BaseModel):
    created_at: AwareDatetime = Field(..., title="Created At")
    updated_at: AwareDatetime = Field(..., title="Updated At")
    name: str = Field(..., title="Name")
    id: UUID = Field(..., title="Id")


class LocalizationEvaluationCreate(BaseModel):
    reconstruction_id: UUID = Field(..., title="Reconstruction Id")
    frame_timestamp: int = Field(..., title="Frame Timestamp")
    retrieval_top_k: int = Field(..., title="Retrieval Top K")
    ransac_threshold: float = Field(..., title="Ransac Threshold")
    pipeline_version: str = Field(..., title="Pipeline Version")
    succeeded: bool = Field(..., title="Succeeded")
    num_correspondences: int = Field(..., title="Num Correspondences")
    num_matches: int = Field(..., title="Num Matches")
    num_inliers: int = Field(..., title="Num Inliers")
    inlier_ratio: float = Field(..., title="Inlier Ratio")
    inlier_coverage: float = Field(..., title="Inlier Coverage")
    reproj_error_median: float = Field(..., title="Reproj Error Median")
    query_image_diagonal_px: float = Field(..., title="Query Image Diagonal Px")
    id: UUID | None = Field(default=None, title="Id")
    pnp_covariance: list[Any] | None = Field(default=None, title="Pnp Covariance")
    se3_residual: list[Any] | None = Field(default=None, title="Se3 Residual")
    err_t_m: float | None = Field(default=None, title="Err T M")
    err_r_deg: float | None = Field(default=None, title="Err R Deg")


class LocalizationEvaluationBatchCreate(BaseModel):
    reconstruction_id: UUID = Field(..., title="Reconstruction Id")
    frame_timestamp: int = Field(..., title="Frame Timestamp")
    retrieval_top_k: int = Field(..., title="Retrieval Top K")
    ransac_threshold: float = Field(..., title="Ransac Threshold")
    pipeline_version: str = Field(..., title="Pipeline Version")
    succeeded: bool = Field(..., title="Succeeded")
    num_correspondences: int = Field(..., title="Num Correspondences")
    num_matches: int = Field(..., title="Num Matches")
    num_inliers: int = Field(..., title="Num Inliers")
    inlier_ratio: float = Field(..., title="Inlier Ratio")
    inlier_coverage: float = Field(..., title="Inlier Coverage")
    reproj_error_median: float = Field(..., title="Reproj Error Median")
    query_image_diagonal_px: float = Field(..., title="Query Image Diagonal Px")
    id: UUID = Field(..., title="Id")
    pnp_covariance: list[Any] | None = Field(default=None, title="Pnp Covariance")
    se3_residual: list[Any] | None = Field(default=None, title="Se3 Residual")
    err_t_m: float | None = Field(default=None, title="Err T M")
    err_r_deg: float | None = Field(default=None, title="Err R Deg")


class LocalizationEvaluationUpdate(BaseModel):
    reconstruction_id: UUID | None = Field(default=None, title="Reconstruction Id")
    frame_timestamp: int | None = Field(default=None, title="Frame Timestamp")
    retrieval_top_k: int | None = Field(default=None, title="Retrieval Top K")
    ransac_threshold: float | None = Field(default=None, title="Ransac Threshold")
    pipeline_version: str | None = Field(default=None, title="Pipeline Version")
    succeeded: bool | None = Field(default=None, title="Succeeded")
    num_correspondences: int | None = Field(default=None, title="Num Correspondences")
    num_matches: int | None = Field(default=None, title="Num Matches")
    num_inliers: int | None = Field(default=None, title="Num Inliers")
    inlier_ratio: float | None = Field(default=None, title="Inlier Ratio")
    inlier_coverage: float | None = Field(default=None, title="Inlier Coverage")
    reproj_error_median: float | None = Field(default=None, title="Reproj Error Median")
    query_image_diagonal_px: float | None = Field(default=None, title="Query Image Diagonal Px")
    pnp_covariance: list[Any] | None = Field(default=None, title="Pnp Covariance")
    se3_residual: list[Any] | None = Field(default=None, title="Se3 Residual")
    err_t_m: float | None = Field(default=None, title="Err T M")
    err_r_deg: float | None = Field(default=None, title="Err R Deg")


class LocalizationEvaluationBatchUpdate(BaseModel):
    reconstruction_id: UUID | None = Field(default=None, title="Reconstruction Id")
    frame_timestamp: int | None = Field(default=None, title="Frame Timestamp")
    retrieval_top_k: int | None = Field(default=None, title="Retrieval Top K")
    ransac_threshold: float | None = Field(default=None, title="Ransac Threshold")
    pipeline_version: str | None = Field(default=None, title="Pipeline Version")
    succeeded: bool | None = Field(default=None, title="Succeeded")
    num_correspondences: int | None = Field(default=None, title="Num Correspondences")
    num_matches: int | None = Field(default=None, title="Num Matches")
    num_inliers: int | None = Field(default=None, title="Num Inliers")
    inlier_ratio: float | None = Field(default=None, title="Inlier Ratio")
    inlier_coverage: float | None = Field(default=None, title="Inlier Coverage")
    reproj_error_median: float | None = Field(default=None, title="Reproj Error Median")
    query_image_diagonal_px: float | None = Field(default=None, title="Query Image Diagonal Px")
    id: UUID = Field(..., title="Id")
    pnp_covariance: list[Any] | None = Field(default=None, title="Pnp Covariance")
    se3_residual: list[Any] | None = Field(default=None, title="Se3 Residual")
    err_t_m: float | None = Field(default=None, title="Err T M")
    err_r_deg: float | None = Field(default=None, title="Err R Deg")


class LocalizationEvaluationRead(BaseModel):
    created_at: AwareDatetime = Field(..., title="Created At")
    updated_at: AwareDatetime = Field(..., title="Updated At")
    reconstruction_id: UUID = Field(..., title="Reconstruction Id")
    frame_timestamp: int = Field(..., title="Frame Timestamp")
    retrieval_top_k: int = Field(..., title="Retrieval Top K")
    ransac_threshold: float = Field(..., title="Ransac Threshold")
    pipeline_version: str = Field(..., title="Pipeline Version")
    succeeded: bool = Field(..., title="Succeeded")
    num_correspondences: int = Field(..., title="Num Correspondences")
    num_matches: int = Field(..., title="Num Matches")
    num_inliers: int = Field(..., title="Num Inliers")
    inlier_ratio: float = Field(..., title="Inlier Ratio")
    inlier_coverage: float = Field(..., title="Inlier Coverage")
    reproj_error_median: float = Field(..., title="Reproj Error Median")
    query_image_diagonal_px: float = Field(..., title="Query Image Diagonal Px")
    id: UUID = Field(..., title="Id")
    pnp_covariance: list[Any] | None = Field(default=None, title="Pnp Covariance")
    se3_residual: list[Any] | None = Field(default=None, title="Se3 Residual")
    err_t_m: float | None = Field(default=None, title="Err T M")
    err_r_deg: float | None = Field(default=None, title="Err R Deg")


class LocalizationMapCreate(BaseModel):
    reconstruction_id: UUID = Field(..., title="Reconstruction Id")
    position_x: float = Field(..., title="Position X")
    position_y: float = Field(..., title="Position Y")
    position_z: float = Field(..., title="Position Z")
    rotation_x: float = Field(..., title="Rotation X")
    rotation_y: float = Field(..., title="Rotation Y")
    rotation_z: float = Field(..., title="Rotation Z")
    rotation_w: float = Field(..., title="Rotation W")
    active: bool | None = Field(default=None, title="Active")
    color: int = Field(..., title="Color")
    id: UUID | None = Field(default=None, title="Id")
    name: str | None = Field(default=None, title="Name")
    lighting: int | None = Field(default=None, title="Lighting")


class LocalizationMapBatchCreate(BaseModel):
    reconstruction_id: UUID = Field(..., title="Reconstruction Id")
    position_x: float = Field(..., title="Position X")
    position_y: float = Field(..., title="Position Y")
    position_z: float = Field(..., title="Position Z")
    rotation_x: float = Field(..., title="Rotation X")
    rotation_y: float = Field(..., title="Rotation Y")
    rotation_z: float = Field(..., title="Rotation Z")
    rotation_w: float = Field(..., title="Rotation W")
    active: bool | None = Field(default=None, title="Active")
    color: int = Field(..., title="Color")
    id: UUID = Field(..., title="Id")
    name: str | None = Field(default=None, title="Name")
    lighting: int | None = Field(default=None, title="Lighting")


class LocalizationMapUpdate(BaseModel):
    reconstruction_id: UUID | None = Field(default=None, title="Reconstruction Id")
    position_x: float | None = Field(default=None, title="Position X")
    position_y: float | None = Field(default=None, title="Position Y")
    position_z: float | None = Field(default=None, title="Position Z")
    rotation_x: float | None = Field(default=None, title="Rotation X")
    rotation_y: float | None = Field(default=None, title="Rotation Y")
    rotation_z: float | None = Field(default=None, title="Rotation Z")
    rotation_w: float | None = Field(default=None, title="Rotation W")
    active: bool | None = Field(default=None, title="Active")
    color: int | None = Field(default=None, title="Color")
    name: str | None = Field(default=None, title="Name")
    lighting: int | None = Field(default=None, title="Lighting")


class LocalizationMapBatchUpdate(BaseModel):
    reconstruction_id: UUID | None = Field(default=None, title="Reconstruction Id")
    position_x: float | None = Field(default=None, title="Position X")
    position_y: float | None = Field(default=None, title="Position Y")
    position_z: float | None = Field(default=None, title="Position Z")
    rotation_x: float | None = Field(default=None, title="Rotation X")
    rotation_y: float | None = Field(default=None, title="Rotation Y")
    rotation_z: float | None = Field(default=None, title="Rotation Z")
    rotation_w: float | None = Field(default=None, title="Rotation W")
    active: bool | None = Field(default=None, title="Active")
    color: int | None = Field(default=None, title="Color")
    id: UUID = Field(..., title="Id")
    name: str | None = Field(default=None, title="Name")
    lighting: int | None = Field(default=None, title="Lighting")


class LocalizationMapRead(BaseModel):
    created_at: AwareDatetime = Field(..., title="Created At")
    updated_at: AwareDatetime = Field(..., title="Updated At")
    reconstruction_id: UUID = Field(..., title="Reconstruction Id")
    position_x: float = Field(..., title="Position X")
    position_y: float = Field(..., title="Position Y")
    position_z: float = Field(..., title="Position Z")
    rotation_x: float = Field(..., title="Rotation X")
    rotation_y: float = Field(..., title="Rotation Y")
    rotation_z: float = Field(..., title="Rotation Z")
    rotation_w: float = Field(..., title="Rotation W")
    active: bool = Field(..., title="Active")
    color: int = Field(..., title="Color")
    id: UUID = Field(..., title="Id")
    name: str | None = Field(default=None, title="Name")
    lighting: int | None = Field(default=None, title="Lighting")


class LocalizationMapCameraPositionCreate(BaseModel):
    localization_map_id: UUID = Field(..., title="Localization Map Id")
    position_x: float = Field(..., title="Position X")
    position_y: float = Field(..., title="Position Y")
    position_z: float = Field(..., title="Position Z")
    id: UUID | None = Field(default=None, title="Id")


class LocalizationMapCameraPositionBatchCreate(BaseModel):
    localization_map_id: UUID = Field(..., title="Localization Map Id")
    position_x: float = Field(..., title="Position X")
    position_y: float = Field(..., title="Position Y")
    position_z: float = Field(..., title="Position Z")
    id: UUID = Field(..., title="Id")


class LocalizationMapCameraPositionUpdate(BaseModel):
    localization_map_id: UUID | None = Field(default=None, title="Localization Map Id")
    position_x: float | None = Field(default=None, title="Position X")
    position_y: float | None = Field(default=None, title="Position Y")
    position_z: float | None = Field(default=None, title="Position Z")


class LocalizationMapCameraPositionBatchUpdate(BaseModel):
    localization_map_id: UUID | None = Field(default=None, title="Localization Map Id")
    position_x: float | None = Field(default=None, title="Position X")
    position_y: float | None = Field(default=None, title="Position Y")
    position_z: float | None = Field(default=None, title="Position Z")
    id: UUID = Field(..., title="Id")


class LocalizationMapCameraPositionRead(BaseModel):
    localization_map_id: UUID = Field(..., title="Localization Map Id")
    position_x: float = Field(..., title="Position X")
    position_y: float = Field(..., title="Position Y")
    position_z: float = Field(..., title="Position Z")
    id: UUID = Field(..., title="Id")


class LocalizationSessionCreate(BaseModel):
    id: UUID | None = Field(default=None, title="Id")


class LocalizationSessionBatchCreate(BaseModel):
    id: UUID = Field(..., title="Id")


class LocalizationSessionUpdate(BaseModel):
    pass


class LocalizationSessionBatchUpdate(BaseModel):
    id: UUID = Field(..., title="Id")


class LocalizationSessionRead(BaseModel):
    created_at: AwareDatetime = Field(..., title="Created At")
    container_id: str = Field(..., title="Container Id")
    container_url: str = Field(..., title="Container Url")
    id: UUID = Field(..., title="Id")


class ReconstructionCreate(BaseModel):
    error_count: int | None = Field(default=None, title="Error Count")
    lease_attempt: int | None = Field(default=None, title="Lease Attempt")
    id: UUID | None = Field(default=None, title="Id")
    capture_session_id: UUID | None = Field(default=None, title="Capture Session Id")
    lease_heartbeat_at: AwareDatetime | None = Field(default=None, title="Lease Heartbeat At")


class ReconstructionBatchCreate(BaseModel):
    error_count: int | None = Field(default=None, title="Error Count")
    lease_attempt: int | None = Field(default=None, title="Lease Attempt")
    id: UUID = Field(..., title="Id")
    capture_session_id: UUID | None = Field(default=None, title="Capture Session Id")
    lease_heartbeat_at: AwareDatetime | None = Field(default=None, title="Lease Heartbeat At")


class ReconstructionUpdate(BaseModel):
    error_count: int | None = Field(default=None, title="Error Count")
    lease_attempt: int | None = Field(default=None, title="Lease Attempt")
    capture_session_id: UUID | None = Field(default=None, title="Capture Session Id")
    lease_heartbeat_at: AwareDatetime | None = Field(default=None, title="Lease Heartbeat At")


class ReconstructionBatchUpdate(BaseModel):
    error_count: int | None = Field(default=None, title="Error Count")
    lease_attempt: int | None = Field(default=None, title="Lease Attempt")
    id: UUID = Field(..., title="Id")
    capture_session_id: UUID | None = Field(default=None, title="Capture Session Id")
    lease_heartbeat_at: AwareDatetime | None = Field(default=None, title="Lease Heartbeat At")


class SpatialRefSyCreate(BaseModel):
    srid: int = Field(..., title="Srid")
    auth_name: str | None = Field(default=None, title="Auth Name")
    auth_srid: int | None = Field(default=None, title="Auth Srid")
    srtext: str | None = Field(default=None, title="Srtext")
    proj4text: str | None = Field(default=None, title="Proj4Text")


class SpatialRefSyBatchCreate(BaseModel):
    srid: int = Field(..., title="Srid")
    auth_name: str | None = Field(default=None, title="Auth Name")
    auth_srid: int | None = Field(default=None, title="Auth Srid")
    srtext: str | None = Field(default=None, title="Srtext")
    proj4text: str | None = Field(default=None, title="Proj4Text")


class SpatialRefSyUpdate(BaseModel):
    auth_name: str | None = Field(default=None, title="Auth Name")
    auth_srid: int | None = Field(default=None, title="Auth Srid")
    srtext: str | None = Field(default=None, title="Srtext")
    proj4text: str | None = Field(default=None, title="Proj4Text")


class SpatialRefSyBatchUpdate(BaseModel):
    srid: int = Field(..., title="Srid")
    auth_name: str | None = Field(default=None, title="Auth Name")
    auth_srid: int | None = Field(default=None, title="Auth Srid")
    srtext: str | None = Field(default=None, title="Srtext")
    proj4text: str | None = Field(default=None, title="Proj4Text")


class SpatialRefSyRead(BaseModel):
    srid: int = Field(..., title="Srid")
    auth_name: str | None = Field(default=None, title="Auth Name")
    auth_srid: int | None = Field(default=None, title="Auth Srid")
    srtext: str | None = Field(default=None, title="Srtext")
    proj4text: str | None = Field(default=None, title="Proj4Text")


class TenantCreate(BaseModel):
    id: UUID | None = Field(default=None, title="Id")


class TenantBatchCreate(BaseModel):
    id: UUID = Field(..., title="Id")


class TenantUpdate(BaseModel):
    pass


class TenantBatchUpdate(BaseModel):
    id: UUID = Field(..., title="Id")


class TenantRead(BaseModel):
    created_at: AwareDatetime = Field(..., title="Created At")
    id: UUID = Field(..., title="Id")


class CaptureSessionCreate(BaseModel):
    recorded_at: AwareDatetime | None = Field(default=None, title="Recorded At")
    name: str = Field(..., title="Name")
    device_type: DeviceType
    size_bytes: int | None = Field(default=None, title="Size Bytes")
    id: UUID | None = Field(default=None, title="Id")


class CaptureSessionBatchCreate(BaseModel):
    recorded_at: AwareDatetime | None = Field(default=None, title="Recorded At")
    name: str = Field(..., title="Name")
    device_type: DeviceType
    size_bytes: int | None = Field(default=None, title="Size Bytes")
    id: UUID = Field(..., title="Id")


class CaptureSessionUpdate(BaseModel):
    recorded_at: AwareDatetime | None = Field(default=None, title="Recorded At")
    name: str | None = Field(default=None, title="Name")
    device_type: DeviceType | None = None
    size_bytes: int | None = Field(default=None, title="Size Bytes")


class CaptureSessionBatchUpdate(BaseModel):
    recorded_at: AwareDatetime | None = Field(default=None, title="Recorded At")
    name: str | None = Field(default=None, title="Name")
    device_type: DeviceType | None = None
    size_bytes: int | None = Field(default=None, title="Size Bytes")
    id: UUID = Field(..., title="Id")


class CaptureSessionRead(BaseModel):
    created_at: AwareDatetime = Field(..., title="Created At")
    updated_at: AwareDatetime = Field(..., title="Updated At")
    recorded_at: AwareDatetime = Field(..., title="Recorded At")
    name: str = Field(..., title="Name")
    device_type: DeviceType
    size_bytes: int = Field(..., title="Size Bytes")
    id: UUID = Field(..., title="Id")


class NodeCreate(BaseModel):
    active: bool | None = Field(default=None, title="Active")
    position_x: float = Field(..., title="Position X")
    position_y: float = Field(..., title="Position Y")
    position_z: float = Field(..., title="Position Z")
    rotation_x: float = Field(..., title="Rotation X")
    rotation_y: float = Field(..., title="Rotation Y")
    rotation_z: float = Field(..., title="Rotation Z")
    rotation_w: float = Field(..., title="Rotation W")
    label_type: LabelType
    link_type: LinkType
    id: UUID | None = Field(default=None, title="Id")
    name: str | None = Field(default=None, title="Name")
    label: str | None = Field(default=None, title="Label")
    link: str | None = Field(default=None, title="Link")
    label_scale: float | None = Field(default=None, title="Label Scale")
    label_width: float | None = Field(default=None, title="Label Width")
    label_height: float | None = Field(default=None, title="Label Height")
    parent_id: UUID | None = Field(default=None, title="Parent Id")
    layer_id: UUID | None = Field(default=None, title="Layer Id")


class NodeBatchCreate(BaseModel):
    active: bool | None = Field(default=None, title="Active")
    position_x: float = Field(..., title="Position X")
    position_y: float = Field(..., title="Position Y")
    position_z: float = Field(..., title="Position Z")
    rotation_x: float = Field(..., title="Rotation X")
    rotation_y: float = Field(..., title="Rotation Y")
    rotation_z: float = Field(..., title="Rotation Z")
    rotation_w: float = Field(..., title="Rotation W")
    label_type: LabelType
    link_type: LinkType
    id: UUID = Field(..., title="Id")
    name: str | None = Field(default=None, title="Name")
    label: str | None = Field(default=None, title="Label")
    link: str | None = Field(default=None, title="Link")
    label_scale: float | None = Field(default=None, title="Label Scale")
    label_width: float | None = Field(default=None, title="Label Width")
    label_height: float | None = Field(default=None, title="Label Height")
    parent_id: UUID | None = Field(default=None, title="Parent Id")
    layer_id: UUID | None = Field(default=None, title="Layer Id")


class NodeUpdate(BaseModel):
    active: bool | None = Field(default=None, title="Active")
    position_x: float | None = Field(default=None, title="Position X")
    position_y: float | None = Field(default=None, title="Position Y")
    position_z: float | None = Field(default=None, title="Position Z")
    rotation_x: float | None = Field(default=None, title="Rotation X")
    rotation_y: float | None = Field(default=None, title="Rotation Y")
    rotation_z: float | None = Field(default=None, title="Rotation Z")
    rotation_w: float | None = Field(default=None, title="Rotation W")
    label_type: LabelType | None = None
    link_type: LinkType | None = None
    name: str | None = Field(default=None, title="Name")
    label: str | None = Field(default=None, title="Label")
    link: str | None = Field(default=None, title="Link")
    label_scale: float | None = Field(default=None, title="Label Scale")
    label_width: float | None = Field(default=None, title="Label Width")
    label_height: float | None = Field(default=None, title="Label Height")
    parent_id: UUID | None = Field(default=None, title="Parent Id")
    layer_id: UUID | None = Field(default=None, title="Layer Id")


class NodeBatchUpdate(BaseModel):
    active: bool | None = Field(default=None, title="Active")
    position_x: float | None = Field(default=None, title="Position X")
    position_y: float | None = Field(default=None, title="Position Y")
    position_z: float | None = Field(default=None, title="Position Z")
    rotation_x: float | None = Field(default=None, title="Rotation X")
    rotation_y: float | None = Field(default=None, title="Rotation Y")
    rotation_z: float | None = Field(default=None, title="Rotation Z")
    rotation_w: float | None = Field(default=None, title="Rotation W")
    label_type: LabelType | None = None
    link_type: LinkType | None = None
    id: UUID = Field(..., title="Id")
    name: str | None = Field(default=None, title="Name")
    label: str | None = Field(default=None, title="Label")
    link: str | None = Field(default=None, title="Link")
    label_scale: float | None = Field(default=None, title="Label Scale")
    label_width: float | None = Field(default=None, title="Label Width")
    label_height: float | None = Field(default=None, title="Label Height")
    parent_id: UUID | None = Field(default=None, title="Parent Id")
    layer_id: UUID | None = Field(default=None, title="Layer Id")


class NodeRead(BaseModel):
    created_at: AwareDatetime = Field(..., title="Created At")
    updated_at: AwareDatetime = Field(..., title="Updated At")
    active: bool = Field(..., title="Active")
    position_x: float = Field(..., title="Position X")
    position_y: float = Field(..., title="Position Y")
    position_z: float = Field(..., title="Position Z")
    rotation_x: float = Field(..., title="Rotation X")
    rotation_y: float = Field(..., title="Rotation Y")
    rotation_z: float = Field(..., title="Rotation Z")
    rotation_w: float = Field(..., title="Rotation W")
    label_type: LabelType
    link_type: LinkType
    id: UUID = Field(..., title="Id")
    name: str | None = Field(default=None, title="Name")
    label: str | None = Field(default=None, title="Label")
    link: str | None = Field(default=None, title="Link")
    label_scale: float | None = Field(default=None, title="Label Scale")
    label_width: float | None = Field(default=None, title="Label Width")
    label_height: float | None = Field(default=None, title="Label Height")
    parent_id: UUID | None = Field(default=None, title="Parent Id")
    layer_id: UUID | None = Field(default=None, title="Layer Id")


class ReconstructionRead(BaseModel):
    created_at: AwareDatetime = Field(..., title="Created At")
    updated_at: AwareDatetime = Field(..., title="Updated At")
    status: ReconstructionStatus
    error_count: int = Field(..., title="Error Count")
    lease_attempt: int = Field(..., title="Lease Attempt")
    manifest: dict[str, Any] = Field(..., title="Manifest")
    manifest_version: int = Field(..., title="Manifest Version")
    id: UUID = Field(..., title="Id")
    capture_session_id: UUID | None = Field(default=None, title="Capture Session Id")
    error: str | None = Field(default=None, title="Error")
    progress_current: int | None = Field(default=None, title="Progress Current")
    progress_total: int | None = Field(default=None, title="Progress Total")
    progress_attempt: int | None = Field(default=None, title="Progress Attempt")
    lease_heartbeat_at: AwareDatetime | None = Field(default=None, title="Lease Heartbeat At")


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
