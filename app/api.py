
import asyncio
from contextlib import asynccontextmanager
from fastapi import HTTPException
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.tg_interface.interface import AsyncTelegramInterface
from app.loads.loads import Loads
from app import settings
from app.logger import api_logger


def setup_ngrok(local_url: str) -> str:
    """
    Set up a tunnel and extract public url from it
    """
    api_logger.info(f"Setting up ngrok tunnel for {local_url}")
    try:
        from pyngrok import ngrok
        tunnel = ngrok.connect(local_url)
        api_logger.info(f"Ngrok tunnel established: {tunnel.public_url}")
        return tunnel.public_url
    except Exception as e:
        api_logger.error(f"Failed to setup ngrok tunnel: {e}")
        raise


def get_public_url(local_mode_on: bool) -> str:
    """
    Get the appropriate public URL for the application.

    Args:
        local_mode_on: If True, sets up ngrok tunnel for local development.
                      If False, returns production host URL.

    Returns:
        str: Public URL that can be used to access the application.
    """
    api_logger.info(f"Getting public URL - local mode: {local_mode_on}")
    if local_mode_on:
        return setup_ngrok(settings.LOCALHOST)
    else:
        api_logger.info(f"Using production host: {settings.PROD_HOST}")
        return settings.PROD_HOST


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
    api_logger.info("Starting application lifespan")

    try:
        public_url = get_public_url(settings.IS_LOCALHOST)
        webhook_url = public_url + settings.TG_WEBHOOK_ENDPOINT
        api_logger.info(f"Webhook URL configured: {webhook_url}")

        # Initialize resources
        api_logger.info("Initializing database connection")
        async with Loads(
                db_host = settings.DB_HOST,
                db_port = settings.DB_PORT,
                db_name = settings.DB_NAME,
                db_user = settings.DB_USER,
                db_password = settings.DB_PASSWORD
        ) as loads:
            api_logger.info("Database connection established")

            api_logger.info("Initializing Telegram interface")
            async with AsyncTelegramInterface(
                    token=settings.TG_API_TOKEN,
                    webhook_url=webhook_url,
                    chat_id=settings.TELEGRAM_LOADS_CHAT_ID,
                    loads=loads) as tg_if:

                api_logger.info("Telegram interface initialized")
                application.state.tg_if = tg_if
                application.state.loads = loads

                api_logger.info("Application startup completed successfully")
                # Yielding control
                yield

        api_logger.info("Application shutdown completed")
    except Exception as e:
        api_logger.error(f"Application startup failed: {e}")
        raise

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
    api_logger.debug("Received Telegram webhook request")

    try:
        tg_if: AsyncTelegramInterface = request.app.state.tg_if
        got_secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token")

        if got_secret != tg_if.own_secret:
            api_logger.warning("Invalid webhook secret token received")
            raise HTTPException(403, 'Forbidden')

        api_logger.debug("Webhook authentication successful")
        data = await request.json()
        api_logger.debug(f"Processing webhook data: {data.get('update_id', 'unknown')}")

        await tg_if.webhook_entrypoint(data)
        api_logger.debug("Webhook processed successfully")
        return {'status': 'ok'}
    except Exception as e:
        api_logger.error(f"Error processing webhook: {e}")
        raise


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
    api_logger.info("Retrieving active loads")

    try:
        loads: Loads = request.app.state.loads
        active_loads_objects = await loads.get_actives()
        active_loads = [load.safe_dump() for load in active_loads_objects]

        api_logger.info(f"Retrieved {len(active_loads)} active loads")
        return _gen_response3(
            json_status='success',
            workload={'len': len(active_loads), 'loads': active_loads}
        )
    except Exception as e:
        api_logger.error(f"Error retrieving active loads: {e}")
        raise e


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
    # /driver?load_id=683cd668819d85b045d7085283aa3b77&auth_num=380951234567
    api_logger.info(f"Driver info request for load {load_id}... with auth {auth_num}...")

    try:
        loads: Loads = request.app.state.loads

        # Start load fetch asynchronously
        delayed_fetch = asyncio.create_task(loads.get_load_by_id(load_id))

        # Brute force protection delay
        api_logger.debug("Applying brute force protection delay")
        await asyncio.sleep(2)

        load = await delayed_fetch
        if load is None:
            api_logger.warning(f"Load not found: {load_id}")
            raise HTTPException(status_code=400, detail='Wrong load ID')

        api_logger.debug(f"Load found: {load.load_id}...")

        if load.client_num != auth_num:
            api_logger.warning(f"Authentication failed for load {load_id}... with auth {auth_num}...")
            raise HTTPException(
                401,
                detail=_gen_response3(
                    json_status='client match fail',
                    message=None,
                    workload={}
                )
            )

        api_logger.info(f"Driver info successfully retrieved for load {load_id}...")
        return _gen_response3(
            json_status='success',
            message=None,
            workload={
                'driver_name': load.driver_name,
                'driver_num': load.driver_num
            }
        )
    except HTTPException as e:
        api_logger.error(f"Error retrieving driver info: {e}")
        raise e

