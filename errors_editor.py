from pydantic import BaseModel, Field, validator
from typing import NamedTuple
from typing import Optional

class Color(NamedTuple):
    R: int = Field(ge=0, le=255)
    G: int = Field(ge=0, le=255)
    B: int = Field(ge=0, le=255)
    A: Optional[int] = Field(ge=0, le=255)

class ErrorsColor(BaseModel):
    label: str
    background_color: Color
    color: Color
