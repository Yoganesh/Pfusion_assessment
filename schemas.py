from pydantic import BaseModel


class UserCreate(BaseModel):
    email: str
    password: str
    organization_name: str


class MemberCreate(BaseModel):
    email: str


class ResetPassword(BaseModel):
    email: str
    password: str
