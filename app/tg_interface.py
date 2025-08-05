
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    Application,
    filters
)
from telegram.error import TelegramError


async def handle_start(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE) -> None:
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='Hello, I am Telegram Bot.'
    )


async def handle_message(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=update.message.text
    )


async def handle_error(update: object, context: ContextTypes.DEFAULT_TYPE):
    raise context.error


async def webhook_entrypoint(data, app: Application):
    update = Update.de_json(data, app.bot)
    await app.process_update(update)


async def build(token: str, webhook_url: str) -> Application:
    app: Application = ApplicationBuilder().token(token).build()
    app.add_error_handler(handle_error)
    app.add_handler(CommandHandler('start', handle_start))
    app.add_handler(MessageHandler(filters.TEXT, handle_message))

    await app.initialize()
    await app.start()
    await app.bot.set_webhook(url=webhook_url)
    return app


async def destroy(app: Application) -> None:
    await app.bot.delete_webhook()
    await app.stop()
    await app.shutdown()
