import secrets
from datetime import datetime

from pydantic import (
    BaseModel,
    Field,
    model_validator,
    field_validator
)
from typing import Literal, Optional


class AllowedStagesViolation(ValueError):
    pass

class NoSuchLoadID(RuntimeError):
    pass

ALLOWED_STAGES = Literal['start', 'engage', 'drive', 'clear', 'finish', 'history']

class Stages(BaseModel):
    # Each stage is a city name
    start: str
    engage: Optional[str] = None
    drive: Optional[str] = None
    clear: Optional[str] = None
    finish: str

class Load(BaseModel):
    load_type: Literal['external', 'internal'] = Field(alias='type')
    stage: ALLOWED_STAGES
    stages: Stages
    client_num: str
    driver_name: str
    driver_num: str
    load_id: str = Field(alias='id', default_factory=lambda: secrets.token_hex(16))
    last_update: datetime = Field(default_factory=lambda: datetime.now())

    @model_validator(mode='after')
    def restrict_some_stages_for_internal_load(self):
        if self.load_type == 'internal':
            if self.stage in ('engage', 'clear'):
                raise ValueError('Internal Load must not have "engage" or "clear" stage')
        return self

    @field_validator('client_num', 'driver_num')
    @classmethod
    def validate_phone_number(cls, value):
        digits = ''.join(char for char in value if char in '0123456789')
        return digits[:12]

    @field_serializer('last_update')
    def format_time(self, last_update: datetime) -> str:
        return last_update.strftime('%H:%M')

    class Config:
        populate_by_name = True

    def is_load_external(self) -> bool:
        return True if self.load_type == 'external' else False

    def change_stage(self, new_stage: ALLOWED_STAGES):
        self.stage = new_stage
        self.last_update = datetime.now()

    def safe_dump(self) -> dict:
        return self.model_dump(
            exclude={
                'client_num',
                'driver_num',
                'driver_name'
            },
            by_alias=True
        )
