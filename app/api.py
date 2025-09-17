
import asyncio
from contextlib import asynccontextmanager
from fastapi import HTTPException
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pyngrok import ngrok
from app.tg_interface.interface import AsyncTelegramInterface
from app.loads.loads import Loads
from app import settings


def setup_ngrok(local_url: str) -> str:
    """
    Set up a tunnel and extract public url from it
    """
    tunnel = ngrok.connect(local_url)
    return tunnel.public_url


def get_public_url(local_mode_on: bool) -> str:
    """
    Get the appropriate public URL for the application.

    Args:
        local_mode_on: If True, sets up ngrok tunnel for local development.
                      If False, returns production host URL.

    Returns:
        str: Public URL that can be used to access the application.
    """
    return setup_ngrok(settings.LOCALHOST) if local_mode_on else settings.PROD_HOST


@asynccontextmanager
async def lifespan(application: FastAPI):
    """
    FastAPI lifespan context manager that handles application startup and shutdown.

    Initializes database connection, telegram interface, and sets up webhook URL.
    Stores initialized resources in application state for use by endpoints.

    Args:
        application: FastAPI application instance.

    Yields:
        None: Control is yielded back to FastAPI during application runtime.
    """

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
        settings.LOCALHOST,
        settings.PROD_HOST
    ]
)


def _gen_response3(
    *,
    json_status: str,
    message: str = None,
    workload=None
) -> dict:
    """
    Generate a standardized JSON response format.

    Args:
        json_status: Status of the operation (e.g., 'success', 'error').
        message: Optional message providing additional context.
        workload: Optional data payload to include in response.

    Returns:
        dict: Standardized response dictionary with status, message, and workload.
    """
    return {
        'status': json_status,
        'message': message,
        'workload': workload
    }


@app.post(settings.TG_WEBHOOK_ENDPOINT)
async def process_tg_webhook(request: Request):
    """
    Process incoming Telegram webhook requests.

    Validates the webhook secret token and forwards the update to the
    Telegram interface for processing.

    Args:
        request: FastAPI request object containing webhook data.

    Returns:
        dict: Status response indicating successful processing.

    Raises:
        HTTPException: 403 if the secret token is invalid.
    """
    tg_if: AsyncTelegramInterface = request.app.state.tg_if
    got_secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
    if got_secret != tg_if.own_secret:
        raise HTTPException(403, 'Forbidden')
    data = await request.json()
    await tg_if.webhook_entrypoint(data)
    return {'status': 'ok'}


@app.get('/s3/loads')
async def get_loads(request: Request):
    """
    Retrieve all active loads from the database.

    Returns a list of active loads with their safe dump representation
    (excluding sensitive driver and client information).

    Args:
        request: FastAPI request object to access application state.

    Returns:
        dict: Response containing count and list of active loads.
    """
    loads: Loads = request.app.state.loads
    active_loads = [load.safe_dump() for load in await loads.get_actives()]
    return _gen_response3(
        json_status='success',
        workload={'len': len(active_loads), 'loads': active_loads}
    )


@app.get('/s3/driver')
async def get_driver(load_id: str, auth_num: str, request: Request):
    """
    Retrieve driver information for a specific load.

    Implements security measures including:
    - 2-second delay for brute force protection
    - Client phone number authentication
    - Load existence validation

    Args:
        load_id: Unique identifier for the load.
        auth_num: Client phone number for authentication.
        request: FastAPI request object to access application state.

    Returns:
        dict: Response containing driver name and phone number.

    Raises:
        HTTPException: 400 if load ID is invalid, 401 if authentication fails.
    """
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
