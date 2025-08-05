
from typing import Optional, Any
import secrets
from telegram import (
    Update,
    ReplyKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    Application,
    filters
)
from app.loads import Loads


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
        self.app.add_handler(MessageHandler(filters.TEXT, self.handle_message))
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
            ['Show active', 'Show deleted'],
            ['Create new']
        ]
        bottom_keyboard = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
        active_loads_qty: int = len(self.loads.expose_active_loads())
        await self.app.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f'Active loads: {active_loads_qty}',
            reply_markup=bottom_keyboard,
            disable_notification=True
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

    @staticmethod
    async def handle_message(
            update: Update,
            context: ContextTypes.DEFAULT_TYPE) -> None:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=update.message.text
        )

    @staticmethod
    async def handle_error(update: object, context: ContextTypes.DEFAULT_TYPE):
        raise context.error

    async def webhook_entrypoint(self, data: dict[str, Any]):
        update = Update.de_json(data, self.app.bot)
        await self.app.process_update(update)
