"""账号注册、登录和个人资料的数据结构。"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class RegisterRequest(BaseModel):
    username: str = Field(min_length=2, max_length=50, examples=["林屿"])
    email: str = Field(min_length=5, max_length=120, examples=["hello@lvye.cn"])
    password: str = Field(min_length=6, max_length=128)


class LoginRequest(BaseModel):
    account: str = Field(description="用户名或邮箱")
    password: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str
    avatar_url: str | None
    bio: str
    created_at: datetime


class UserUpdate(BaseModel):
    username: str | None = Field(default=None, min_length=2, max_length=50)
    bio: str | None = Field(default=None, max_length=200)
    avatar_url: str | None = Field(default=None, max_length=500)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

