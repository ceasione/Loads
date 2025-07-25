from app import settings
from app.lib.apis import telegramapi2
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
from queue import Queue
import secrets
from abc import ABC, abstractmethod
import time
import threading
from app.lib.loads.loads import Load, Loads
from textwrap import dedent


class TelegramInterface:

    def __init__(self, loads: Loads,
                 webhook_url=settings.DEFAULT_WEBHOOK_URL,
                 chat_id=settings.TELEGRAM_LOADS_CHAT_ID,
                 _context=None):
        self.bot = telegramapi2.bot
        self.dispatcher = Dispatcher(bot=self.bot, update_queue=Queue(), use_context=True)
        self.chat_id = chat_id
        self.dispatcher.add_handler(CommandHandler(command="start", callback=self.handle_cmd_start))
        self.dispatcher.add_handler(MessageHandler(filters=Filters.text, callback=self.handle_messages))
        self.dispatcher.add_handler(CallbackQueryHandler(callback=self.handle_inline_buttons))
        loads.iface_instance = self
        self.loads_instance = loads
        if _context is None:
            self.dialog_context = TelegramInterface.DialogContext(
                self,
                loads,
                TelegramInterface.StandbyState()
            )
        else:
            self.dialog_context = _context

        self.own_secret = secrets.token_urlsafe(32)
        self.bot.set_webhook(webhook_url, secret_token=self.own_secret)

    @staticmethod
    def craft_load(_load):
        load = _load.expose_to_dict()

        craft = f'''\
            {load['stages']['start']} ... {load['stages']['finish']}
            {_load.driver['name']}, +{_load.driver['num']}
            
            Stage: {load['stage']} ({load['last_update']})'''

        keyboard = {
            'external': [
                [InlineKeyboardButton("Set Start", callback_data=f'set_start:{_load.id}'),
                 InlineKeyboardButton("Set Engage", callback_data=f'set_engage:{_load.id}'),
                 InlineKeyboardButton("Set Drive", callback_data=f'set_drive:{_load.id}')],
                [InlineKeyboardButton("Set Clear", callback_data=f'set_clear:{_load.id}'),
                 InlineKeyboardButton("Set Finish", callback_data=f'set_finish:{_load.id}'),
                 InlineKeyboardButton("Delete", callback_data=f'delete:{_load.id}')]
            ],
            'internal': [
                [InlineKeyboardButton("Set Start", callback_data=f'set_start:{_load.id}'),
                 InlineKeyboardButton("Set Drive", callback_data=f'set_drive:{_load.id}')],
                [InlineKeyboardButton("Set Finish", callback_data=f'set_finish:{_load.id}'),
                 InlineKeyboardButton("Delete", callback_data=f'delete:{_load.id}')]
            ]
        }
        reply_markup = InlineKeyboardMarkup(keyboard[_load.type])
        return dedent(craft).lstrip(), reply_markup

    def render_load(self, load):
        _message, reply_markup = self.craft_load(load)
        time.sleep(0.1)
        self.bot.send_message(self.chat_id,
                              _message,
                              reply_markup=reply_markup,
                              parse_mode='MARKDOWN')

    def render_loads(self, loads: list, message='Total'):
        if len(loads) == 0:
            return
        for load in loads:
            self.render_load(load)
        time.sleep(0.1)
        self.bot.send_message(chat_id=self.chat_id,
                              text=f'{message}: {str(len(loads))}',
                              parse_mode='MARKDOWN')

    def create_new_load(self, _str):

        lines = _str.strip().split('\n')
        method, load_type = lines[0].split(':')
        if method != 'new':
            raise RuntimeError()
        if load_type == 'external':
            """ 0 new:external
                1 Кривой Рог
                2 Днепр
                3 Черновцы
                4 Яссы
                5
                6 Козак Григорий
                7 +380501231212
                8 
                9 Client: +380953459607"""
            start = lines[1].strip()
            engage = lines[2].strip()
            clear = lines[3].strip()
            finish = lines[4].strip()
            driver_name = lines[6].strip()
            driver_num = lines[7].strip()
            client_num = lines[9].replace('Client: ', '').strip()

            if not bool(start) \
                    or not bool(engage) \
                    or not bool(clear) \
                    or not bool(finish) \
                    or not bool(driver_name) or not bool(driver_num) \
                    or not bool(client_num):
                raise RuntimeError()

            if '+' not in driver_num or '+' not in client_num:
                raise RuntimeError()

            new_load = Load(_type=load_type, stage='history',
                            start=start, engage=engage, clear=clear, finish=finish,
                            client_num=client_num.replace('+', ''),
                            driver_name=driver_name, driver_num=driver_num.replace('+', ''))

        elif load_type == 'internal':

            start = lines[1].strip()
            finish = lines[2].strip()
            driver_name = lines[4].strip()
            driver_num = lines[5].strip()
            client_num = lines[7].replace('Client: ', '').strip()

            if not bool(start) \
                    or not bool(finish) \
                    or not bool(driver_name) or not bool(driver_num) \
                    or not bool(client_num):
                raise RuntimeError()

            if '+' not in driver_num or '+' not in client_num:
                raise RuntimeError()

            new_load = Load(_type=load_type, stage='history',
                            start=start, engage=None, clear=None, finish=finish,
                            client_num=client_num.replace('+', ''),
                            driver_name=driver_name, driver_num=driver_num.replace('+', ''))
        else:
            raise RuntimeError()

        self.loads_instance.add_load(new_load)
        return new_load

    class DialogState(ABC):

        def __init__(self):
            self.context = None

        @abstractmethod
        def on_enter(self):
            pass

        @abstractmethod
        def handle_event(self, update):
            pass

    class StandbyState(DialogState):

        def on_enter(self):

            keyboard = [
                ['Show active', 'Show deleted'],
                ['Create new']
            ]
            main_keyboard = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
            active_loads = len(self.context.loads.expose_active_loads())
            iface = self.context.interface
            iface.bot.send_message(chat_id=iface.chat_id,
                                   text=f'Active loads: {active_loads}',
                                   reply_markup=main_keyboard,
                                   parse_mode='MARKDOWN')

        def handle_event(self, update):
            loads = self.context.loads
            iface = self.context.interface
            message = update.message.text
            if message == 'Show active':
                threading.Thread(target=iface.render_loads,
                                 kwargs={'loads': loads.get_active_loads(), 'message': 'Active'}).start()
                return self

            elif message == 'Show deleted':
                threading.Thread(target=iface.render_loads,
                                 kwargs={'loads': loads.get_active_loads(), 'message': 'Deleted'}).start()
                return self

            elif message == 'Create new':
                draft_ext = '''
                    new:external
                    Полтава
                    Черновцы
                    Яссы
                    Плопени
                    
                    Козак Григорий
                    +380501231212
                    
                    Client: +380953459607
                '''
                draft_int = '''
                    new:internal
                    Днепр
                    Конотоп
                    
                    Козак Григорий
                    +380501231212
                    
                    Client: +380953459607
                '''
                iface.bot.send_message(iface.chat_id, 'Copy, edit and send back')
                iface.bot.send_message(iface.chat_id, dedent(draft_int).strip())
                iface.bot.send_message(iface.chat_id, dedent(draft_ext).strip())
                return self
            elif message == 'Craft sms':
                iface.bot.send_message(iface.chat_id, 'Not implemented')
                return self
            elif message.startswith('new:'):
                try:
                    load = iface.create_new_load(message)
                    iface.render_load(load)
                except (AttributeError, LookupError, NameError, ValueError, TypeError):
                    iface.bot.send_message(iface.chat_id, 'Try again')
            return self

    class CreateLoadState(DialogState):

        def on_enter(self):
            pass

        def handle_event(self, update):
            pass

    class CraftsmsState(DialogState):

        def on_enter(self):
            pass

        def handle_event(self, update):
            pass

    class DialogContext:
        def __init__(self, interface, loads, state):
            self.interface = interface
            self.loads = loads
            self.state = state
            self.state.context = self
            self.state.on_enter()

        def handle_event(self, update):
            new_state = self.state.handle_event(update)
            if new_state != self.state:
                self.state = new_state
                self.state.on_enter()

    def handle_cmd_start(self, update, context):

        self.dialog_context.state = self.StandbyState()
        self.dialog_context.handle_event(update)

    def handle_messages(self, update: Update, context):

        self.dialog_context.handle_event(update)

    def handle_inline_buttons(self, update, context):
        query = update.callback_query
        query.answer()
        data = query.data
        _cmd, _id = data.split(":", 1)
        load = self.loads_instance.get_load_by_id(_id)

        if _cmd == 'set_start':
            load.change_stage('start')
            _message, reply_markup = self.craft_load(load)
            query.edit_message_text(text=_message, reply_markup=reply_markup, parse_mode='MARKDOWN')
        elif _cmd == 'set_engage':
            load.change_stage('engage')
            _message, reply_markup = self.craft_load(load)
            query.edit_message_text(text=_message, reply_markup=reply_markup, parse_mode='MARKDOWN')
        elif _cmd == 'set_drive':
            load.change_stage('drive')
            _message, reply_markup = self.craft_load(load)
            query.edit_message_text(text=_message, reply_markup=reply_markup, parse_mode='MARKDOWN')
        elif _cmd == 'set_clear':
            load.change_stage('clear')
            _message, reply_markup = self.craft_load(load)
            query.edit_message_text(text=_message, reply_markup=reply_markup, parse_mode='MARKDOWN')
        elif _cmd == 'set_finish':
            load.change_stage('finish')
            _message, reply_markup = self.craft_load(load)
            query.edit_message_text(text=_message, reply_markup=reply_markup, parse_mode='MARKDOWN')
        elif _cmd == 'delete':
            load.change_stage('history')
            query.edit_message_text(text=f"Deleted")
        else:
            pass

    def catch_webhook(self, _json):

        update = Update.de_json(_json, self.bot)
        self.dispatcher.process_update(update)
