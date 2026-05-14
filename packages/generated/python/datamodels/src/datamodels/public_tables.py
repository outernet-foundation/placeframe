import datetime
import enum
import uuid
from typing import Any, Optional

from sqlalchemy import (
    ARRAY,
    BigInteger,
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Double,
    Enum,
    ForeignKeyConstraint,
    Index,
    Integer,
    PrimaryKeyConstraint,
    SmallInteger,
    String,
    Table,
    Text,
    UniqueConstraint,
    Uuid,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def enum_values(x: list[enum.Enum]) -> list[str]:
    return [str(e.value) for e in x]


class DeviceType(enum.Enum):
    ARFOUNDATION = "ARFoundation"
    ZED = "Zed"


class LinkType(enum.Enum):
    NONE = "none"
    ADDRESS = "address"
    ANNOTATION = "annotation"
    IMAGE_LIST = "image_list"


class LabelType(enum.Enum):
    AUTOMATIC = "automatic"
    TEXT = "text"
    IMAGE = "image"


class ReconstructionStatus(enum.Enum):
    QUEUED = "queued"
    EXTRACTING_FEATURES = "extracting_features"
    MATCHING_FEATURES = "matching_features"
    TRAINING_OPQ_MATRIX = "training_opq_matrix"
    TRAINING_PRODUCT_QUANTIZER = "training_product_quantizer"
    VERIFYING_GEOMETRY = "verifying_geometry"
    RECONSTRUCTING = "reconstructing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Base(DeclarativeBase):
    pass


class Tenant(Base):
    __tablename__ = "tenants"
    __table_args__ = (PrimaryKeyConstraint("id", name="tenants_pkey"), {"schema": "auth"})

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text("gen_random_uuid()"))
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text("now()"))

    capture_sessions: Mapped[list["CaptureSession"]] = relationship("CaptureSession", back_populates="tenant")
    groups: Mapped[list["Group"]] = relationship("Group", back_populates="tenant")
    layers: Mapped[list["Layer"]] = relationship("Layer", back_populates="tenant")
    localization_sessions: Mapped[list["LocalizationSession"]] = relationship(
        "LocalizationSession", back_populates="tenant"
    )
    nodes: Mapped[list["Node"]] = relationship("Node", back_populates="tenant")
    reconstructions: Mapped[list["Reconstruction"]] = relationship("Reconstruction", back_populates="tenant")
    localization_evaluations: Mapped[list["LocalizationEvaluation"]] = relationship(
        "LocalizationEvaluation", back_populates="tenant"
    )
    localization_maps: Mapped[list["LocalizationMap"]] = relationship("LocalizationMap", back_populates="tenant")
    localization_map_camera_positions: Mapped[list["LocalizationMapCameraPosition"]] = relationship(
        "LocalizationMapCameraPosition", back_populates="tenant"
    )


t_geography_columns = Table(
    "geography_columns",
    Base.metadata,
    Column("f_table_catalog", String),
    Column("f_table_schema", String),
    Column("f_table_name", String),
    Column("f_geography_column", String),
    Column("coord_dimension", Integer),
    Column("srid", Integer),
    Column("type", Text),
    schema="public",
)


t_geometry_columns = Table(
    "geometry_columns",
    Base.metadata,
    Column("f_table_catalog", String(256, "C")),
    Column("f_table_schema", String),
    Column("f_table_name", String),
    Column("f_geometry_column", String),
    Column("coord_dimension", Integer),
    Column("srid", Integer),
    Column("type", String(30)),
    schema="public",
)


class SpatialRefSy(Base):
    __tablename__ = "spatial_ref_sys"
    __table_args__ = (
        CheckConstraint("srid > 0 AND srid <= 998999", name="spatial_ref_sys_srid_check"),
        PrimaryKeyConstraint("srid", name="spatial_ref_sys_pkey"),
        {"schema": "public"},
    )

    srid: Mapped[int] = mapped_column(Integer, primary_key=True)
    auth_name: Mapped[Optional[str]] = mapped_column(String(256))
    auth_srid: Mapped[Optional[int]] = mapped_column(Integer)
    srtext: Mapped[Optional[str]] = mapped_column(String(2048))
    proj4text: Mapped[Optional[str]] = mapped_column(String(2048))


