from app import settings
import telegram
from telegram.error import BadRequest
import traceback
from datetime import datetime
import app.lib.utils.utils as utils


APIKEY = settings.TELEGRAM_BOT_APIKEY
SILENT_CHAT_ID = settings.TELEGRAM_SILENT_CHAT_ID
LOUD_CHAT_ID = settings.TELEGRAM_LOUD_CHAT_ID
DEVELOPER_CHAT_ID = settings.TELEGRAM_DEVELOPER_CHAT_ID


bot = telegram.Bot(token=APIKEY)


def _send_message(chat_id, text, parse_mode=None):
    # asyncio.run(bot.send_message(chat_id=chat_id, text=text, parse_mode=parse_mode))
    bot.send_message(chat_id=chat_id, text=text, parse_mode=parse_mode)


def send_message(chat_id: str, msg: str) -> None:
    try:
        _send_message(chat_id=chat_id, text=msg, parse_mode='MARKDOWN')
    except Exception as e:
        if isinstance(e, BadRequest) and "Can't parse entities" in str(e):
            _send_message(chat_id=chat_id, text=msg)
            error_message = f"{traceback.format_exc()}\n\n{msg}\n\nFailsafe msg has been sent"
            send_developer(error_message, e)
        else:
            error_message = f"{str(e)}\n\nTraceback: {traceback.format_exc()}\n\nmsg = {msg}"
            utils.log_safely(error_message)
            send_developer(error_message, e)


def send_silent(msg: str):
    send_message(SILENT_CHAT_ID, msg)


def send_loud(msg: str):
    send_message(LOUD_CHAT_ID, msg)


def send_developer(msg: str, cause: Exception = None) -> None:
    try:
        timestamp = datetime.now().isoformat()
        if cause is not None:
            txt_cause = str(cause)
            trace = str().join(traceback.format_exception(type(cause), cause, cause.__traceback__))
        else:
            txt_cause = 'No exception provided'
            trace = 'No exception provided'
        message = f"{timestamp}:\n\nMessage: {msg}\n\nCause: {txt_cause}\n\nTraceback: '{trace}'"
        _send_message(chat_id=DEVELOPER_CHAT_ID, text=message)

        error_message = \
            f"{timestamp} DEV TG report has been sent: {msg}\n\nCause: {txt_cause}\n\nTraceback: {trace}"
        utils.log_safely(error_message)
    except Exception as e:
        timestamp = datetime.now().isoformat()
        error_message = f"{timestamp} Failed to send dev tg report\n\n{str(e)}\n\n{traceback.format_exc()}\n\n{msg}"
        utils.log_safely(error_message)


# send_developer(f'Application boot at {datetime.now().strftime("%H:%M:%S")}')
