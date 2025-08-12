
from typing import Optional, List
from abc import ABC, abstractmethod
from telegram import InlineKeyboardButton
from app.loads import Loads, Load


class AbstractButton(ABC):
    button_name: Optional[str] = None
    callback_prefix: Optional[str] = None

    @classmethod
    def get_callback_data(cls, load_id) -> str:
        if cls.button_name is None:
            raise ValueError(f"{cls.__name__} does not define button_name")
        if cls.callback_prefix is None:
            raise ValueError(f"{cls.__name__} does not define callback_prefix")
        return cls.callback_prefix+load_id

    @staticmethod
    def get_load_id(callback_data: str) -> str:
        _command, load_id = callback_data.split(':', 1)
        if len(load_id) != 32:
            raise RuntimeError('Invalid load_id')
        return load_id

    @staticmethod
    @abstractmethod
    def process_click(callback_data: str, loads: Loads) -> Optional[Load]:
        """
        returns edited Load instance or None if load were deleted
        """
        pass


class SetStartButton(AbstractButton):
    button_name = 'Set Start'
    callback_prefix = 'set_start:'

    @staticmethod
    def process_click(callback_data: str, loads: Loads) -> Optional[Load]:
        load_id = AbstractButton.get_load_id(callback_data)
        load: Load = loads.get_load_by_id(load_id)
        load.change_stage('start')
        return load


class SetEngagedButton(AbstractButton):
    button_name = 'Set Engage'
    callback_prefix = 'set_engage:'

    @staticmethod
    def process_click(callback_data: str, loads: Loads) -> Optional[Load]:
        load_id = AbstractButton.get_load_id(callback_data)
        load: Load = loads.get_load_by_id(load_id)
        load.change_stage('engage')
        return load


class SetDriveButton(AbstractButton):
    button_name = 'Set Drive'
    callback_prefix = 'set_drive:'

    @staticmethod
    def process_click(callback_data: str, loads: Loads) -> Optional[Load]:
        load_id = AbstractButton.get_load_id(callback_data)
        load: Load = loads.get_load_by_id(load_id)
        load.change_stage('drive')
        return load


class SetClearButton(AbstractButton):
    button_name = 'Set Clear'
    callback_prefix = 'set_clear:'

    @staticmethod
    def process_click(callback_data: str, loads: Loads) -> Optional[Load]:
        load_id = AbstractButton.get_load_id(callback_data)
        load: Load = loads.get_load_by_id(load_id)
        load.change_stage('clear')
        return load

class SetFinishButton(AbstractButton):
    button_name = 'Set Finish'
    callback_prefix = 'set_finish:'

    @staticmethod
    def process_click(callback_data: str, loads: Loads) -> Optional[Load]:
        load_id = AbstractButton.get_load_id(callback_data)
        load: Load = loads.get_load_by_id(load_id)
        load.change_stage('finish')
        return load

class DeleteButton(AbstractButton):
    button_name = 'Delete'
    callback_prefix = 'delete:'

    @staticmethod
    def process_click(callback_data: str, loads: Loads) -> Optional[Load]:
        load_id = AbstractButton.get_load_id(callback_data)
        load: Load = loads.get_load_by_id(load_id)
        load.change_stage('history')
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
