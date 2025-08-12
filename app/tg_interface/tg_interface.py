from typing import Tuple, Optional, Any, cast, Sequence, List
import secrets
from telegram import (
    Update,
    ReplyKeyboardMarkup,
    InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    Application,
    filters
)
from app.loads import Loads, Load
from app.tg_interface.tg_inline_buttons import get_kbd, BUTTONS
from app.tg_interface.tg_reply_buttons import get_kbd as get_reply_kbd, COMMANDS


def craft_load_message(load: Load) -> Tuple[str, InlineKeyboardMarkup]:
    craft = \
        f'{load.stages["start"]} ... {load.stages["finish"]}\n'\
        f'{load.driver["name"]}, +{load.driver["num"]}\n'\
        f'\nStage: {load.stage} ({load.last_update})'
    reply_markup = InlineKeyboardMarkup(
        get_kbd(
            load_id=load.id,
            external_layout=load.is_load_external()
        )
    )
    return craft, reply_markup


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
        self.app.add_handler(CallbackQueryHandler(self.handle_inline_buttons))
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
        keyboard = get_reply_kbd()
        reply_keyboard = ReplyKeyboardMarkup(cast(Sequence, keyboard), resize_keyboard=True, one_time_keyboard=True)
        active_loads_qty: int = len(self.loads.expose_active_loads())
        await self.app.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f'Active loads: {active_loads_qty}',
            reply_markup=reply_keyboard,
            disable_notification=True
        )

    @staticmethod
    async def post_loads(
            chat_id: int,
            loads: Tuple[Load, ...],
            context: ContextTypes.DEFAULT_TYPE,

    ) -> None:

        for load in loads:
            text, kbd = craft_load_message(load)
            await context.bot.send_message(
                chat_id=chat_id,
                text=text,
                reply_markup=kbd
            )
        await context.bot.send_message(
            chat_id=chat_id,
            text=f'Total {len(loads)} loads'
        )

    @staticmethod
    async def post_message(
            chat_id: int,
            message: str,
            context: ContextTypes.DEFAULT_TYPE,

    ) -> None:
        await context.bot.send_message(
            chat_id=chat_id,
            text=message
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

    async def handle_text(
            self,
            update: Update,
            context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        message = update.message.text

        for cmd in COMMANDS:
            if cmd.text in message:
                await cmd.action(update, context, loads=self.loads, if_=self)
                return

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f'Щось незрозуміле: {message}'
        )


    async def handle_inline_buttons(
            self,
            update: Update,
            context: ContextTypes.DEFAULT_TYPE):
        callback_data = update.callback_query.data
        for btn in BUTTONS:
            if btn.callback_prefix in callback_data:
                edited_load = btn.process_click(
                    callback_data=callback_data,
                    loads=self.loads
                )
                if edited_load is None:
                    await update.callback_query.edit_message_text('Deleted')
                    await update.callback_query.answer()
                    return

                edited_load_msg, keyboard = craft_load_message(edited_load)
                await update.callback_query.edit_message_text(
                    text=edited_load_msg,
                    reply_markup=keyboard
                )
                await update.callback_query.answer()
                return

    async def handle_error(self, update: object, context: ContextTypes.DEFAULT_TYPE):
        # LOG
        # Send error to user
        raise context.error
        # raise context.error

    async def webhook_entrypoint(self, data: dict[str, Any]):
        update = Update.de_json(data, self.app.bot)
        await self.app.process_update(update)
