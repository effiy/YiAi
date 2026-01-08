from typing import Dict, Any
import base64
import logging
from playwright.async_api import async_playwright, Browser, Page
from core.settings import settings

logger = logging.getLogger(__name__)

async def _get_browser(p):
    """获取浏览器实例：优先尝试连接远程，失败则启动本地实例"""
    # 注意：Playwright 的上下文管理通常在外部处理，这里我们需要传递 playwright 对象 p
    
    if settings.puppeteer_browser_url:
        try:
            logger.info(f"正在连接远程浏览器 (CDP): {settings.puppeteer_browser_url}")
            # 尝试使用 CDP 连接
            return await p.chromium.connect_over_cdp(settings.puppeteer_browser_url)
        except Exception as e:
            logger.warning(f"无法连接到远程浏览器: {str(e)}，尝试启动本地浏览器...")
    
    logger.info("启动本地浏览器实例...")
    return await p.chromium.launch(
        headless=True,
        args=['--no-sandbox', '--disable-setuid-sandbox']
    )

async def _setup_page(browser: Browser) -> Page:
    """创建并配置新页面"""
    context = await browser.new_context(
        viewport={
            'width': settings.puppeteer_viewport_width,
            'height': settings.puppeteer_viewport_height
        },
        device_scale_factor=settings.puppeteer_device_scale_factor
    )
    page = await context.new_page()
    return page

async def _execute_with_browser(callback):
    """浏览器执行上下文包装器"""
    async with async_playwright() as p:
        browser = await _get_browser(p)
        try:
            page = await _setup_page(browser)
            try:
                return await callback(page)
            finally:
                await page.close()
        finally:
            # 如果是 connect_over_cdp 获取的 browser，close 会断开连接而不是关闭浏览器
            # 如果是 launch 获取的，close 会关闭浏览器进程
            await browser.close()

async def open_page(params: Dict[str, Any]) -> str:
    """
    打开指定页面（仅用于测试连接和页面加载）
    
    Args:
        params: 包含 url 等参数的字典
            - url (str): 目标页面 URL
            
    Returns:
        str: 页面标题
    """
    url = params.get("url")
    if not url:
        raise ValueError("URL is required")

    async def _action(page):
        await page.goto(url)
        title = await page.title()
        return f"Successfully opened: {title}"

    return await _execute_with_browser(_action)

async def take_screenshot(params: Dict[str, Any]) -> Dict[str, str]:
    """
    截取页面截图
    
    Args:
        params:
            - url (str): 目标页面 URL
            - full_page (bool): 是否截取全屏，默认 False
            
    Returns:
        Dict: 包含 base64 编码的截图数据
    """
    url = params.get("url")
    full_page = params.get("full_page", False)
    
    if not url:
        raise ValueError("URL is required")

    async def _action(page):
        await page.goto(url)
        screenshot_bytes = await page.screenshot(full_page=full_page)
        return {'image_base64': base64.b64encode(screenshot_bytes).decode('utf-8')}

    return await _execute_with_browser(_action)

async def get_html_content(params: Dict[str, Any]) -> Dict[str, str]:
    """
    获取页面 HTML 内容
    
    Args:
        params:
            - url (str): 目标页面 URL
            
    Returns:
        Dict: 包含 html 内容
    """
    url = params.get("url")
    if not url:
        raise ValueError("URL is required")

    async def _action(page):
        await page.goto(url)
        content = await page.content()
        return {'html': content}

    return await _execute_with_browser(_action)
