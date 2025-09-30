
import os
from dotenv import load_dotenv

if IS_LOCALHOST := os.getenv('IS_LOCALHOST', 'true') == 'true':
    load_dotenv()

# This has influence on Loglevel
DEBUG = os.getenv('DEBUG', 'false') == 'true'

# PostgreSQL
DB_HOST = os.getenv('DB_HOST', default='localhost')
DB_PORT = os.getenv('DB_PORT', default='5432')
DB_NAME = os.getenv('DB_NAME', default='loads_db')
DB_USER = os.getenv('DB_USER', default=None)
DB_PASSWORD = os.getenv('DB_PASSWORD', default=None)

# This host is using to set up Telegram Webhook
PROD_HOST = os.getenv('PROD_HOST', default=None)             # On IS_LOCALHOST == False
LOCALHOST = os.getenv('LOCALHOST', 'http://localhost:8000')  # On IS_LOCALHOST == True

# This is used to set up a Bot
TG_API_TOKEN = os.getenv('TG_API_TOKEN', default=None)
TG_WEBHOOK_ENDPOINT = os.getenv('TG_WEBHOOK_ENDPOINT', '/tgwhep')
TELEGRAM_DEVELOPER_CHAT_ID = os.getenv('TELEGRAM_DEVELOPER_CHAT_ID', default=None)
TELEGRAM_LOADS_CHAT_ID = TELEGRAM_DEVELOPER_CHAT_ID if DEBUG else os.getenv('TELEGRAM_LOADS_CHAT_ID')


SOCKET_LOC = os.getenv('SOCKET_LOC', default=None)


required_envs = {
    'DB_USER': DB_USER,
    'DB_PASSWORD': DB_PASSWORD,
    'PROD_HOST': PROD_HOST,
    'TG_API_TOKEN': TG_API_TOKEN,
    'TELEGRAM_DEVELOPER_CHAT_ID': TELEGRAM_DEVELOPER_CHAT_ID,
    'TELEGRAM_LOADS_CHAT_ID': TELEGRAM_LOADS_CHAT_ID,
    'SOCKET_LOC': SOCKET_LOC
}
for name, value in required_envs.items():
    if value is None:
        raise EnvironmentError(f"Required environment variable '{name}' is missing")

