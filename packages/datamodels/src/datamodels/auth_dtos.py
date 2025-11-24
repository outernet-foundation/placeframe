from __future__ import annotations

from enum import Enum
from pydantic import AwareDatetime, BaseModel, Field
from typing import Optional
from uuid import UUID

from sqlalchemy import inspect as sa_inspect

from .auth_tables import Membership, Tenant, User



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


class UserCreate(BaseModel):
    id: UUID = Field(..., title='Id')


class UserUpdate(BaseModel):
    pass


class UserBatchUpdate(BaseModel):
    id: UUID = Field(..., title='Id')


class UserRead(BaseModel):
    id: UUID = Field(..., title='Id')
    created_at: AwareDatetime = Field(..., title='Created At')


class MembershipRole(Enum):
    owner = 'owner'
    admin = 'admin'
    member = 'member'


class MembershipCreate(BaseModel):
    user_id: UUID = Field(..., title='User Id')
    role: Optional[MembershipRole] = None
    is_personal: Optional[bool] = Field(None, title='Is Personal')


class MembershipUpdate(BaseModel):
    role: Optional[MembershipRole] = None
    is_personal: Optional[bool] = Field(None, title='Is Personal')


class MembershipBatchUpdate(BaseModel):
    user_id: UUID = Field(..., title='User Id')
    role: Optional[MembershipRole] = None
    is_personal: Optional[bool] = Field(None, title='Is Personal')


class MembershipRead(BaseModel):
    user_id: UUID = Field(..., title='User Id')
    created_at: AwareDatetime = Field(..., title='Created At')
    updated_at: AwareDatetime = Field(..., title='Updated At')
    role: MembershipRole
    is_personal: bool = Field(..., title='Is Personal')

def membership_from_dto(create: MembershipCreate) -> Membership:
    data = create.model_dump(exclude_unset=True, mode="json")
    return Membership(**data)

def membership_from_dto_overwrite(instance: Membership, create: MembershipCreate) -> Membership:
    for field, value in create.model_dump(exclude_unset=True, mode="json").items():
        setattr(instance, field, value)
    return instance

def membership_to_dto(instance: Membership) -> MembershipRead:
    column_keys = tuple(attr.key for attr in sa_inspect(Membership).mapper.column_attrs)
    data = {k: getattr(instance, k) for k in column_keys}
    return MembershipRead.model_validate(data)

def membership_apply_dto(instance: Membership, update: MembershipUpdate) -> Membership:
    for field, value in update.model_dump(exclude_unset=True, mode="json").items():
        setattr(instance, field, value)
    return instance

def membership_apply_batch_update_dto(instance: Membership, update: MembershipBatchUpdate) -> Membership:
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

def user_from_dto(create: UserCreate) -> User:
    data = create.model_dump(exclude_unset=True, mode="json")
    return User(**data)

def user_from_dto_overwrite(instance: User, create: UserCreate) -> User:
    for field, value in create.model_dump(exclude_unset=True, mode="json").items():
        setattr(instance, field, value)
    return instance

def user_to_dto(instance: User) -> UserRead:
    column_keys = tuple(attr.key for attr in sa_inspect(User).mapper.column_attrs)
    data = {k: getattr(instance, k) for k in column_keys}
    return UserRead.model_validate(data)

def user_apply_dto(instance: User, update: UserUpdate) -> User:
    for field, value in update.model_dump(exclude_unset=True, mode="json").items():
        setattr(instance, field, value)
    return instance

def user_apply_batch_update_dto(instance: User, update: UserBatchUpdate) -> User:
    for field, value in update.model_dump(exclude_unset=True, mode="json").items():
        setattr(instance, field, value)
    return instance