class CaptureSession(Base):
    __tablename__ = "capture_sessions"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id"], ["auth.tenants.id"], ondelete="RESTRICT", name="capture_sessions_tenant_id_fkey"
        ),
        PrimaryKeyConstraint("id", name="capture_sessions_pkey"),
        {"schema": "public"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, server_default=text("current_tenant()"))
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text("uuid_generate_v4()"))
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text("now()"))
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text("now()"))
    recorded_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text("now()"))
    device_type: Mapped[DeviceType] = mapped_column(
        Enum(DeviceType, name="device_type", values_callable=enum_values), nullable=False
    )
    name: Mapped[Optional[str]] = mapped_column(Text)

    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="capture_sessions")
    reconstructions: Mapped[list["Reconstruction"]] = relationship("Reconstruction", back_populates="capture_session")


class Group(Base):
    __tablename__ = "groups"
    __table_args__ = (
        ForeignKeyConstraint(["parent_id"], ["public.groups.id"], ondelete="RESTRICT", name="groups_parent_id_fkey"),
        ForeignKeyConstraint(["tenant_id"], ["auth.tenants.id"], ondelete="RESTRICT", name="groups_tenant_id_fkey"),
        PrimaryKeyConstraint("id", name="groups_pkey"),
        {"schema": "public"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, server_default=text("current_tenant()"))
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text("gen_random_uuid()"))
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text("now()"))
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text("now()"))
    name: Mapped[str] = mapped_column(Text, nullable=False)
    parent_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid)

    parent: Mapped[Optional["Group"]] = relationship("Group", remote_side=[id], back_populates="parent_reverse")
    parent_reverse: Mapped[list["Group"]] = relationship("Group", remote_side=[parent_id], back_populates="parent")
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="groups")
    nodes: Mapped[list["Node"]] = relationship("Node", back_populates="parent")


class Layer(Base):
    __tablename__ = "layers"
    __table_args__ = (
        ForeignKeyConstraint(["tenant_id"], ["auth.tenants.id"], ondelete="RESTRICT", name="layers_tenant_id_fkey"),
        PrimaryKeyConstraint("id", name="layers_pkey"),
        {"schema": "public"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, server_default=text("current_tenant()"))
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text("gen_random_uuid()"))
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text("now()"))
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text("now()"))
    name: Mapped[str] = mapped_column(Text, nullable=False)

    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="layers")
    nodes: Mapped[list["Node"]] = relationship("Node", back_populates="layer")


class LocalizationSession(Base):
    __tablename__ = "localization_sessions"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id"], ["auth.tenants.id"], ondelete="RESTRICT", name="localization_sessions_tenant_id_fkey"
        ),
        PrimaryKeyConstraint("id", name="localization_sessions_pkey"),
        {"schema": "public"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, server_default=text("current_tenant()"))
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text("gen_random_uuid()"))
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text("now()"))
    container_id: Mapped[str] = mapped_column(Text, nullable=False)
    container_url: Mapped[str] = mapped_column(Text, nullable=False)

    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="localization_sessions")


class Node(Base):
    __tablename__ = "nodes"
    __table_args__ = (
        ForeignKeyConstraint(["layer_id"], ["public.layers.id"], ondelete="RESTRICT", name="nodes_layer_id_fkey"),
        ForeignKeyConstraint(["parent_id"], ["public.groups.id"], ondelete="RESTRICT", name="nodes_parent_id_fkey"),
        ForeignKeyConstraint(["tenant_id"], ["auth.tenants.id"], ondelete="RESTRICT", name="nodes_tenant_id_fkey"),
        PrimaryKeyConstraint("id", name="nodes_pkey"),
        Index("idx_nodes_position_gist"),
        {"schema": "public"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, server_default=text("current_tenant()"))
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text("gen_random_uuid()"))
    rotation_z: Mapped[float] = mapped_column(Double(53), nullable=False)
    position_y: Mapped[float] = mapped_column(Double(53), nullable=False)
    position_z: Mapped[float] = mapped_column(Double(53), nullable=False)
    rotation_x: Mapped[float] = mapped_column(Double(53), nullable=False)
    rotation_y: Mapped[float] = mapped_column(Double(53), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text("now()"))
    rotation_w: Mapped[float] = mapped_column(Double(53), nullable=False)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text("now()"))
    position_x: Mapped[float] = mapped_column(Double(53), nullable=False)
    link_type: Mapped[LinkType] = mapped_column(
        Enum(LinkType, name="link_type", values_callable=enum_values), nullable=False
    )
    label_type: Mapped[LabelType] = mapped_column(
        Enum(LabelType, name="label_type", values_callable=enum_values), nullable=False
    )
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    layer_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid)
    parent_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid)
    label_width: Mapped[Optional[float]] = mapped_column(Double(53))
    label_height: Mapped[Optional[float]] = mapped_column(Double(53))
    label_scale: Mapped[Optional[float]] = mapped_column(Double(53))
    link: Mapped[Optional[str]] = mapped_column(Text)
    label: Mapped[Optional[str]] = mapped_column(Text)
    name: Mapped[Optional[str]] = mapped_column(Text)

    layer: Mapped[Optional["Layer"]] = relationship("Layer", back_populates="nodes")
    parent: Mapped[Optional["Group"]] = relationship("Group", back_populates="nodes")
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="nodes")


