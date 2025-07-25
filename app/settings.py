
import os
from dotenv import load_dotenv
from pathlib import Path
load_dotenv()

DEV_MACHINE = True if os.getenv('DEV_MACHINE', 'false') == 'true' else False

LOADS_NOSQL_LOC = Path(os.getenv('LOADS_JSON_LOCATION', 'storage/loads.json'))

TELEGRAM_BOT_APIKEY = '5030273725:AAH-pVUN1ZFC4w9cISDpE3cVQc4pgZZ8qgA'
TELEGRAM_DEVELOPER_CHAT_ID = os.getenv('TELEGRAM_DEVELOPER_CHAT_ID')
TELEGRAM_LOADS_CHAT_ID = os.getenv('TELEGRAM_LOADS_CHAT_ID')
DEFAULT_WEBHOOK_URL = os.getenv('DEFAULT_WEBHOOK_URL')

WEBHOOK_RESET_SECRET_TOKEN = os.getenv('WEBHOOK_RESET_SECRET_TOKEN')
WEBHOOK_RESET_SECRET_LINK = os.getenv('WEBHOOK_RESET_SECRET_LINK')
