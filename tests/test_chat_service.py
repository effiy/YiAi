"""Tests for services/ai/chat_service.py — text extraction, image URL detection, message building."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


def _make_async_iter(items):
    async def _iter():
        for item in items:
            yield item
    return _iter()


class TestExtractUserOnlyText:
    def test_extract_marker_section(self):
        """正常: 提取 ## 当前消息 后的文本"""
        from services.ai.chat_service import _extract_user_only_text

        text = "前面内容\n## 当前消息\nreal message here"
        result = _extract_user_only_text(text)
        assert result == "real message here"

    def test_extract_marker_with_hash_prefix(self):
        """正常: ## 当前消息 后跟 ## 开头的内容"""
        from services.ai.chat_service import _extract_user_only_text

        text = "## 当前消息\n## 当前消息\nimportant content"
        result = _extract_user_only_text(text)
        assert result == "important content"

    def test_extract_empty_string(self):
        """边界: 空字符串"""
        from services.ai.chat_service import _extract_user_only_text
        assert _extract_user_only_text("") == ""

    def test_extract_none(self):
        """边界: None 输入"""
        from services.ai.chat_service import _extract_user_only_text
        assert _extract_user_only_text(None) == ""

    def test_extract_without_marker(self):
        """边界: 不含 marker 的文本，原样返回"""
        from services.ai.chat_service import _extract_user_only_text
        text = "plain text without marker"
        result = _extract_user_only_text(text)
        assert result == text


class TestIsHttpUrl:
    def test_https_url_returns_true(self):
        """正常: HTTPS URL"""
        from services.ai.chat_service import _is_http_url
        assert _is_http_url("https://example.com/image.png") is True

    def test_http_url_returns_true(self):
        """正常: HTTP URL"""
        from services.ai.chat_service import _is_http_url
        assert _is_http_url("http://example.com/image.png") is True

    def test_relative_path_returns_false(self):
        """正常: 相对路径不是 URL"""
        from services.ai.chat_service import _is_http_url
        assert _is_http_url("images/photo.png") is False

    def test_empty_string_returns_false(self):
        """边界: 空字符串"""
        from services.ai.chat_service import _is_http_url
        assert _is_http_url("") is False

    def test_none_returns_false(self):
        """边界: None 输入"""
        from services.ai.chat_service import _is_http_url
        assert _is_http_url(None) is False


class TestFetchImageBytes:
    @pytest.mark.asyncio
    async def test_fetch_valid_image(self):
        """正常: 获取图片字节"""
        from services.ai.chat_service import _fetch_image_bytes

        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_resp = AsyncMock()
            mock_resp.status = 200
            mock_resp.headers = {"Content-Type": "image/png"}
            mock_resp.content.iter_chunked = MagicMock(
                return_value=_make_async_iter([b"PNG_DATA"])
            )
            mock_get.return_value.__aenter__ = AsyncMock(return_value=mock_resp)

            result = await _fetch_image_bytes("https://example.com/photo.png")
            assert result is not None

    @pytest.mark.asyncio
    async def test_fetch_non_image_content_type(self):
        """异常: Content-Type 不是图片"""
        from services.ai.chat_service import _fetch_image_bytes

        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_resp = AsyncMock()
            mock_resp.status = 200
            mock_resp.headers = {"Content-Type": "text/html"}
            mock_get.return_value.__aenter__ = AsyncMock(return_value=mock_resp)

            result = await _fetch_image_bytes("https://example.com/page.html")
            assert result is None

    @pytest.mark.asyncio
    async def test_fetch_http_error_status(self):
        """异常: HTTP 状态码非 2xx"""
        from services.ai.chat_service import _fetch_image_bytes

        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_resp = AsyncMock()
            mock_resp.status = 404
            mock_get.return_value.__aenter__ = AsyncMock(return_value=mock_resp)

            result = await _fetch_image_bytes("https://example.com/missing.png")
            assert result is None

    @pytest.mark.asyncio
    async def test_fetch_empty_url(self):
        """异常: 空 URL"""
        from services.ai.chat_service import _fetch_image_bytes
        result = await _fetch_image_bytes("")
        assert result is None
