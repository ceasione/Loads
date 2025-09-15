
from typing import List, TYPE_CHECKING
import asyncio
from abc import ABC, abstractmethod
from app.loads.loads import Loads
from app.tg_interface.new_load_parser import LoadMessageParser, LoadMessageParseError
from telegram import Bot, Update

if TYPE_CHECKING:
    from typing import (
        List
    )
    from app.tg_interface.interface import (
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
            loads = await loads.get_actives(),
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
            loads = await loads.get_historicals(),
            bot=bot
        )


class CreateNewCommand(AbstractCommand):

    SAMPLE_EXTERNAL = \
        "new:external\n" \
        "Полтава\n" \
        "Чернівці\n" \
        "Ясси\n" \
        "Плопені\n\n" \
        "ПІБводія\n" \
        "+380501231212\n\n" \
        "Client: +380953459607\n"

    SAMPLE_INTERNAL = \
        "new:internal\n" \
        "Дніпро\n" \
        "Конотоп\n\n" \
        "ПІБводія\n" \
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
        try:
            message = update.message.text

            # 1. Get Load from message
            if 'new:external' in message:
                load = LoadMessageParser.external(message)
            elif 'new:internal' in message:
                load = LoadMessageParser.internal(message)
            else:
                raise LoadMessageParseError(message)

            # 2. Add Load to database
            await loads.add(load)

            # 3. Send Load to the User via Bot
            await interface.post_loads(
                chat_id=update.effective_chat.id,
                loads=[load],
                bot=bot
            )
        except LoadMessageParseError as e:
            await bot.send_message(
                chat_id=update.effective_chat.id,
                text='✋ Ой помилочка! Перевірте чи все вірно вказано'
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
    """
    Remake LAYOUT so each button is represented by its label as string
    Preserves structure of the LAYOUT.
    """
    return [[button.text for button in line] for line in LAYOUT]
