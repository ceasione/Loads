
import asyncio
from abc import ABC, abstractmethod
from typing import Tuple, Optional, Any, cast, Sequence, List
import secrets
from telegram import (
    Update,
    ReplyKeyboardMarkup,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    Application,
    filters
)
from app.loads import Loads, Load


def craft_load_message(load: Load) -> Tuple[str, InlineKeyboardMarkup]:
    craft = \
        f'{load.stages["start"]} ... {load.stages["finish"]}\n'\
        f'{load.driver["name"]}, +{load.driver["num"]}\n'\
        f'\nStage: {load.stage} ({load.last_update})'

    if load.type == 'external':
        inline_keyboard = [
            [InlineKeyboardButton("Set Start", callback_data=f'set_start:{load.id}'),
             InlineKeyboardButton("Set Engage", callback_data=f'set_engage:{load.id}'),
             InlineKeyboardButton("Set Drive", callback_data=f'set_drive:{load.id}')],

            [InlineKeyboardButton("Set Clear", callback_data=f'set_clear:{load.id}'),
             InlineKeyboardButton("Set Finish", callback_data=f'set_finish:{load.id}'),
             InlineKeyboardButton("Delete", callback_data=f'delete:{load.id}')]
        ]
    elif load.type == 'internal':
        inline_keyboard = [
            [InlineKeyboardButton("Set Start", callback_data=f'set_start:{load.id}'),
             InlineKeyboardButton("Set Drive", callback_data=f'set_drive:{load.id}')],

            [InlineKeyboardButton("Set Finish", callback_data=f'set_finish:{load.id}'),
             InlineKeyboardButton("Delete", callback_data=f'delete:{load.id}')]
        ]
    else:
        raise RuntimeError(f'Unknown load type: {load.type}')

    reply_markup = InlineKeyboardMarkup(inline_keyboard)
    return craft, reply_markup


class LoadMessageParseError(RuntimeError):
    pass


class LoadMessageParser:

    @staticmethod
    def external(message: str) -> Load:
        """
        0 new:external
        1 Кривой Рог
        2 Днепр
        3 Черновцы
        4 Яссы
        5
        6 Козак Григорий
        7 +380501231212
        8
        9 Client: +380953459607
        """
        try:
            lines = message.strip().split('\n')
            start_place = lines[1].strip()
            engage_place = lines[2].strip()
            clear_place = lines[3].strip()
            finish_place = lines[4].strip()
            driver_name = lines[6].strip()
            driver_num = lines[7].strip().replace('+', '')
            client_num = lines[9].replace('Client: ', '').strip().replace('+', '')
            if not all(
                    (
                            start_place,
                            engage_place,
                            clear_place,
                            finish_place,
                            driver_name,
                            driver_num,
                            client_num
                    )
            ):
                raise LoadMessageParseError(message)
        except IndexError as e:
            raise LoadMessageParseError(message) from e

        return Load(load_type='external',
                    stage='history',
                    start=start_place,
                    engage=engage_place,
                    clear=clear_place,
                    finish=finish_place,
                    client_num=client_num,
                    driver_name=driver_name,
                    driver_num=driver_num)

    @staticmethod
    def internal(message: str) -> Load:
        """
            0 new:external
            1 Кривой Рог
            2 Днепр
            3 Черновцы
            4 Яссы
            5
            6 Козак Григорий
            7 +380501231212
            8
            9 Client: +380953459607
            """
        try:
            lines = message.strip().split('\n')
            start_place = lines[1].strip()
            finish_place = lines[2].strip()
            driver_name = lines[4].strip()
            driver_num = lines[5].strip().replace('+', '')
            client_num = lines[7].replace('Client: ', '').strip().replace('+', '')

            if not all(
                    (
                            start_place,
                            finish_place,
                            driver_name,
                            driver_num,
                            client_num
                    )
            ):
                raise LoadMessageParseError(message)
        except IndexError as e:
            raise LoadMessageParseError(message) from e

        return Load(load_type='internal',
                    stage='history',
                    start=start_place,
                    engage=None,
                    clear=None,
                    finish=finish_place,
                    client_num=client_num,
                    driver_name=driver_name,
                    driver_num=driver_num)


class AbstractCommand(ABC):

    text: str

    @staticmethod
    @abstractmethod
    async def action(update, context, loads: Loads):
        pass


