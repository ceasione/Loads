
import os
from dotenv import load_dotenv
from pathlib import Path
load_dotenv()

DEV_MACHINE = True if os.getenv('DEV_MACHINE', 'false') == 'true' else False

LOADS_NOSQL_LOC = Path(os.getenv('LOADS_JSON_LOCATION', 'storage/loads.json'))

TELEGRAM_BOT_APIKEY = os.getenv('TELEGRAM_BOT_APIKEY')
DEVELOPER_BOT_APIKEY = os.getenv('DEVELOPER_BOT_APIKEY')


WEBHOOK_BASE = os.getenv('WEBHOOK_BASE', 'https://api.intersmartgroup.com')
WEBHOOK_PATH = os.getenv('WEBHOOK_PATH', '/s2/loads-tgbot')
WEBHOOK_URL = WEBHOOK_BASE + WEBHOOK_PATH

WEBHOOK_RESET_SECRET_TOKEN = os.getenv('WEBHOOK_RESET_SECRET_TOKEN')
WEBHOOK_RESET_SECRET_LINK = os.getenv('WEBHOOK_RESET_SECRET_LINK')

DEBUG = False if os.getenv('DEBUG', 'false') == 'false' else True
TELEGRAM_DEVELOPER_CHAT_ID = os.getenv('TELEGRAM_DEVELOPER_CHAT_ID')
TELEGRAM_LOADS_CHAT_ID = TELEGRAM_DEVELOPER_CHAT_ID if DEBUG else os.getenv('TELEGRAM_LOADS_CHAT_ID')
if TELEGRAM_LOADS_CHAT_ID is None:
    raise RuntimeError('TG_API_TOKEN environment variable not set')
TG_WEBHOOK_ENDPOINT = os.getenv('TG_WEBHOOK_ENDPOINT', '/tgwhep')
TG_API_TOKEN = os.getenv('TG_API_TOKEN', default=None)
if TG_API_TOKEN is None:
    raise RuntimeError('TG_API_TOKEN environment variable not set')
