import datetime
import uuid

from sqlalchemy import DateTime, Enum, ForeignKeyConstraint, PrimaryKeyConstraint, Text, Uuid, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass


class Tenant(Base):
    __tablename__ = 'tenants'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='tenants_pkey'),
        {'schema': 'auth'}
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text('gen_random_uuid()'))
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'))

    captures: Mapped[list['Capture']] = relationship('Capture', back_populates='tenant')
    reconstructions: Mapped[list['Reconstruction']] = relationship('Reconstruction', back_populates='tenant')


class Capture(Base):
    __tablename__ = 'captures'
    __table_args__ = (
        ForeignKeyConstraint(['tenant_id'], ['auth.tenants.id'], ondelete='RESTRICT', name='captures_tenant_id_fkey'),
        PrimaryKeyConstraint('id', name='captures_pkey'),
        {'schema': 'public'}
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, server_default=text('current_tenant()'))
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text('uuid_generate_v4()'))
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'))
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'))
    device_type: Mapped[str] = mapped_column(Enum('ARFoundation', 'Zed', name='device_type'), nullable=False)
    filename: Mapped[str] = mapped_column(Text, nullable=False)

    tenant: Mapped['Tenant'] = relationship('Tenant', back_populates='captures')
    reconstructions: Mapped[list['Reconstruction']] = relationship('Reconstruction', back_populates='capture')


class Reconstruction(Base):
    __tablename__ = 'reconstructions'
    __table_args__ = (
        ForeignKeyConstraint(['capture_id'], ['public.captures.id'], ondelete='RESTRICT', name='reconstructions_capture_id_fkey'),
        ForeignKeyConstraint(['tenant_id'], ['auth.tenants.id'], ondelete='RESTRICT', name='reconstructions_tenant_id_fkey'),
        PrimaryKeyConstraint('id', name='reconstructions_pkey'),
        {'schema': 'public'}
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, server_default=text('current_tenant()'))
    capture_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text('uuid_generate_v4()'))
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'))
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'))
    status: Mapped[str] = mapped_column(Enum('queued', 'running', 'succeeded', 'cancelled', 'failed', name='reconstruction_status'), nullable=False, server_default=text("'queued'::reconstruction_status"))

    capture: Mapped['Capture'] = relationship('Capture', back_populates='reconstructions')
    tenant: Mapped['Tenant'] = relationship('Tenant', back_populates='reconstructions')
