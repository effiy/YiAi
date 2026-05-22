"""Tests for services/rss/feed_service.py — RSS feed fetching and parsing."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


def _make_async_iter(items):
    """Create a proper async iterator from a list of items."""
    async def _iter():
        for item in items:
            yield item
    return _iter()


class TestFetchRssFeed:
    @pytest.mark.asyncio
    async def test_fetch_valid_rss_feed(self):
        """正常: 获取并解析 RSS 源"""
        from services.rss.feed_service import fetch_rss_feed

        with patch("aiohttp.ClientSession.get") as mock_get, \
             patch("feedparser.parse") as mock_parse:

            mock_resp = AsyncMock()
            mock_resp.status = 200
            mock_resp.headers = {}
            mock_resp.content.iter_chunked = MagicMock(return_value=_make_async_iter([b"<rss>...</rss>"]))
            mock_get.return_value.__aenter__ = AsyncMock(return_value=mock_resp)

            mock_feed = MagicMock()
            mock_feed.entries = []
            mock_parse.return_value = mock_feed

            result = await fetch_rss_feed("https://example.com/feed.xml")
            assert result is not None

    @pytest.mark.asyncio
    async def test_fetch_rss_http_error(self):
        """异常: HTTP 状态码非 200"""
        from services.rss.feed_service import fetch_rss_feed
        from core.exceptions import BusinessException

        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_resp = AsyncMock()
            mock_resp.status = 404
            mock_resp.headers = {}
            mock_get.return_value.__aenter__ = AsyncMock(return_value=mock_resp)

            with pytest.raises(BusinessException):
                await fetch_rss_feed("https://example.com/not-found.xml")

    @pytest.mark.asyncio
    async def test_fetch_rss_content_too_large(self):
        """异常: Content-Length 超过限制"""
        from services.rss.feed_service import fetch_rss_feed
        from core.exceptions import BusinessException

        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_resp = AsyncMock()
            mock_resp.status = 200
            mock_resp.headers = {"Content-Length": "20971520"}
            mock_get.return_value.__aenter__ = AsyncMock(return_value=mock_resp)

            with pytest.raises(BusinessException):
                await fetch_rss_feed("https://example.com/huge.xml")

    @pytest.mark.asyncio
    async def test_fetch_rss_no_content_length(self):
        """边界: 无 Content-Length 头，正常获取"""
        from services.rss.feed_service import fetch_rss_feed

        with patch("aiohttp.ClientSession.get") as mock_get, \
             patch("feedparser.parse") as mock_parse:
            mock_resp = AsyncMock()
            mock_resp.status = 200
            mock_resp.headers = {}
            mock_resp.content.iter_chunked = MagicMock(return_value=_make_async_iter([b"<rss>data</rss>"]))
            mock_get.return_value.__aenter__ = AsyncMock(return_value=mock_resp)

            mock_feed = MagicMock()
            mock_feed.entries = []
            mock_parse.return_value = mock_feed

            result = await fetch_rss_feed("https://example.com/feed.xml")
            assert result is not None

    @pytest.mark.asyncio
    async def test_fetch_rss_network_error(self):
        """异常: 网络错误"""
        from services.rss.feed_service import fetch_rss_feed
        from core.exceptions import BusinessException

        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_get.side_effect = Exception("Network error")

            with pytest.raises(BusinessException):
                await fetch_rss_feed("https://invalid.example.com/feed.xml")

    @pytest.mark.asyncio
    async def test_fetch_rss_with_timeout(self):
        """边界: 超时参数"""
        from services.rss.feed_service import fetch_rss_feed

        with patch("aiohttp.ClientSession.get") as mock_get, \
             patch("feedparser.parse") as mock_parse:
            mock_resp = AsyncMock()
            mock_resp.status = 200
            mock_resp.headers = {}
            mock_resp.content.iter_chunked = MagicMock(return_value=_make_async_iter([b"<rss>data</rss>"]))
            mock_get.return_value.__aenter__ = AsyncMock(return_value=mock_resp)

            mock_parse.return_value = MagicMock(entries=[])

            result = await fetch_rss_feed("https://example.com/feed.xml")
            assert result is not None
