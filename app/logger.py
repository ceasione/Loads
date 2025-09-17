import logging
import sys
from typing import Dict
from app import settings


class ColoredFormatter(logging.Formatter):
    """Colored log formatter for console output."""

    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
        'RESET': '\033[0m'       # Reset
    }

    def format(self, record):
        log_color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset_color = self.COLORS['RESET']

        # Add color to the entire message
        record.levelname = f"{log_color}{record.levelname}{reset_color}"
        record.name = f"{log_color}{record.name}{reset_color}"

        return super().format(record)


class TelegramLogHandler(logging.Handler):
    """
    Custom logging handler to send logs to Telegram developer chat.

    This is a stub implementation for future development.
    When implemented, this handler will send log messages to the
    Telegram developer chat for real-time monitoring.
    """

    def __init__(self, bot_token: str = None, chat_id: str = None, level: int = logging.ERROR):
        """
        Initialize Telegram log handler.

        Args:
            bot_token: Telegram bot token for sending messages.
            chat_id: Developer chat ID to send logs to.
            level: Minimum log level to send to Telegram.
        """
        super().__init__(level)
        self.bot_token = bot_token or settings.TG_API_TOKEN
        self.chat_id = chat_id or settings.TELEGRAM_DEVELOPER_CHAT_ID
        self.enabled = False  # TODO: Add settings flag to enable/disable

    def emit(self, record):
        """
        Emit a log record to Telegram.

        Args:
            record: LogRecord instance to send.
        """
        if not self.enabled:
            return

        try:
            # TODO: Implement actual Telegram message sending
            # This would format the log message and send it via Telegram Bot API
            log_entry = self.format(record)
            # await send_telegram_message(self.bot_token, self.chat_id, log_entry)
            pass
        except Exception:
            # Never let logging errors crash the application
            self.handleError(record)


def setup_logging() -> Dict[str, logging.Logger]:
    """
    Set up logging configuration for different application areas.

    Creates separate loggers for different modules with appropriate
    formatting and log levels based on the DEBUG setting.

    Returns:
        Dict[str, logging.Logger]: Dictionary of configured loggers by area.
    """
    # Determine log level based on DEBUG setting
    log_level = logging.DEBUG if settings.DEBUG else logging.INFO

    # Create formatters
    console_formatter = ColoredFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    telegram_formatter = logging.Formatter(
        '🚨 %(levelname)s - %(name)s\n%(funcName)s:%(lineno)d\n%(message)s'
    )

    # Configure console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(log_level)

    # Configure file handler if not in debug mode
    file_handler = None
    if not settings.DEBUG:
        file_handler = logging.FileHandler('app.log')
        file_handler.setFormatter(file_formatter)
        file_handler.setLevel(logging.INFO)

    # Configure Telegram handler (stub)
    telegram_handler = TelegramLogHandler(level=logging.ERROR)
    telegram_handler.setFormatter(telegram_formatter)

    # Create loggers for different application areas
    loggers = {}
    logger_names = {
        'api': 'loads.api',
        'tg_interface': 'loads.telegram',
        'database': 'loads.database',
        'pydantic_model': 'loads.models',
        'parser': 'loads.parser',
        'buttons': 'loads.buttons'
    }

    for area, logger_name in logger_names.items():
        logger = logging.getLogger(logger_name)
        logger.setLevel(log_level)

        # Clear existing handlers to avoid duplicates
        logger.handlers.clear()
        logger.propagate = False

        # Add handlers
        logger.addHandler(console_handler)
        if file_handler:
            logger.addHandler(file_handler)
        logger.addHandler(telegram_handler)

        loggers[area] = logger

    return loggers


def get_logger(area: str) -> logging.Logger:
    """
    Get a logger for a specific application area.

    Args:
        area: Application area ('api', 'tg_interface', 'database',
              'pydantic_model', 'parser', 'buttons').

    Returns:
        logging.Logger: Configured logger for the specified area.

    Raises:
        ValueError: If the specified area is not recognized.
    """
    logger_names = {
        'api': 'loads.api',
        'tg_interface': 'loads.telegram',
        'database': 'loads.database',
        'pydantic_model': 'loads.models',
        'parser': 'loads.parser',
        'buttons': 'loads.buttons'
    }

    if area not in logger_names:
        raise ValueError(f"Unknown logging area: {area}. Available: {list(logger_names.keys())}")

    return logging.getLogger(logger_names[area])


# Initialize logging on module import
_loggers = setup_logging()

# Export loggers for easy access
api_logger = _loggers['api']
tg_logger = _loggers['tg_interface']
db_logger = _loggers['database']
model_logger = _loggers['pydantic_model']
parser_logger = _loggers['parser']
buttons_logger = _loggers['buttons']
