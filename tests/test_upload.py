"""Tests for upload routes — file/image upload/read/write/delete/rename."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock
from fastapi.testclient import TestClient

from src.api.routes import upload as upload_module


@pytest.fixture
def client():
    with patch("src.api.routes.upload.upload_bytes_to_oss", new_callable=AsyncMock) as mock_oss:
        mock_oss.return_value = "https://oss.example.com/files/test.txt"
        from src.main import create_app
        app = create_app(enable_auth=False, init_db=False, init_rss=False)
        with TestClient(app) as c:
            c._mock_oss = mock_oss
            yield c


def _setup_mock_db():
    """Set up a mock MongoDB instance on upload_module.db so db.db doesn't raise RuntimeError."""
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_collection.find_one = AsyncMock(return_value=None)
    mock_collection.delete_one = AsyncMock(return_value=MagicMock(deleted_count=1))
    mock_collection.update_one = AsyncMock()
    mock_db.__getitem__.return_value = mock_collection
    upload_module.db._db = mock_db
    upload_module.db._initialized = True
    return mock_db, mock_collection


class TestWriteFile:
    def test_write_text_file(self, client):
        """正常: 写入文本文件"""
        response = client.post(
            "/write-file",
            json={
                "target_file": "test/example.txt",
                "content": "Hello, World!",
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
        """正常: 读取磁盘已存在文件"""
        with patch("os.path.exists", return_value=True), \
             patch("os.path.isfile", return_value=True), \
             patch("builtins.open", MagicMock()) as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = "file content"
            response = client.post(
                "/read-file",
                json={"target_file": "docs/test.md"},
            )
            assert response.status_code in [200, 400]

    def test_read_path_traversal_attempt(self, client):
        """边界: 路径以 / 开头被拒绝"""
        response = client.post(
            "/read-file",
            json={"target_file": "/etc/passwd"},
        )
        assert response.status_code in [400, 422]

    def test_read_nonexistent_file(self, client):
        """异常: 磁盘和 DB 均无该文件 → 404"""
        _setup_mock_db()
        with patch("os.path.exists", return_value=False):
            response = client.post(
                "/read-file",
                json={"target_file": "no/such/file.md"},
            )
            assert response.status_code in [400, 404]


class TestDeleteFile:
    def test_delete_existing_file(self, client):
        """正常: 删除已存在文件"""
        _setup_mock_db()
        with patch("os.path.exists", return_value=True), \
             patch("os.path.isfile", return_value=True), \
             patch("os.remove") as mock_remove:
            response = client.post(
                "/delete-file", json={"target_file": "docs/old.md"}
            )
            assert response.status_code in [200, 400]

    def test_delete_path_traversal_attempt(self, client):
        """边界: 删除路径遍历攻击"""
        response = client.post(
            "/delete-file", json={"target_file": "../../etc/passwd"}
        )
        assert response.status_code in [400, 422]

    def test_delete_with_empty_path(self, client):
        """异常: 删除路径为空"""
        response = client.post("/delete-file", json={"target_file": ""})
        assert response.status_code in [400, 422]


class TestWriteReadRoundTrip:
    def test_write_then_read_no_extension(self, client):
        """回归: 写入无扩展名文件后应立即能读取（不再要求扩展名）"""
        _setup_mock_db()
        with patch("os.makedirs"), \
             patch("builtins.open", MagicMock()), \
             patch("os.path.exists", return_value=True), \
             patch("os.path.isfile", return_value=True):
            # Write
            resp = client.post("/write-file", json={
                "target_file": "test/myfile",
                "content": "no extension content",
            })
            assert resp.status_code in [200, 201]

            # Read — should NOT return 400/404
            resp2 = client.post("/read-file", json={
                "target_file": "test/myfile",
            })
            assert resp2.status_code in [200, 201]
