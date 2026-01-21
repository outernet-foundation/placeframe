import datetime
import enum
import uuid
from typing import Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Double,
    Enum,
    ForeignKeyConstraint,
    Integer,
    PrimaryKeyConstraint,
    Text,
    UniqueConstraint,
    Uuid,
    text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def enum_values(x: list[enum.Enum]) -> list[str]:
    return [str(e.value) for e in x]


class DeviceType(enum.Enum):
    ARFOUNDATION = "ARFoundation"
    ZED = "Zed"


class OrchestrationStatus(enum.Enum):
    QUEUED = "queued"
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    CANCELLED = "cancelled"
    FAILED = "failed"


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
    localization_maps: Mapped[list["LocalizationMap"]] = relationship("LocalizationMap", back_populates="tenant")


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
    device_type: Mapped[DeviceType] = mapped_column(
        Enum(DeviceType, name="device_type", values_callable=enum_values), nullable=False
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)

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
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    name: Mapped[str] = mapped_column(Text, nullable=False)
    layer_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid)
    parent_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid)
    label_width: Mapped[Optional[float]] = mapped_column(Double(53))
    label_height: Mapped[Optional[float]] = mapped_column(Double(53))
    label_scale: Mapped[Optional[float]] = mapped_column(Double(53))
    link_type: Mapped[Optional[int]] = mapped_column(Integer)
    label_type: Mapped[Optional[int]] = mapped_column(Integer)
    link: Mapped[Optional[str]] = mapped_column(Text)
    label: Mapped[Optional[str]] = mapped_column(Text)

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
    orchestration_status: Mapped[OrchestrationStatus] = mapped_column(
        Enum(OrchestrationStatus, name="orchestration_status", values_callable=enum_values),
        nullable=False,
        server_default=text("'queued'::orchestration_status"),
    )

    capture_session: Mapped["CaptureSession"] = relationship("CaptureSession", back_populates="reconstructions")
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="reconstructions")
    localization_map: Mapped["LocalizationMap"] = relationship(
        "LocalizationMap", uselist=False, back_populates="reconstruction"
    )


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
