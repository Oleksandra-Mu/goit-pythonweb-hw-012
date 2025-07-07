from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class UserModelRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    avatar: str


class UserModel(BaseModel):
    email: EmailStr
    password: str


class ResponseUser(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    avatar: Optional[str] = None

    class Config:
        from_attributes = True


class TokenModel(BaseModel):
    access_token: str
    token_type: str = "bearer"
