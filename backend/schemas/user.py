from pydantic import BaseModel
from typing import Optional

# what frontend SENDS
class UserLogin(BaseModel):
    username: str
    password: str


class UserCreate(BaseModel):
    username: str
    password: str
    role_id: str
    name: str


class UserUpdate(BaseModel):
    username: Optional[str] = None
    name: Optional[str] = None
    role_id: Optional[str] = None
    password: Optional[str] = None


# what frontend RECEIVES
class UserPublic(BaseModel):
    id: str
    username: str
    name: str
    role: str              # ← from roles.name (JOIN)
    createdAt: str
    lastLogin: Optional[str]
