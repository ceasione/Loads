
from typing import Optional, Any
from telegram import Update
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
        await self.app.bot.set_webhook(url=self.webhook_url)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.app.bot.delete_webhook()
        await self.app.stop()
        await self.app.shutdown()

    @staticmethod
    async def handle_start(
            update: Update,
            context: ContextTypes.DEFAULT_TYPE) -> None:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text='Hello, I am Telegram Bot.'
        )

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
