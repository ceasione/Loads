
from typing import List, Tuple, Optional, Any, TYPE_CHECKING
import secrets
from app.loads.loads import Loads
from app.loads.load import Load
from app.tg_interface.inline_buttons import get_kbd, BUTTONS
from app.tg_interface.reply_buttons import get_kbd as get_reply_kbd, COMMANDS
from telegram import (
    Bot,
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

if TYPE_CHECKING:
    from telegram import Bot


def craft_load_message(load: Load) -> Tuple[str, InlineKeyboardMarkup]:
    """
    Builds a textual description and inline keyboard for a given load.

    The generated message includes:
        - Start and finish stage locations.
        - Driver's name and phone number.
        - Current stage and the last update timestamp.

    The inline keyboard is created using `get_kbd()` with the load's ID and
    external status.

    Args:
        load (Load): The load instance containing stage, driver, and status
            information.

    Returns:
        Tuple[str, InlineKeyboardMarkup]:
            - A formatted message string describing the load.
            - An inline keyboard for interacting with the load.
    """
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

    @staticmethod
    async def _prepare_chat(chat_id: int, loads: Loads, bot: Bot) -> None:
        """
        Sends a message to the specified chat displaying the number of active loads.

        This method sends a reply keyboard with control commands to the chat for users
        to be able to control the bot

        Args:
            chat_id (int): Unique identifier of the target chat.
            loads (Loads): An object that provides the `expose_active_loads()` method
                to retrieve the list of active loads.
            bot (Bot): A PTB Bot instance used to send the message.

        Returns:
            None
        """
        keyboard = get_reply_kbd()
        active_loads_qty: int = await loads.get_qty_of_actives()
        reply_keyboard = ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True,
            one_time_keyboard=True
        )
        await bot.send_message(
            chat_id=chat_id,
            text=f'Active loads: {active_loads_qty}',
            reply_markup=reply_keyboard,
            disable_notification=True
        )

    @staticmethod
    async def post_loads(
            chat_id: int,
            loads: List[Load],
            bot: Bot
    ) -> None:
        """
        Sends messages to the specified chat for each load in the provided tuple.

        For each load, this method uses `craft_load_message()` to generate the
        message text and associated inline keyboard, then sends it via the given bot.
        After all loads are posted, it sends a final summary message with the
        total number of loads sent.

        Args:
            chat_id (int): Unique identifier of the target chat.
            loads (Tuple[Load, ...]): A tuple of `Load` instances to be posted.
            bot (Bot): A PTB Bot instance used to send the messages.

        Returns:
            None
        """
        for load in loads:
            text, kbd = craft_load_message(load)
            await bot.send_message(
                chat_id=chat_id,
                text=text,
                reply_markup=kbd
            )
        await bot.send_message(
            chat_id=chat_id,
            text=f'Total {len(loads)} loads'
        )

    async def handle_start(
            self,
            update: Update,
            context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handler for the /start command. Prepares the chat interface.

        This method triggers `_prepare_chat()` to send an initial message and a
        reply keyboard for further bot interactions.

        Args:
            update (Update): The incoming update containing message and chat data.
            context (ContextTypes.DEFAULT_TYPE): The context for the callback,
                providing the bot instance and other runtime data.

        Returns:
            None
        """
        await self._prepare_chat(
            update.effective_chat.id,
            self.loads,
            context.bot
        )

    async def handle_text(
            self,
            update: Update,
            context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """
        Handles incoming text messages by matching them against predefined commands.

        Iterates over the `COMMANDS` collection and executes the associated action
        for the first command whose text is found in the incoming message. If no
        command matches, sends a fallback message indicating the text was not
        understood.

        Args:
            update (Update): The incoming update containing the user's message.
            context (ContextTypes.DEFAULT_TYPE): The context for the callback,
                providing the bot instance and other runtime data.

        Returns:
            None

        Side Effects:
            - Executes a command's action if matched.
            - Sends a fallback message to the chat if no match is found.
        """
        message = update.message.text

        for cmd in COMMANDS:
            if cmd.text in message:
                await cmd.action(
                    update=update,
                    loads=self.loads,
                    bot=context.bot,
                    interface=self
                )
                return
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f'✋ {message}?'
        )

    async def handle_inline_buttons(
            self,
            update: Update,
            _context: ContextTypes.DEFAULT_TYPE):
        """
        Handler for inline button clicks from the loads messages.

        Matches the callback data from the clicked button against entries in the
        `BUTTONS` collection. Executes the associated button's `process_click()`
        method, which may update or delete a load. If the load is deleted, the
        original message is replaced with "Deleted". If the load is updated,
        the message is edited with the new load details and updated inline keyboard.

        Args:
            update (Update): The incoming update containing the callback query data.
            _context (ContextTypes.DEFAULT_TYPE): The callback context. Unused here.

        Returns:
            None

        Side Effects:
            - Edits the bot's message in response to the button click.
            - Sends a callback query answer to acknowledge the click.
        """
        callback_data = update.callback_query.data
        for btn in BUTTONS:
            if btn.callback_prefix in callback_data:
                edited_load = await btn.process_click(
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
        """
        Entry point for processing incoming webhook updates.

        Converts the raw webhook payload into an `Update` object and passes it to
        the application's bot for processing.

        Args:
            data (dict[str, Any]): The JSON payload received from the
            FastAPI webhook endpoint.

        Returns:
            None

        Side Effects:
            Passes the update to `self.app.process_update()` for handling.
        """
        update = Update.de_json(data, self.app.bot)
        await self.app.process_update(update)
