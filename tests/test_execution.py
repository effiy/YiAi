"""Tests for execution route — module execution via GET/POST with SSE streaming."""
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    mock_exec = AsyncMock()
    mock_exec.return_value = {"status": "ok", "data": {"result": "output"}}

    with patch("api.routes.execution.execute_module", mock_exec):
        from src.main import create_app
        app = create_app(enable_auth=False, init_db=False, init_rss=False)
        with TestClient(app) as c:
            c._mock_exec = mock_exec
            yield c


class TestExecutionGet:
    def test_get_with_valid_params(self, client):
        """正常: GET 执行模块"""
        client._mock_exec.return_value = {"status": "ok", "data": "done"}
        response = client.get(
            "/",
            params={
                "module_name": "services.database.data_service",
                "method_name": "query_documents",
                "parameters": json.dumps({"cname": "sessions"}),
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0

    def test_get_default_params(self, client):
        """边界: 不传参数使用默认值"""
        client._mock_exec.return_value = {"status": "ok"}
        response = client.get("/", params={
            "module_name": "svc.test",
            "method_name": "run",
        })
        assert response.status_code == 200


class TestExecutionPost:
    def test_post_with_valid_body(self, client):
        """正常: POST 执行模块"""
        client._mock_exec.return_value = {"status": "ok", "data": "post_result"}
        response = client.post(
            "/",
            json={
                "module_name": "services.ai.chat_service",
                "method_name": "chat",
                "parameters": {"message": "hello"},
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0

    def test_post_empty_params(self, client):
        """边界: 空参数字典"""
        client._mock_exec.return_value = {"status": "ok"}
        response = client.post(
            "/",
            json={
                "module_name": "services.database.data_service",
                "method_name": "query_documents",
                "parameters": {},
            },
        )
        assert response.status_code == 200

    def test_post_invalid_json(self, client):
        """异常: 非法 JSON body"""
        response = client.post(
            "/",
            content="not valid json",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code in [400, 422]
