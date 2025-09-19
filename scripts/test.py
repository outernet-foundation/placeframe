from typing import Optional
import uuid

from sqlalchemy import Enum, ForeignKeyConstraint, PrimaryKeyConstraint, Uuid, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass


class Users(Base):
    __tablename__ = 'users'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='users_pkey'),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)

    tenants: Mapped[list['Tenants']] = relationship('Tenants', back_populates='owner_user')
    memberships: Mapped[list['Memberships']] = relationship('Memberships', back_populates='user')


class Tenants(Base):
    __tablename__ = 'tenants'
    __table_args__ = (
        ForeignKeyConstraint(['owner_user_id'], ['users.id'], ondelete='RESTRICT', name='tenants_owner_user_id_fkey'),
        PrimaryKeyConstraint('id', name='tenants_pkey')
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    kind: Mapped[str] = mapped_column(Enum('individual', 'organization', name='tenant_kind'), nullable=False)
    owner_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid)

    owner_user: Mapped[Optional['Users']] = relationship('Users', back_populates='tenants')
    captures: Mapped[list['Captures']] = relationship('Captures', back_populates='tenant')
    memberships: Mapped[list['Memberships']] = relationship('Memberships', back_populates='tenant')


class Captures(Base):
    __tablename__ = 'captures'
    __table_args__ = (
        ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='RESTRICT', name='captures_tenant_id_fkey'),
        PrimaryKeyConstraint('id', name='captures_pkey')
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text('uuid_generate_v4()'))
    tenant_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)

    tenant: Mapped['Tenants'] = relationship('Tenants', back_populates='captures')


class Memberships(Base):
    __tablename__ = 'memberships'
    __table_args__ = (
        ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='RESTRICT', name='memberships_tenant_id_fkey'),
        ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='RESTRICT', name='memberships_user_id_fkey'),
        PrimaryKeyConstraint('id', name='memberships_pkey')
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid)
    tenant_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid)

    tenant: Mapped[Optional['Tenants']] = relationship('Tenants', back_populates='memberships')
    user: Mapped[Optional['Users']] = relationship('Users', back_populates='memberships')
