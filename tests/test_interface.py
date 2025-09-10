
import pytest, pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from app.tg_interface.interface import AsyncTelegramInterface
from app.tg_interface import reply_buttons
from telegram import Update


def test_get_reply_kbd():
    simplified_kbd = reply_buttons.get_kbd()
    assert isinstance(simplified_kbd, list)
    assert len(simplified_kbd) > 0
    assert isinstance(simplified_kbd[0], list)


@pytest.fixture
def reply_kbd():
    return reply_buttons.get_kbd()

@pytest_asyncio.fixture
async def mocked_iface():
    with patch('app.tg_interface.interface.ApplicationBuilder') \
        as mock_app_builder_cls:

        mock_app = AsyncMock()

        mock_app_builder = MagicMock()
        mock_app_builder.token.return_value = mock_app_builder
        mock_app_builder.build.return_value = mock_app

        mock_app_builder_cls.return_value = mock_app_builder

        mock_loads = AsyncMock()
        iface = AsyncTelegramInterface(
            token='some_telegram_token:123457890',
            webhook_url='/telegram-webhook-url/',
            chat_id=-123498765,
            loads=mock_loads
        )
        async with iface:
            yield iface


@pytest.mark.asyncio
async def test_interface_init(mocked_iface):
    mocked_iface.app.add_error_handler.assert_called_once()
    mocked_iface.app.add_handler.assert_called()
    mocked_iface.app.initialize.assert_awaited_once()
    mocked_iface.app.start.assert_awaited_once()
    mocked_iface.app.bot.set_webhook.assert_awaited_once()


@patch('app.tg_interface.interface.ReplyKeyboardMarkup')
async def test_prepare_chat(mock_reply_kbd_markup, reply_kbd):
    chat_id = -123456789  # Telegram groups often have negative ids
    fake_loads = AsyncMock()
    fake_loads.get_qty_of_actives.return_value = 5
    fake_bot = AsyncMock()
    mock_reply_kbd_markup.return_value = 'mock_reply_kbd_markup'


    await AsyncTelegramInterface._prepare_chat(chat_id, fake_loads, fake_bot)

    fake_loads.get_qty_of_actives.assert_awaited_once()
    mock_reply_kbd_markup.assert_called_once_with(
        reply_kbd,
        resize_keyboard=True,
        one_time_keyboard=True
    )
    fake_bot.send_message.assert_awaited_once_with(
        chat_id=chat_id,
        text='Active loads: 5',
        reply_markup='mock_reply_kbd_markup',
        disable_notification = True
    )


@pytest.mark.asyncio
async def test_handle_start_calls_prepare_chat(mocked_iface):

    mocked_iface._prepare_chat = AsyncMock()

    fake_update = MagicMock()
    fake_update.effective_chat.id = 1234567890

    fake_bot = AsyncMock()
    fake_context = MagicMock()
    fake_context.bot = fake_bot

    await mocked_iface.handle_start(fake_update, fake_context)

    mocked_iface._prepare_chat.assert_awaited_once_with(
        fake_update.effective_chat.id,
        mocked_iface.loads,
        fake_context.bot
    )
