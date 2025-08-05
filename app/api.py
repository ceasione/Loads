
import asyncio
from contextlib import asynccontextmanager
from fastapi import HTTPException
from fastapi import FastAPI, Request
from pyngrok import ngrok
from typing import Optional, cast
from app import tg_interface
from app.loads import Loads, Load
from telegram.ext import Application
from app import settings


DEBUG = True
DEBUG_URL = 'http://localhost:8000'
PROD_URL = 'http://localhost:8000'
TELEGRAM_WEBHOOK_ENDPOINT = '/tg_wh'


def setup_ngrok(local_url: str) -> str:
    """
    Set up a tunnel and extract public url from it
    """
    tunnel = ngrok.connect(local_url)
    return tunnel.public_url


@asynccontextmanager
async def lifespan(app: FastAPI):
    if DEBUG:
        public_url = setup_ngrok(DEBUG_URL)
    else:
        public_url = PROD_URL

    tg_if = await tg_interface.build(
        token=settings.TG_API_TOKEN,
        webhook_url=public_url+TELEGRAM_WEBHOOK_ENDPOINT
    )
    app.state.tg_if = tg_if

    loads = Loads.from_file_storage(settings.LOADS_NOSQL_LOC)
    app.state.loads = loads

    yield

    await tg_interface.destroy(tg_if)


app = FastAPI(lifespan=lifespan)


def _gen_response3(
        *,
        json_status: str,
        message: str = None,
        workload=None) -> dict:

    return {'status': json_status,
            'message': message,
            'workload': workload}


@app.post(TELEGRAM_WEBHOOK_ENDPOINT)
async def process_tg_webhook(request: Request):
    data = await request.json()
    tg_if = cast(Application, request.app.state.tg_if)
    await tg_interface.webhook_entrypoint(data, tg_if)
    return {'status': 'ok'}


@app.get('/s3/loads')
async def get_loads(request: Request):
    loads = cast(Loads, request.app.state.loads)
    active = loads.expose_active_loads()
    return _gen_response3(
        json_status='success',
        workload={'len': len(active), 'loads': active}
    )


@app.get('/s3/driver')
async def get_driver(load_id: str, auth_num: str, request: Request):
    # /driver?load_id=4214&auth_num=470129384701
    loads = cast(Loads, request.app.state.loads)
    await asyncio.sleep(2)  # Bruteforce defense
    try:
        driver, js_status, http_status = loads.get_load_by_id(load_id).get_driver_details(auth_num)
        return _gen_response3(
            json_status=js_status,
            message=None,
            workload=driver)
    except Load.NoSuchLoadID:
        raise HTTPException(status_code=400, detail='Wrong load ID')


