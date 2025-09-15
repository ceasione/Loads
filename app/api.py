
import asyncio
from contextlib import asynccontextmanager
from fastapi import HTTPException
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pyngrok import ngrok
from typing import Optional, cast
from app.tg_interface.interface import AsyncTelegramInterface
from app.loads.loads import Loads
from app.loads.load import Load
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
    return setup_ngrok(DEBUG_URL) if debug_mode_on else PROD_URL
    # if debug_mode_on:
    #     return setup_ngrok(DEBUG_URL)
    # else:
    #     return PROD_URL


@asynccontextmanager
async def lifespan(application: FastAPI):

    public_url = get_public_url(settings.DEBUG)

    # Initialize resources
    async with Loads(settings.DB_CONNECTION_URL) as loads:

        async with AsyncTelegramInterface(
                token=settings.TG_API_TOKEN,
                webhook_url=public_url+settings.TG_WEBHOOK_ENDPOINT,
                chat_id=settings.TELEGRAM_LOADS_CHAT_ID,
                loads=loads) as tg_if:

            application.state.tg_if = tg_if
            application.state.loads = loads
            # Yielding control
            yield

    # No need to clean up after since we were at context managers

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        'http://localhost:3000',
        'https://intersmartgroup.com/'
    ]
)


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
    tg_if = cast(AsyncTelegramInterface, request.app.state.tg_if)
    got_secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
    if got_secret != tg_if.own_secret:
        raise HTTPException(403, 'Forbidden')
    data = await request.json()
    await tg_if.webhook_entrypoint(data)
    return {'status': 'ok'}


@app.get('/s3/loads')
async def get_loads(request: Request):
    loads: Loads = request.app.state.loads
    active_loads = [load.safe_dump() for load in await loads.get_actives()]
    return _gen_response3(
        json_status='success',
        workload={'len': len(active_loads), 'loads': active_loads}
    )


@app.get('/s3/driver')
async def get_driver(load_id: str, auth_num: str, request: Request):
    # /driver?load_id=699bc14e38c0b49a6947ca4854439426&auth_num=380951234567
    loads: Loads = request.app.state.loads

    delayed_fetch = asyncio.create_task(loads.get_load_by_id(load_id))

    await asyncio.sleep(2)  # Bruteforce defense

    load = await delayed_fetch
    if load is None:
        raise HTTPException(status_code=400, detail='Wrong load ID')

    if load.client_num != auth_num:
        raise HTTPException(
            401,
            detail=_gen_response3(
                json_status='client match fail',
                message=None,
                workload={}
            )
        )

    return _gen_response3(
        json_status='success',
        message=None,
        workload={
            'driver_name':load.driver_name,
            'driver_num':load.driver_num
        }
    )
