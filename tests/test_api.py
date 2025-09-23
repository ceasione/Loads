import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi import HTTPException
from fastapi.testclient import TestClient
from app.api import setup_ngrok, get_public_url, _gen_response3, app

@pytest.mark.skip
class TestSetupNgrok:

    @patch('app.api.ngrok.connect')
    def test_setup_ngrok_returns_public_url(self, mock_connect):
        mock_tunnel = MagicMock()
        mock_tunnel.public_url = "https://abcd1234.ngrok.io"
        mock_connect.return_value = mock_tunnel

        result = setup_ngrok("http://localhost:8000")

        mock_connect.assert_called_once_with("http://localhost:8000")
        assert result == "https://abcd1234.ngrok.io"

    @patch('app.api.ngrok.connect')
    def test_setup_ngrok_with_different_local_url(self, mock_connect):
        mock_tunnel = MagicMock()
        mock_tunnel.public_url = "https://xyz9876.ngrok.io"
        mock_connect.return_value = mock_tunnel

        result = setup_ngrok("http://localhost:3000")

        mock_connect.assert_called_once_with("http://localhost:3000")
        assert result == "https://xyz9876.ngrok.io"

    @patch('app.api.ngrok.connect')
    def test_setup_ngrok_handles_ngrok_exception(self, mock_connect):
        mock_connect.side_effect = Exception("Ngrok connection failed")

        with pytest.raises(Exception, match="Ngrok connection failed"):
            setup_ngrok("http://localhost:8000")


class TestGetPublicUrl:

    @patch('app.api.setup_ngrok')
    @patch('app.api.settings')
    def test_get_public_url_local_mode_true(self, mock_settings, mock_setup_ngrok):
        mock_settings.LOCALHOST = "http://localhost:8000"
        mock_setup_ngrok.return_value = "https://test123.ngrok.io"

        result = get_public_url(local_mode_on=True)

        mock_setup_ngrok.assert_called_once_with("http://localhost:8000")
        assert result == "https://test123.ngrok.io"

    @patch('app.api.setup_ngrok')
    @patch('app.api.settings')
    def test_get_public_url_local_mode_false(self, mock_settings, mock_setup_ngrok):
        mock_settings.PROD_HOST = "https://api.intersmartgroup.com"

        result = get_public_url(local_mode_on=False)

        mock_setup_ngrok.assert_not_called()
        assert result == "https://api.intersmartgroup.com"

    @patch('app.api.setup_ngrok')
    @patch('app.api.settings')
    def test_get_public_url_with_different_localhost(self, mock_settings, mock_setup_ngrok):
        mock_settings.LOCALHOST = "http://localhost:3000"
        mock_setup_ngrok.return_value = "https://different456.ngrok.io"

        result = get_public_url(local_mode_on=True)

        mock_setup_ngrok.assert_called_once_with("http://localhost:3000")
        assert result == "https://different456.ngrok.io"

    @patch('app.api.setup_ngrok')
    @patch('app.api.settings')
    def test_get_public_url_with_different_prod_host(self, mock_settings, mock_setup_ngrok):
        mock_settings.PROD_HOST = "https://production.example.com"

        result = get_public_url(local_mode_on=False)

        mock_setup_ngrok.assert_not_called()
        assert result == "https://production.example.com"

    @patch('app.api.setup_ngrok')
    @patch('app.api.settings')
    def test_get_public_url_setup_ngrok_failure(self, mock_settings, mock_setup_ngrok):
        mock_settings.LOCALHOST = "http://localhost:8000"
        mock_setup_ngrok.side_effect = Exception("Ngrok setup failed")

        with pytest.raises(Exception, match="Ngrok setup failed"):
            get_public_url(local_mode_on=True)

@pytest.mark.skip
@pytest.mark.integration
class TestIntegration:

    @patch('app.api.ngrok.connect')
    @patch('app.api.settings')
    def test_full_flow_local_mode(self, mock_settings, mock_connect):
        mock_settings.LOCALHOST = "http://localhost:8000"
        mock_tunnel = MagicMock()
        mock_tunnel.public_url = "https://integration123.ngrok.io"
        mock_connect.return_value = mock_tunnel

        result = get_public_url(local_mode_on=True)

        mock_connect.assert_called_once_with("http://localhost:8000")
        assert result == "https://integration123.ngrok.io"

    @patch('app.api.settings')
    def test_full_flow_production_mode(self, mock_settings):
        mock_settings.PROD_HOST = "https://api.intersmartgroup.com"

        result = get_public_url(local_mode_on=False)

        assert result == "https://api.intersmartgroup.com"


