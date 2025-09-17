
from typing import Optional, List
from abc import ABC, abstractmethod
from telegram import InlineKeyboardButton
from app.loads.loads import Loads
from app.loads.load import Load


def extract_id_from_callback_data(callback_data: str) -> str:
    """
    Extract load ID from Telegram callback data.

    Args:
        callback_data: Callback data in format 'command:load_id'.

    Returns:
        str: The extracted load ID (32 characters).

    Raises:
        RuntimeError: If callback format is invalid or load_id length is wrong.
    """
    command, sep, load_id = callback_data.partition(':')
    if sep != ':' or len(load_id) != 32:
        raise RuntimeError('Invalid load_id or callback format')
    return load_id


class AbstractButton(ABC):
    """
    Abstract base class for inline keyboard buttons.

    Provides common functionality for generating callback data
    and processing button clicks for load stage management.
    """
    button_name: Optional[str] = None
    callback_prefix: Optional[str] = None

    @classmethod
    def get_callback_data(cls, load_id) -> str:
        """
        Generate callback data for the button.

        Args:
            load_id: Unique identifier for the load.

        Returns:
            str: Formatted callback data string.

        Raises:
            ValueError: If button_name or callback_prefix is not defined.
        """
        if cls.button_name is None:
            raise ValueError(f"{cls.__name__} does not define button_name")
        if cls.callback_prefix is None:
            raise ValueError(f"{cls.__name__} does not define callback_prefix")
        return cls.callback_prefix+load_id

    @staticmethod
    @abstractmethod
    async def process_click(callback_data: str, loads: Loads) -> Optional[Load]:
        """
        returns edited Load instance or None if load was deleted
        """
        pass


class SetStartButton(AbstractButton):
    """Button to set load stage to 'start'."""
    button_name = 'Set Start'
    callback_prefix = 'set_start:'

    @staticmethod
    async def process_click(callback_data: str, loads: Loads) -> Optional[Load]:
        load_id = extract_id_from_callback_data(callback_data)
        load: Load = await loads.get_load_by_id(load_id)
        await loads.change_stage(load, 'start')
        return load


class SetEngagedButton(AbstractButton):
    """Button to set load stage to 'engage'."""
    button_name = 'Set Engage'
    callback_prefix = 'set_engage:'

    @staticmethod
    async def process_click(callback_data: str, loads: Loads) -> Optional[Load]:
        load_id = extract_id_from_callback_data(callback_data)
        load: Load = await loads.get_load_by_id(load_id)
        await loads.change_stage(load, 'engage')
        return load


class SetDriveButton(AbstractButton):
    """Button to set load stage to 'drive'."""
    button_name = 'Set Drive'
    callback_prefix = 'set_drive:'

    @staticmethod
    async def process_click(callback_data: str, loads: Loads) -> Optional[Load]:
        load_id = extract_id_from_callback_data(callback_data)
        load: Load = await loads.get_load_by_id(load_id)
        await loads.change_stage(load, 'drive')
        return load


class SetClearButton(AbstractButton):
    """Button to set load stage to 'clear'."""
    button_name = 'Set Clear'
    callback_prefix = 'set_clear:'

    @staticmethod
    async def process_click(callback_data: str, loads: Loads) -> Optional[Load]:
        load_id = extract_id_from_callback_data(callback_data)
        load: Load = await loads.get_load_by_id(load_id)
        await loads.change_stage(load, 'clear')
        return load

class SetFinishButton(AbstractButton):
    """Button to set load stage to 'finish'."""
    button_name = 'Set Finish'
    callback_prefix = 'set_finish:'

    @staticmethod
    async def process_click(callback_data: str, loads: Loads) -> Optional[Load]:
        load_id = extract_id_from_callback_data(callback_data)
        load: Load = await loads.get_load_by_id(load_id)
        await loads.change_stage(load, 'finish')
        return load

class DeleteButton(AbstractButton):
    """Button to move load to 'history' stage (delete)."""
    button_name = 'Delete'
    callback_prefix = 'delete:'

    @staticmethod
    async def process_click(callback_data: str, loads: Loads) -> Optional[Load]:
        load_id = extract_id_from_callback_data(callback_data)
        load: Load = await loads.get_load_by_id(load_id)
        await loads.change_stage(load, 'history')
        return None


BUTTONS = (
    SetStartButton,
    SetEngagedButton,
    SetDriveButton,
    SetClearButton,
    SetFinishButton,
    DeleteButton
)

EXTERNAL_LAYOUT = (
    (SetStartButton, SetEngagedButton, SetDriveButton),
    (SetClearButton, SetFinishButton, DeleteButton)
)

INTERNAL_LAYOUT = (
    (SetStartButton, SetDriveButton),
    (SetFinishButton, DeleteButton)
)


def get_kbd(load_id: str, external_layout: bool) -> List[List[InlineKeyboardButton]]:
    layout = EXTERNAL_LAYOUT if external_layout else INTERNAL_LAYOUT

    keyboard = []
    for layout_line in layout:
        keyboard_line = []
        for button in layout_line:
            keyboard_line.append(
                InlineKeyboardButton(
                    text=button.button_name,
                    callback_data=button.get_callback_data(load_id)
                )
            )
        keyboard.append(keyboard_line)
    return keyboard
