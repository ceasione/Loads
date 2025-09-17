import pytest
from unittest.mock import patch, MagicMock
from app.api import setup_ngrok, get_public_url


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