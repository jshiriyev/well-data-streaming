from typing import Any, Optional

from pydantic import BaseModel, Field


class LogOut(BaseModel):
    well: str
    metadata: Optional[dict[str, Any]] = None
    data: Optional[dict[str, Any]] = None

    class Config:
        extra = "allow"


class LogQuery(BaseModel):
    well: str = Field(
        ...,
        description="Well name, e.g. 'GUN_0001' (case sensitive).",
    )
