import secrets
from datetime import datetime

from pydantic import (
    BaseModel,
    Field,
    model_validator,
    field_validator,
    field_serializer,
    ConfigDict
)
from typing import Literal, Optional


class AllowedStagesViolation(ValueError):
    """Exception raised when an invalid stage is assigned to a load."""
    pass

class NoSuchLoadID(RuntimeError):
    """Exception raised when attempting to access a non-existent load ID."""
    pass

ALLOWED_STAGES = Literal['start', 'engage', 'drive', 'clear', 'finish', 'history']

class Stages(BaseModel):
    """
    Model representing the different stages/locations in a load's journey.

    Attributes:
        start: Starting city/location for the load.
        engage: Optional customs engagement point (for external loads).
        drive: Optional driving destination.
        clear: Optional customs clearance location (for external loads).
        finish: Final destination city/location.
    """
    # Each stage is a city name
    start: str
    engage: Optional[str] = None
    drive: Optional[str] = None
    clear: Optional[str] = None
    finish: str

class Load(BaseModel):
    """
    Model representing a transportation load with all its associated data.

    This model handles both internal and external loads, with different
    validation rules and stage requirements for each type.

    Attributes:
        load_type: Type of load ('external' or 'internal').
        stage: Current stage of the load.
        stages: All stage locations for the load journey.
        client_num: Client's phone number.
        driver_name: Name of the assigned driver.
        driver_num: Driver's phone number.
        load_id: Unique identifier for the load.
        last_update: Timestamp of the last update.
    """
    model_config = ConfigDict(populate_by_name=True)

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
        """
        Validate that internal loads don't have 'engage' or 'clear' stages.

        Internal loads have a simplified workflow and should not include
        the engage and clear stages that are used for external loads.

        Returns:
            self: The validated load instance.

        Raises:
            ValueError: If an internal load has engage or clear stage.
        """
        if self.load_type == 'internal':
            if self.stage in ('engage', 'clear'):
                raise ValueError('Internal Load must not have "engage" or "clear" stage')
        return self

    @field_validator('client_num', 'driver_num')
    @classmethod
    def validate_phone_number(cls, value):
        """
        Validate and normalize phone numbers.

        Extracts digits from phone numbers and limits to 12 characters
        to ensure consistent formatting.

        Args:
            value: Raw phone number string.

        Returns:
            str: Normalized phone number with only digits (max 12 chars).
        """
        digits = ''.join(char for char in value if char in '0123456789')
        return digits[:12]

    @field_serializer('last_update')
    def format_time(self, last_update: datetime) -> str:
        """
        Format the last_update timestamp for display.

        Args:
            last_update: Datetime object to format.

        Returns:
            str: Formatted time string in HH:MM format.
        """
        return last_update.strftime('%H:%M')

    def is_load_external(self) -> bool:
        """
        Check if the load is an external load.

        Returns:
            bool: True if load type is 'external', False otherwise.
        """
        return True if self.load_type == 'external' else False

    def change_stage(self, new_stage: ALLOWED_STAGES):
        """
        Update the load to a new stage and refresh the timestamp.

        Args:
            new_stage: The new stage to transition to.
        """
        self.stage = new_stage
        self.last_update = datetime.now()

    def safe_dump(self) -> dict:
        """
        Generate a safe dictionary representation excluding sensitive data.

        Excludes client phone number, driver phone number, and driver name
        to protect sensitive information when exposing data publicly.

        Returns:
            dict: Load data with sensitive fields excluded, using field aliases.
        """
        return self.model_dump(
            exclude={
                'client_num',
                'driver_num',
                'driver_name'
            },
            by_alias=True
        )
