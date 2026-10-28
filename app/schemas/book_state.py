from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class BookStateBase(BaseModel):
    name: str = Field(
        ...,
        min_length=2,
        max_length=50,
        description="Condition state name (Available, Borrowed, Damaged, Lost)",
    )


class BookStateCreate(BookStateBase):
    pass


class BookStateUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=50)


class BookStateRead(BookStateBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
