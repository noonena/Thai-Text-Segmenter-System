from pydantic import BaseModel
from typing import Optional

class RoleCreate(BaseModel):
    name: str
    description: Optional[str] = None


class RoleUpdate(BaseModel):
    name: str
    description: Optional[str] = None
