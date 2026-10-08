from typing import Literal

from pydantic import BaseModel, ConfigDict


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Health(Contract):
    status: Literal["ok"] = "ok"
    service: Literal["airwise-schools"] = "airwise-schools"
    data_mode: Literal["SYNTHETIC"] = "SYNTHETIC"


class Section(Contract):
    id: str
    label: str
    size: int


class School(Contract):
    id: str
    name: str
    mode: Literal["SYNTHETIC"]
    timezone: Literal["Asia/Kolkata"]
    sections: list[Section]
