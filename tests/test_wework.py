"""Tests for WeChat Work webhook message sending route."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from src.main import create_app
    app = create_app(enable_auth=False, init_db=False, init_rss=False)
    with TestClient(app) as c:
        yield c


VALID_URL = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=test"


class TestSendWeworkMessage:
    def test_send_valid_message(self, client):
        """正常: 发送合法 webhook 消息"""
        with patch("aiohttp.ClientSession.post") as mock_post:
            mock_resp = AsyncMock()
            mock_resp.status = 200
            mock_resp.json = AsyncMock(return_value={"errcode": 0, "errmsg": "ok"})
            mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
            mock_post.return_value = mock_resp

            response = client.post(
                "/wework/send-message",
                json={"webhook_url": VALID_URL, "content": "hello from test"},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 0

    def test_send_with_empty_content(self, client):
        """边界: 消息内容为空"""
        response = client.post(
            "/wework/send-message",
            json={"webhook_url": VALID_URL, "content": ""},
        )
        assert response.status_code in [400, 422]
        data = response.json()
        assert "code" in data

    def test_send_with_invalid_url_format(self, client):
        """异常: 非企业微信 URL"""
        response = client.post(
            "/wework/send-message",
            json={"webhook_url": "https://evil.com/hook", "content": "bad url"},
        )
        assert response.status_code in [400, 422]

    def test_send_with_empty_url(self, client):
        """异常: Webhook URL 为空"""
        response = client.post(
            "/wework/send-message",
            json={"webhook_url": "", "content": "test"},
        )
        assert response.status_code in [400, 422]

    def test_send_with_network_error(self, client):
        """异常: 网络错误"""
        with patch("aiohttp.ClientSession.post") as mock_post:
            mock_post.side_effect = Exception("Connection refused")
            response = client.post(
                "/wework/send-message",
                json={"webhook_url": VALID_URL, "content": "test"},
            )
            assert response.status_code in [400, 500]