class TestGenResponse3:

    def test_gen_response3_with_all_parameters(self):
        result = _gen_response3(
            json_status="success",
            message="Operation completed",
            workload={"data": "test"}
        )

        assert result == {
            'status': 'success',
            'message': 'Operation completed',
            'workload': {'data': 'test'}
        }

    def test_gen_response3_with_status_only(self):
        result = _gen_response3(json_status="error")

        assert result == {
            'status': 'error',
            'message': None,
            'workload': None
        }

    def test_gen_response3_with_status_and_message(self):
        result = _gen_response3(
            json_status="warning",
            message="This is a warning"
        )

        assert result == {
            'status': 'warning',
            'message': 'This is a warning',
            'workload': None
        }

    def test_gen_response3_with_status_and_workload(self):
        workload_data = {"loads": [], "count": 0}
        result = _gen_response3(
            json_status="success",
            workload=workload_data
        )

        assert result == {
            'status': 'success',
            'message': None,
            'workload': workload_data
        }

    def test_gen_response3_with_complex_workload(self):
        complex_workload = {
            "driver_name": "John Doe",
            "driver_num": "123456789",
            "loads": [{"id": 1}, {"id": 2}]
        }
        result = _gen_response3(
            json_status="success",
            message="Driver found",
            workload=complex_workload
        )

        assert result == {
            'status': 'success',
            'message': 'Driver found',
            'workload': complex_workload
        }


class TestProcessTgWebhook:

    @pytest.fixture
    def mock_request(self):
        request = MagicMock()
        request.app.state.tg_if = MagicMock()
        request.headers.get.return_value = "correct_secret"
        request.app.state.tg_if.own_secret = "correct_secret"
        request.json = AsyncMock(return_value={"message": "test"})
        request.app.state.tg_if.webhook_entrypoint = AsyncMock()
        return request

    @pytest.mark.asyncio
    async def test_process_tg_webhook_success(self, mock_request):
        from app.api import process_tg_webhook

        result = await process_tg_webhook(mock_request)

        mock_request.app.state.tg_if.webhook_entrypoint.assert_called_once_with({"message": "test"})
        assert result == {'status': 'ok'}

    @pytest.mark.asyncio
    async def test_process_tg_webhook_wrong_secret(self, mock_request):
        from app.api import process_tg_webhook

        mock_request.headers.get.return_value = "wrong_secret"

        with pytest.raises(HTTPException) as exc_info:
            await process_tg_webhook(mock_request)

        assert exc_info.value.status_code == 403
        assert exc_info.value.detail == 'Forbidden'

    @pytest.mark.asyncio
    async def test_process_tg_webhook_missing_secret(self, mock_request):
        from app.api import process_tg_webhook

        mock_request.headers.get.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await process_tg_webhook(mock_request)

        assert exc_info.value.status_code == 403
        assert exc_info.value.detail == 'Forbidden'

    @pytest.mark.asyncio
    async def test_process_tg_webhook_json_parsing_error(self, mock_request):
        from app.api import process_tg_webhook

        mock_request.json.side_effect = Exception("JSON parsing failed")

        with pytest.raises(Exception, match="JSON parsing failed"):
            await process_tg_webhook(mock_request)

    @pytest.mark.asyncio
    async def test_process_tg_webhook_entrypoint_error(self, mock_request):
        from app.api import process_tg_webhook

        mock_request.app.state.tg_if.webhook_entrypoint.side_effect = Exception("Webhook processing failed")

        with pytest.raises(Exception, match="Webhook processing failed"):
            await process_tg_webhook(mock_request)