class Reconstruction(Base):
    __tablename__ = "reconstructions"
    __table_args__ = (
        ForeignKeyConstraint(
            ["capture_session_id"],
            ["public.capture_sessions.id"],
            ondelete="RESTRICT",
            name="reconstructions_capture_session_id_fkey",
        ),
        ForeignKeyConstraint(
            ["tenant_id"], ["auth.tenants.id"], ondelete="RESTRICT", name="reconstructions_tenant_id_fkey"
        ),
        PrimaryKeyConstraint("id", name="reconstructions_pkey"),
        {"schema": "public"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, server_default=text("current_tenant()"))
    capture_session_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text("uuid_generate_v4()"))
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text("now()"))
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text("now()"))
    status: Mapped[ReconstructionStatus] = mapped_column(
        Enum(ReconstructionStatus, name="reconstruction_status", values_callable=enum_values),
        nullable=False,
        server_default=text("'queued'::reconstruction_status"),
    )
    manifest_version: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    manifest: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    progress_current: Mapped[Optional[int]] = mapped_column(Integer)
    progress_total: Mapped[Optional[int]] = mapped_column(Integer)
    progress_attempt: Mapped[Optional[int]] = mapped_column(Integer)
    error: Mapped[Optional[str]] = mapped_column(Text)

    capture_session: Mapped["CaptureSession"] = relationship("CaptureSession", back_populates="reconstructions")
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="reconstructions")
    localization_evaluations: Mapped[list["LocalizationEvaluation"]] = relationship(
        "LocalizationEvaluation", back_populates="reconstruction"
    )
    localization_map: Mapped["LocalizationMap"] = relationship(
        "LocalizationMap", uselist=False, back_populates="reconstruction"
    )


class LocalizationEvaluation(Base):
    __tablename__ = "localization_evaluations"
    __table_args__ = (
        CheckConstraint(
            "pnp_covariance IS NULL OR array_length(pnp_covariance, 1) = 6 AND array_length(pnp_covariance, 2) = 6",
            name="pnp_covariance_shape",
        ),
        CheckConstraint("se3_residual IS NULL OR array_length(se3_residual, 1) = 6", name="se3_residual_length"),
        CheckConstraint(
            "succeeded = (err_t_m IS NOT NULL) AND succeeded = (err_r_deg IS NOT NULL) AND succeeded = (se3_residual IS NOT NULL) AND succeeded = (pnp_covariance IS NOT NULL)",
            name="labels_present_iff_succeeded",
        ),
        ForeignKeyConstraint(
            ["reconstruction_id"],
            ["public.reconstructions.id"],
            ondelete="RESTRICT",
            name="localization_evaluations_reconstruction_id_fkey",
        ),
        ForeignKeyConstraint(
            ["tenant_id"], ["auth.tenants.id"], ondelete="RESTRICT", name="localization_evaluations_tenant_id_fkey"
        ),
        PrimaryKeyConstraint("id", name="localization_evaluations_pkey"),
        UniqueConstraint(
            "reconstruction_id",
            "frame_timestamp",
            "retrieval_top_k",
            "ransac_threshold",
            "pipeline_version",
            name="localization_evaluations_cache_key",
        ),
        {"schema": "public"},
    )

    reconstruction_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text("uuid_generate_v4()"))
    tenant_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, server_default=text("current_tenant()"))
    ransac_threshold: Mapped[float] = mapped_column(Double(53), nullable=False)
    frame_timestamp: Mapped[int] = mapped_column(BigInteger, nullable=False)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text("now()"))
    inlier_coverage: Mapped[float] = mapped_column(Double(53), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text("now()"))
    query_image_diagonal_px: Mapped[float] = mapped_column(Double(53), nullable=False)
    reproj_error_median: Mapped[float] = mapped_column(Double(53), nullable=False)
    inlier_ratio: Mapped[float] = mapped_column(Double(53), nullable=False)
    retrieval_top_k: Mapped[int] = mapped_column(Integer, nullable=False)
    num_inliers: Mapped[int] = mapped_column(Integer, nullable=False)
    num_matches: Mapped[int] = mapped_column(Integer, nullable=False)
    num_correspondences: Mapped[int] = mapped_column(Integer, nullable=False)
    succeeded: Mapped[bool] = mapped_column(Boolean, nullable=False)
    pipeline_version: Mapped[str] = mapped_column(Text, nullable=False)
    err_r_deg: Mapped[Optional[float]] = mapped_column(Double(53))
    err_t_m: Mapped[Optional[float]] = mapped_column(Double(53))
    pnp_covariance: Mapped[Optional[list[float]]] = mapped_column(ARRAY[float](Double(53)))
    se3_residual: Mapped[Optional[list[float]]] = mapped_column(ARRAY[float](Double(53)))

    reconstruction: Mapped["Reconstruction"] = relationship("Reconstruction", back_populates="localization_evaluations")
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="localization_evaluations")


