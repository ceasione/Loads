
import asyncio
from contextlib import asynccontextmanager
from fastapi import HTTPException
from fastapi import FastAPI, Request
from pyngrok import ngrok
from typing import Optional, cast
from app.tg_interface import AsyncTelegramInterface
from app.loads import Loads, Load
from telegram.ext import Application
from app import settings


DEBUG_URL = 'http://localhost:8000'
PROD_URL = 'http://localhost:8000'


def setup_ngrok(local_url: str) -> str:
    """
    Set up a tunnel and extract public url from it
    """
    tunnel = ngrok.connect(local_url)
    return tunnel.public_url


def get_public_url(debug_mode_on: bool) -> str:
    if debug_mode_on:
        return setup_ngrok(DEBUG_URL)
    else:
        return PROD_URL


@asynccontextmanager
async def lifespan(app_: FastAPI):

    public_url = get_public_url(settings.DEBUG)

    # Initialize sync resources
    loads = Loads.from_file_storage(settings.LOADS_NOSQL_LOC)
    app_.state.loads = loads

    # Initialize async resources
    async with AsyncTelegramInterface(
            token=settings.TG_API_TOKEN,
            webhook_url=public_url+settings.TG_WEBHOOK_ENDPOINT) as tg_if:
        app_.state.tg_if = tg_if
        # Yielding control
        yield

    # No need to clean up for now

app = FastAPI(lifespan=lifespan)


def _gen_response3(
        *,
        json_status: str,
        message: str = None,
        workload=None) -> dict:

    return {'status': json_status,
            'message': message,
            'workload': workload}


@app.post(settings.TG_WEBHOOK_ENDPOINT)
async def process_tg_webhook(request: Request):
    data = await request.json()
    tg_if = cast(AsyncTelegramInterface, request.app.state.tg_if)
    await tg_if.webhook_entrypoint(data)
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


