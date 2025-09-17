
import os
from dotenv import load_dotenv
from pathlib import Path
load_dotenv()

DEV_MACHINE = True if os.getenv('DEV_MACHINE', 'false') == 'true' else False

LOADS_NOSQL_LOC = Path(os.getenv('LOADS_JSON_LOCATION', 'storage/loads.json'))

TELEGRAM_BOT_APIKEY = os.getenv('TELEGRAM_BOT_APIKEY')
DEVELOPER_BOT_APIKEY = os.getenv('DEVELOPER_BOT_APIKEY')


# DB_HOST = os.environ['DB_HOST']
# DB_PORT = os.environ['DB_PORT']
# DB_NAME = os.environ['DB_NAME']
# DB_USER = os.environ['DB_USER']
# DB_PASSWORD = os.environ['DB_PASSWORD']
DB_CONNECTION_URL=os.environ['DB_CONNECTION_URL']

WEBHOOK_BASE = os.getenv('WEBHOOK_BASE', 'https://api.intersmartgroup.com')
WEBHOOK_PATH = os.getenv('WEBHOOK_PATH', '/s2/loads-tgbot')
WEBHOOK_URL = WEBHOOK_BASE + WEBHOOK_PATH

WEBHOOK_RESET_SECRET_TOKEN = os.getenv('WEBHOOK_RESET_SECRET_TOKEN')
WEBHOOK_RESET_SECRET_LINK = os.getenv('WEBHOOK_RESET_SECRET_LINK')

DEBUG = False if os.getenv('DEBUG', 'false') == 'false' else True
# Using LOCALHOST if IS_LOCALHOST == True else Using PROD_HOST
# IS_LOCALHOST is needed only for testing purposes
IS_LOCALHOST = True if os.getenv('LOCALHOST', 'false') == 'true' else False
PROD_HOST = os.environ['PROD_HOST']
LOCALHOST = os.getenv('LOCALHOST', 'http://localhost:8000')

TELEGRAM_DEVELOPER_CHAT_ID = os.getenv('TELEGRAM_DEVELOPER_CHAT_ID')
TELEGRAM_LOADS_CHAT_ID = TELEGRAM_DEVELOPER_CHAT_ID if DEBUG else os.getenv('TELEGRAM_LOADS_CHAT_ID')
if TELEGRAM_LOADS_CHAT_ID is None:
    raise RuntimeError('TG_API_TOKEN environment variable not set')
TG_WEBHOOK_ENDPOINT = os.getenv('TG_WEBHOOK_ENDPOINT', '/tgwhep')
TG_API_TOKEN = os.getenv('TG_API_TOKEN', default=None)
if TG_API_TOKEN is None:
    raise RuntimeError('TG_API_TOKEN environment variable not set')
