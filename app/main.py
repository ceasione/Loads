from flask import Flask
from flask import request
import json
from flask import Response
from flask_cors import CORS
from app.lib.apis import telegramapi2
from app.lib.loads.loads import Loads
from app.lib.loads.interface import TelegramInterface
from app import settings

"""
pip install Flask
pip install flask-cors
pip install urllib3==1.26.16
pip install python-telegram-bot==13.15
pip install pyngrok
pip install requests
"""

app = Flask(__name__)
CORS = CORS(app)


LOADS = Loads.from_file_storage(settings.LOADS_NOSQL_LOC)

if settings.isDeveloperPC:
    from pyngrok import ngrok
    tunnel = ngrok.connect('http://localhost:5000')
    INTERFACE = TelegramInterface(loads=LOADS,
                                  webhook_url=f'{tunnel.public_url}{settings.DEFAULT_WEBHOOK}',
                                  chat_id=settings.TELEGRAM_DEVELOPER_CHAT_ID)
else:
    INTERFACE = TelegramInterface(loads=LOADS)


def __gen_response2(http_status: int, json_status: str, message: str = None, workload=None) -> Response:
    resp = Response(response=json.dumps({'status': json_status,
                                         'message': message,
                                         'workload': workload},
                                        ensure_ascii=False),
                    status=http_status,
                    content_type='application/json; charset=utf-8')

    resp.headers.add('Access-Control-Allow-Origin', '*')
    return resp


@app.route('/s2/loads/', methods=['GET'])
def get_loads():
    _loads = LOADS.expose_active_loads()
    return __gen_response2(http_status=200, json_status='success', workload={'len': len(_loads), 'loads': _loads})


@app.route('/s2/driver/', methods=['GET'])
def get_driver():
    # /driver?load_id=4214$auth_num=470129384701
    load_id = request.args.get('load_id')
    auth_num = request.args.get('auth_num')
    if not load_id or auth_num:
        __gen_response2(http_status=400, json_status='error', message='load_id and client_num are required')

    from app.lib.loads.loads import Load
    try:
        driver, js_status, http_status = LOADS.get_load_by_id(load_id).get_driver_details(auth_num)
        return __gen_response2(http_status, js_status, workload=driver)
    except Load.NoSuchLoadID:
        return __gen_response2(400, 'No such load ID')


@app.route(settings.DEFAULT_WEBHOOK, methods=['POST'])
def loads_webhook():
    own_secret = INTERFACE.own_secret
    got_secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
    if got_secret != own_secret:
        return "Forbidden", 403
    INTERFACE.catch_webhook(request.get_json())
    return "OK", 200


# This route is designed to be easily triggered from a mobile device,
# often via a simple browser request (e.g., URL typed into browser or QR code scan).
# Using GET allows for maximum accessibility without requiring a dedicated client or POST tooling.
# https://api.intersmartgroup.com/webhook_reset/?token=WEBHOOK_RESET_SECRET_TOKEN
@app.route('/s2/webhook_reset/', methods=['GET'])
def webhook_reset():
    global INTERFACE
    try:
        if request.args.get('token') != settings.WEBHOOK_RESET_SECRET_TOKEN:
            return "Unauthorized", 403
        INTERFACE = TelegramInterface(loads=LOADS)
        return "DONE", 200
    except Exception as e:
        return f'FAIL: {e}', 500


@app.errorhandler(Exception)
def handle_exception(e):
    telegramapi2.send_developer(f'Exception escape', e)
    return __gen_response2(http_status=500,
                           json_status='Internal error, see logs',
                           message='Exception escape',
                           workload=None)


def create_app():
    return app


if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)
