
import pytest, pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from app.tg_interface.interface import AsyncTelegramInterface
from app.tg_interface import reply_buttons


def test_get_reply_kbd():
    simplified_kbd = reply_buttons.get_kbd()
    assert isinstance(simplified_kbd, list)
    assert len(simplified_kbd) > 0
    assert isinstance(simplified_kbd[0], list)


@pytest.fixture
def reply_kbd():
    return reply_buttons.get_kbd()


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