class LocalizationMap(Base):
    __tablename__ = "localization_maps"
    __table_args__ = (
        ForeignKeyConstraint(
            ["reconstruction_id"],
            ["public.reconstructions.id"],
            ondelete="RESTRICT",
            name="localization_maps_reconstruction_id_fkey",
        ),
        ForeignKeyConstraint(
            ["tenant_id"], ["auth.tenants.id"], ondelete="RESTRICT", name="localization_maps_tenant_id_fkey"
        ),
        PrimaryKeyConstraint("id", name="localization_maps_pkey"),
        UniqueConstraint("reconstruction_id", name="localization_maps_reconstruction_id_key"),
        Index("idx_localization_maps_position_gist"),
        {"schema": "public"},
    )

    reconstruction_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text("gen_random_uuid()"))
    tenant_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, server_default=text("current_tenant()"))
    rotation_y: Mapped[float] = mapped_column(Double(53), nullable=False)
    position_x: Mapped[float] = mapped_column(Double(53), nullable=False)
    position_y: Mapped[float] = mapped_column(Double(53), nullable=False)
    position_z: Mapped[float] = mapped_column(Double(53), nullable=False)
    rotation_x: Mapped[float] = mapped_column(Double(53), nullable=False)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text("now()"))
    rotation_z: Mapped[float] = mapped_column(Double(53), nullable=False)
    rotation_w: Mapped[float] = mapped_column(Double(53), nullable=False)
    color: Mapped[int] = mapped_column(BigInteger, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text("now()"))
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    lighting: Mapped[Optional[int]] = mapped_column(Integer)
    name: Mapped[Optional[str]] = mapped_column(Text)

    reconstruction: Mapped["Reconstruction"] = relationship("Reconstruction", back_populates="localization_map")
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="localization_maps")
    localization_map_camera_positions: Mapped[list["LocalizationMapCameraPosition"]] = relationship(
        "LocalizationMapCameraPosition", back_populates="localization_map", passive_deletes=True
    )


class LocalizationMapCameraPosition(Base):
    __tablename__ = "localization_map_camera_positions"
    __table_args__ = (
        ForeignKeyConstraint(
            ["localization_map_id"],
            ["public.localization_maps.id"],
            ondelete="CASCADE",
            name="localization_map_camera_positions_localization_map_id_fkey",
        ),
        ForeignKeyConstraint(
            ["tenant_id"],
            ["auth.tenants.id"],
            ondelete="RESTRICT",
            name="localization_map_camera_positions_tenant_id_fkey",
        ),
        PrimaryKeyConstraint("id", name="localization_map_camera_positions_pkey"),
        Index("idx_lm_camera_positions_gist"),
        Index("idx_lm_camera_positions_map_id", "localization_map_id"),
        {"schema": "public"},
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, server_default=text("current_tenant()"))
    localization_map_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text("gen_random_uuid()"))
    position_x: Mapped[float] = mapped_column(Double(53), nullable=False)
    position_y: Mapped[float] = mapped_column(Double(53), nullable=False)
    position_z: Mapped[float] = mapped_column(Double(53), nullable=False)

    localization_map: Mapped["LocalizationMap"] = relationship(
        "LocalizationMap", back_populates="localization_map_camera_positions"
    )
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="localization_map_camera_positions")
