import datetime
import enum
import uuid

from sqlalchemy import Boolean, DateTime, Enum, ForeignKeyConstraint, Index, PrimaryKeyConstraint, Uuid, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def enum_values(x: list[enum.Enum]) -> list[str]:
    return [str(e.value) for e in x]


class MembershipRole(enum.Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"


class Base(DeclarativeBase):
    pass


class Tenant(Base):
    __tablename__ = "tenants"
    __table_args__ = (PrimaryKeyConstraint("id", name="tenants_pkey"), {"schema": "auth"})

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text("gen_random_uuid()"))
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text("now()"))

    memberships: Mapped[list["Membership"]] = relationship("Membership", back_populates="tenant")


class User(Base):
    __tablename__ = "users"
    __table_args__ = (PrimaryKeyConstraint("id", name="users_pkey"), {"schema": "auth"})

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text("now()"))

    memberships: Mapped[list["Membership"]] = relationship("Membership", back_populates="user")


class Membership(Base):
    __tablename__ = "memberships"
    __table_args__ = (
        ForeignKeyConstraint(["tenant_id"], ["auth.tenants.id"], ondelete="CASCADE", name="memberships_tenant_id_fkey"),
        ForeignKeyConstraint(["user_id"], ["auth.users.id"], ondelete="CASCADE", name="memberships_user_id_fkey"),
        PrimaryKeyConstraint("user_id", "tenant_id", name="memberships_pkey"),
        Index("user_personal_tenant", "user_id", unique=True),
        {"schema": "auth"},
    )

    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text("now()"))
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text("now()"))
    role: Mapped[MembershipRole] = mapped_column(
        Enum(MembershipRole, name="membership_role", values_callable=enum_values),
        nullable=False,
        server_default=text("'member'::membership_role"),
    )
    is_personal: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))

    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="memberships")
    user: Mapped["User"] = relationship("User", back_populates="memberships")
