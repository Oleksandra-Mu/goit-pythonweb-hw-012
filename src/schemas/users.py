from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from enum import Enum


class RoleEnum(str, Enum):
    admin = "admin"
    user = "user"


class UserModelRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    roles: RoleEnum


class UserModel(BaseModel):
    email: EmailStr
    password: str


class ResponseUser(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    avatar: Optional[str] = None

    model_config = ConfigDict(
        from_attributes=True,
    )


class TokenModel(BaseModel):
    access_token: str
    token_type: str = "bearer"


class RequestEmail(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordConfirm(BaseModel):
    token: str
    new_password: str = Field(min_length=8)
