
from typing import List, TYPE_CHECKING
import asyncio
from abc import ABC, abstractmethod
from app.loads.loads import Loads
from app.tg_interface.tg_new_load_parser import LoadMessageParser, LoadMessageParseError
from telegram import Bot, Update

if TYPE_CHECKING:
    from typing import (
        List
    )
    from app.tg_interface.tg_interface import (
        AsyncTelegramInterface
    )

class AbstractCommand(ABC):

    text: str

    @staticmethod
    @abstractmethod
    async def action(
        update: Update,
        loads: Loads,
        bot: Bot,
        interface: 'AsyncTelegramInterface'
    ) -> None:
        pass


class ShowActiveCommand(AbstractCommand):

    text = 'Show active'

    @staticmethod
    async def action(
        update: Update,
        loads: Loads,
        bot: Bot,
        interface: 'AsyncTelegramInterface'
    ) -> None:
        await interface.post_loads(
            chat_id=update.effective_chat.id,
            loads=tuple(loads.get_active_loads()),
            bot=bot
        )


class ShowDeletedCommand(AbstractCommand):

    text = 'Show deleted'

    @staticmethod
    async def action(
        update: Update,
        loads: Loads,
        bot: Bot,
        interface: 'AsyncTelegramInterface'
    ) -> None:
        await interface.post_loads(
            chat_id=update.effective_chat.id,
            loads=tuple(loads.get_deleted_loads()),
            bot=bot
        )


class CreateNewCommand(AbstractCommand):

    SAMPLE_EXTERNAL = \
        "new:external\n" \
        "Полтава\n" \
        "Чернівці\n" \
        "Ясси\n" \
        "Плопені\n\n" \
        "Козак Григорій\n" \
        "+380501231212\n\n" \
        "Client: +380953459607\n"

    SAMPLE_INTERNAL = \
        "new:internal\n" \
        "Дніпро\n" \
        "Конотоп\n\n" \
        "Козак Григорій\n" \
        "+380501231212\n\n" \
        "Client: +380953459607"

    text = 'Create new'

    @staticmethod
    async def action(
        update: Update,
        loads: Loads,
        bot: Bot,
        interface: 'AsyncTelegramInterface'
    ) -> None:
        await asyncio.gather(
            bot.send_message(
                chat_id=update.effective_chat.id,
                text=CreateNewCommand.SAMPLE_EXTERNAL
            ),
            bot.send_message(
                chat_id=update.effective_chat.id,
                text=CreateNewCommand.SAMPLE_INTERNAL
            )
        )


#  This command does not have a button representation
class ParseLoadCommand(AbstractCommand):

    text = 'new:'

    @staticmethod
    async def action(
        update: Update,
        loads: Loads,
        bot: Bot,
        interface: 'AsyncTelegramInterface'
    ) -> None:
        message = update.message.text

        # 1. Get Load from message
        if 'new:external' in message:
            load = LoadMessageParser.external(message)
        elif 'new:internal' in message:
            load = LoadMessageParser.internal(message)
        else:
            raise LoadMessageParseError(message)

        # 2. Add Load to database
        loads.add_load(load)

        # 3. Send Load to the User via Bot
        await interface.post_loads(
            chat_id=update.effective_chat.id,
            loads=(load, ),
            bot=bot
        )


COMMANDS = (
    ShowActiveCommand,
    ShowDeletedCommand,
    CreateNewCommand,
    ParseLoadCommand
)


LAYOUT = (
    (ShowActiveCommand, ShowDeletedCommand),
    (CreateNewCommand, )
)


def get_kbd() -> List[List[str]]:
    layout = LAYOUT

    keyboard = []
    for layout_line in layout:
        keyboard_line = []
        for button in layout_line:
            keyboard_line.append(
                button.text
            )
        keyboard.append(keyboard_line)
    return keyboard
