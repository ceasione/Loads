
from typing import List, TYPE_CHECKING
import asyncio
from abc import ABC, abstractmethod
from app.loads import Loads
from app.tg_interface.tg_new_load_parser import LoadMessageParser, LoadMessageParseError

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
    async def action(update, context, loads: Loads, if_: 'AsyncTelegramInterface'):
        pass


class ShowActiveCommand(AbstractCommand):

    text = 'Show active'

    @staticmethod
    async def action(update, context, loads: Loads, if_):
        await if_.post_loads(
            chat_id=update.effective_chat.id,
            loads=tuple(loads.get_active_loads()),
            context=context
        )


class ShowDeletedCommand(AbstractCommand):

    text = 'Show deleted'

    @staticmethod
    async def action(update, context, loads: Loads, if_):
        await if_.post_loads(
            chat_id=update.effective_chat.id,
            loads=tuple(loads.get_deleted_loads()),
            context=context
        )


class CreateNewCommand(AbstractCommand):

    sample_external = \
        "new:external\n" \
        "Полтава\n" \
        "Чернівці\n" \
        "Ясси\n" \
        "Плопені\n\n" \
        "Козак Григорій\n" \
        "+380501231212\n\n" \
        "Client: +380953459607\n"

    sample_internal = \
        "new:internal\n" \
        "Дніпро\n" \
        "Конотоп\n\n" \
        "Козак Григорій\n" \
        "+380501231212\n\n" \
        "Client: +380953459607"

    text = 'Create new'

    @staticmethod
    async def action(update, context, loads: Loads, if_):

        await asyncio.gather(
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=CreateNewCommand.sample_external
            ),
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=CreateNewCommand.sample_internal
            )
        )


#  This command does not have a button representation
class ParseLoadCommand(AbstractCommand):

    text = 'new:'

    @staticmethod
    async def action(update, context, loads: Loads, if_):
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
        await if_.post_loads(
            chat_id=update.effective_chat.id,
            loads=(load, ),
            context=context,
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