class TestGetLoads:

    @pytest.fixture
    def mock_request(self):
        request = MagicMock()
        request.app.state.loads = MagicMock()
        return request

    @pytest.fixture
    def mock_load(self):
        load = MagicMock()
        load.safe_dump.return_value = {
            "id": "test_id",
            "driver_name": "John Doe",
            "status": "active"
        }
        return load

    @pytest.mark.asyncio
    async def test_get_loads_success(self, mock_request, mock_load):
        from app.api import get_loads

        mock_request.app.state.loads.get_actives = AsyncMock(return_value=[mock_load, mock_load])

        result = await get_loads(mock_request)

        expected_loads = [mock_load.safe_dump.return_value, mock_load.safe_dump.return_value]
        assert result == {
            'status': 'success',
            'message': None,
            'workload': {
                'len': 2,
                'loads': expected_loads
            }
        }

    @pytest.mark.asyncio
    async def test_get_loads_empty_result(self, mock_request):
        from app.api import get_loads

        mock_request.app.state.loads.get_actives = AsyncMock(return_value=[])

        result = await get_loads(mock_request)

        assert result == {
            'status': 'success',
            'message': None,
            'workload': {
                'len': 0,
                'loads': []
            }
        }

    @pytest.mark.asyncio
    async def test_get_loads_database_error(self, mock_request):
        from app.api import get_loads

        mock_request.app.state.loads.get_actives.side_effect = Exception("Database connection failed")

        with pytest.raises(Exception, match="Database connection failed"):
            await get_loads(mock_request)


class TestGetDriver:

    @pytest.fixture
    def mock_request(self):
        request = MagicMock()
        request.app.state.loads = MagicMock()
        return request

    @pytest.fixture
    def mock_load(self):
        load = MagicMock()
        load.client_num = "380951234567"
        load.driver_name = "John Doe"
        load.driver_num = "987654321"
        return load

    @pytest.mark.asyncio
    async def test_get_driver_success(self, mock_request, mock_load):
        from app.api import get_driver

        mock_request.app.state.loads.get_load_by_id = AsyncMock(return_value=mock_load)

        with patch('app.api.asyncio.sleep', new_callable=AsyncMock):
            result = await get_driver("test_load_id", "380951234567", mock_request)

        assert result == {
            'status': 'success',
            'message': None,
            'workload': {
                'driver_name': 'John Doe',
                'driver_num': '987654321'
            }
        }

    @pytest.mark.asyncio
    async def test_get_driver_load_not_found(self, mock_request):
        from app.api import get_driver

        mock_request.app.state.loads.get_load_by_id = AsyncMock(return_value=None)

        with patch('app.api.asyncio.sleep', new_callable=AsyncMock):
            with pytest.raises(HTTPException) as exc_info:
                await get_driver("invalid_load_id", "380951234567", mock_request)

        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == 'Wrong load ID'

    @pytest.mark.asyncio
    async def test_get_driver_auth_mismatch(self, mock_request, mock_load):
        from app.api import get_driver

        mock_load.client_num = "380951234567"
        mock_request.app.state.loads.get_load_by_id = AsyncMock(return_value=mock_load)

        with patch('app.api.asyncio.sleep', new_callable=AsyncMock):
            with pytest.raises(HTTPException) as exc_info:
                await get_driver("test_load_id", "wrong_auth_num", mock_request)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == {
            'status': 'client match fail',
            'message': None,
            'workload': {}
        }

    @pytest.mark.asyncio
    async def test_get_driver_with_delay(self, mock_request, mock_load):
        from app.api import get_driver

        mock_request.app.state.loads.get_load_by_id = AsyncMock(return_value=mock_load)

        with patch('app.api.asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
            await get_driver("test_load_id", "380951234567", mock_request)
            mock_sleep.assert_called_once_with(2)

    @pytest.mark.asyncio
    async def test_get_driver_database_error(self, mock_request):
        from app.api import get_driver

        mock_request.app.state.loads.get_load_by_id.side_effect = Exception("Database error")

        with patch('app.api.asyncio.sleep', new_callable=AsyncMock):
            with pytest.raises(Exception, match="Database error"):
                await get_driver("test_load_id", "380951234567", mock_request)

    @pytest.mark.asyncio
    async def test_get_driver_different_auth_formats(self, mock_request, mock_load):
        from app.api import get_driver

        test_cases = [
            ("380951234567", "380951234567"),
            ("+380951234567", "+380951234567"),
            ("0951234567", "0951234567")
        ]

        for client_num, auth_num in test_cases:
            mock_load.client_num = client_num
            mock_request.app.state.loads.get_load_by_id = AsyncMock(return_value=mock_load)

            with patch('app.api.asyncio.sleep', new_callable=AsyncMock):
                result = await get_driver("test_load_id", auth_num, mock_request)

                assert result['status'] == 'success'
                assert result['workload']['driver_name'] == 'John Doe'
