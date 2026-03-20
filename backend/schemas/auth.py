from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserInfo"


class UserInfo(BaseModel):
    id: int
    username: str
    display_name: str
    role: str

    model_config = {"from_attributes": True}


class LogoutRequest(BaseModel):
    token: str


class UserCreateSchema(BaseModel):
    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=8)
    display_name: str = Field(..., min_length=1, max_length=100)
    role: str = Field(..., pattern="^(admin|staff|viewer)$")
    department: str | None = Field(None, max_length=100)
