from typing import Any

from pydantic import BaseModel, Field, RootModel


class LogOut(RootModel[dict[str, Any]]):
    pass


class LogQuery(BaseModel):
    well: str = Field(
        ...,
        description="Well name, e.g. 'GUN_001' (case sensitive).",
    )
