from pydantic import BaseModel, EmailStr

from app.schemas.users import UserResponse


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class GoogleLoginRequest(BaseModel):
    credential: str  # Google ID token from Google Identity Services
