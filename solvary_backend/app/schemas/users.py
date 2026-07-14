from typing import Literal

from pydantic import BaseModel, EmailStr


class UserResponse(BaseModel):
    id: str
    name: str
    email: EmailStr
    avatar_url: str
    role: Literal["user", "admin"]


class UserUpdate(BaseModel):
    name: str | None = None
    avatar_url: str | None = None
