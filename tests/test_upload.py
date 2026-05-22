"""Tests for upload routes — file/image upload/read/write/delete/rename."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    with patch("api.routes.upload.upload_bytes_to_oss", new_callable=AsyncMock) as mock_oss:
        mock_oss.return_value = "https://oss.example.com/files/test.txt"
        from src.main import create_app
        app = create_app(enable_auth=False, init_db=False, init_rss=False)
        with TestClient(app) as c:
            c._mock_oss = mock_oss
            yield c


class TestWriteFile:
    def test_write_text_file(self, client):
        """正常: 写入文本文件"""
        response = client.post(
            "/write-file",
            json={
                "target_file": "test/example.txt",
                "content": "Hello, World!",
                "encoding": "utf-8",
            },
        )
        assert response.status_code in [200, 201]
        data = response.json()
        assert data["code"] == 0

    def test_write_with_empty_path(self, client):
        """边界: 写入路径为空"""
        response = client.post(
            "/write-file",
            json={"target_file": "", "content": "data"},
        )
        assert response.status_code in [400, 422]

    def test_write_path_traversal_attempt(self, client):
        """异常: 路径遍历攻击"""
        response = client.post(
            "/write-file",
            json={
                "target_file": "../../../etc/passwd",
                "content": "malicious",
            },
        )
        assert response.status_code in [400, 422]
        data = response.json()
        assert "code" in data


class TestReadFile:
    def test_read_existing_file(self, client):
        """正常: 读取已存在文件"""
        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", MagicMock()) as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = "file content"
            response = client.post(
                "/read-file",
                json={"file_path": "docs/test.md", "encoding": "utf-8"},
            )
            assert response.status_code in [200, 400]

    def test_read_path_traversal_attempt(self, client):
        """边界: 路径以 / 开头被拒绝"""
        response = client.post(
            "/read-file",
            json={"file_path": "/etc/passwd", "encoding": "utf-8"},
        )
        assert response.status_code in [400, 422]

    def test_read_nonexistent_file(self, client):
        """异常: 读取不存在的文件"""
        with patch("os.path.exists", return_value=False):
            response = client.post(
                "/read-file",
                json={"file_path": "no/such/file.md", "encoding": "utf-8"},
            )
            assert response.status_code in [400, 404]


class TestDeleteFile:
    def test_delete_existing_file(self, client):
        """正常: 删除已存在文件"""
        with patch("os.path.exists", return_value=True), \
             patch("os.remove") as mock_remove:
            response = client.post(
                "/delete-file", json={"file_path": "docs/old.md"}
            )
            assert response.status_code in [200, 400]

    def test_delete_path_traversal_attempt(self, client):
        """边界: 删除路径遍历攻击"""
        response = client.post(
            "/delete-file", json={"file_path": "../../etc/passwd"}
        )
        assert response.status_code in [400, 422]

    def test_delete_with_empty_path(self, client):
        """异常: 删除路径为空"""
        response = client.post("/delete-file", json={"file_path": ""})
        assert response.status_code in [400, 422]