class ShowActiveCommand(AbstractCommand):

    text = 'Show active'

    @staticmethod
    async def action(update, context, loads: Loads):
        await AsyncTelegramInterface.post_loads(
            chat_id=update.effective_chat.id,
            loads=tuple(loads.get_active_loads()),
            context=context
        )


class ShowDeletedCommand(AbstractCommand):

    text = 'Show deleted'

    @staticmethod
    async def action(update, context, loads: Loads):
        await AsyncTelegramInterface.post_loads(
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
    async def action(update, context, loads: Loads):

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


class ParseLoadCommand(AbstractCommand):

    text = 'new:'

    @staticmethod
    async def action(update, context, loads: Loads):
        message = update.message.text

        # 1. Get Load from message
        load: Optional[Load] = None
        if 'new:external' in message:
            load = LoadMessageParser.external(message)
        elif 'new:internal' in message:
            load = LoadMessageParser.internal(message)
        else:
            raise LoadMessageParseError(message)

        # 2. Add Load to database
        loads.add_load(load)

        # 3. Send Load to the User via Bot
        await AsyncTelegramInterface.post_loads(
            chat_id=update.effective_chat.id,
            loads=(load, ),
            context=context,
        )


class AsyncTelegramInterface:

    def __init__(
            self,
            token: str,
            webhook_url: str,
            chat_id: int,
            loads: Loads):
        self.token: str = token
        self.webhook_url: str = webhook_url
        self.chat_id: int = chat_id
        self.app: Optional[Application] = None
        self.loads: Loads = loads
        self.own_secret = secrets.token_urlsafe(32)

    async def __aenter__(self) -> 'AsyncTelegramInterface':
        self.app = ApplicationBuilder().token(self.token).build()
        self.app.add_error_handler(self.handle_error)
        self.app.add_handler(CommandHandler('start', self.handle_start))
        self.app.add_handler(MessageHandler(filters.TEXT, self.handle_text))
        await self.app.initialize()
        await self.app.start()
        await self.app.bot.set_webhook(url=self.webhook_url, secret_token=self.own_secret)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.app.bot.delete_webhook()
        await self.app.stop()
        await self.app.shutdown()

    async def _prepare_chat(self, update, _context):
        """
        Sends a message with quantity of loads and set
        ReplyKeyboardMarkup to show a keyboard at the bottom of chat.
        """
        keyboard = [
            [ShowActiveCommand.text, ShowDeletedCommand.text],
            [CreateNewCommand.text]
        ]
        bottom_keyboard = ReplyKeyboardMarkup(cast(Sequence, keyboard), resize_keyboard=True, one_time_keyboard=True)
        active_loads_qty: int = len(self.loads.expose_active_loads())
        await self.app.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f'Active loads: {active_loads_qty}',
            reply_markup=bottom_keyboard,
            disable_notification=True
        )

    @staticmethod
    async def post_loads(
            chat_id: int,
            loads: Tuple[Load, ...],
            context: ContextTypes.DEFAULT_TYPE,

    ) -> None:
        coros = []
        for load in loads:
            text, kbd = craft_load_message(load)
            coros.append(
                context.bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    reply_markup=kbd
                )
            )
        await asyncio.gather(*coros)
        await context.bot.send_message(
            chat_id=chat_id,
            text=f'Total {len(loads)} loads'
        )

    async def handle_start(
            self,
            update: Update,
            context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handles the /start command. For this command we are preparing
        the ReplyKeyboardMarkup for further bot controls
        """
        await self._prepare_chat(update, context)

    TXT_COMMANDS: List[AbstractCommand] = [
        ShowActiveCommand,
        ShowDeletedCommand,
        CreateNewCommand,
        ParseLoadCommand
    ]

    async def handle_text(
            self,
            update: Update,
            context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        message = update.message.text

        for cmd in self.TXT_COMMANDS:
            if cmd.text in message:
                await cmd.action(update, context, loads=self.loads)
                return

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f'Щось незрозуміле: {message}'
        )

    @staticmethod
    async def handle_error(update: object, context: ContextTypes.DEFAULT_TYPE):
        raise NotImplemented() from context.error
        # raise context.error

    async def webhook_entrypoint(self, data: dict[str, Any]):
        update = Update.de_json(data, self.app.bot)
        await self.app.process_update(update)
