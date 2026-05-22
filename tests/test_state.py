"""Tests for state routes — CRUD operations on state records (prefix=/state)."""
import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    mock_svc = AsyncMock()
    mock_svc.create = AsyncMock(return_value={
        "_id": "test-id-001", "key": "test-key",
        "record_type": "log", "tags": ["test"], "title": "Test",
    })
    mock_svc.query = AsyncMock(return_value={
        "items": [], "total": 0, "page_num": 1, "page_size": 10,
    })

    with patch("api.routes.state.StateStoreService", return_value=mock_svc):
        from src.main import create_app
        app = create_app(enable_auth=False, init_db=False, init_rss=False)
        with TestClient(app) as c:
            yield c


class TestCreateRecord:
    def test_create_valid_record(self, client):
        """正常: 创建状态记录"""
        response = client.post(
            "/state/records",
            json={
                "key": "test-key",
                "record_type": "log",
                "tags": ["test", "demo"],
                "title": "Test Record",
                "data": {"extra": "value"},
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["code"] == 0

    def test_create_minimal_record(self, client):
        """边界: 最小字段"""
        response = client.post(
            "/state/records",
            json={"record_type": "note", "title": "Minimal"},
        )
        assert response.status_code == 201

    def test_create_without_record_type(self, client):
        """异常: 缺少必填字段 record_type"""
        response = client.post(
            "/state/records",
            json={"title": "No Type"},
        )
        assert response.status_code == 400


class TestQueryRecords:
    def test_query_default(self, client):
        """正常: 默认查询"""
        response = client.get("/state/records")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0

    def test_query_with_filters(self, client):
        """边界: 带过滤条件"""
        response = client.get(
            "/state/records",
            params={"record_type": "log", "tags": ["test"], "page_num": 1, "page_size": 5},
        )
        assert response.status_code == 200

    def test_query_invalid_page_size(self, client):
        """异常: 超出范围的分页"""
        response = client.get("/state/records", params={"page_size": 99999})
        assert response.status_code in [400, 422]
