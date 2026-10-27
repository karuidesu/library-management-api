from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class RoleBase(BaseModel):
    label: str = Field(
        ...,
        min_length=2,
        max_length=50,
        description="Role label (Administrator, Librarian, Member)",
    )


class RoleCreate(RoleBase):
    pass


class RoleUpdate(BaseModel):
    label: Optional[str] = Field(None, min_length=2, max_length=50)


class RoleRead(RoleBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
