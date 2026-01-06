from typing import List, Dict
from pyppeteer import connect
from core.config import settings

async def open_page(params: Dict[str, any]) -> List[Dict[str, str]]:
    """
    Puppeteer 控制脚本入口
    
    Args:
        params: 包含 url 等参数的字典
            - url (str): 目标页面 URL
            
    Returns:
        List[Dict[str, str]]: 处理结果列表 (目前返回空字符串)

    Example:
        GET /?module_name=services.web.puppeteer.browser_service&method_name=open_page&parameters={"url": "https://www.google.com"}
    """
    url = params.get("url")

    # 连接到已经启动的远程浏览器
    browser = await connect({
        'browserURL': settings.puppeteer_browser_url
    })

    page = await browser.newPage()

    # 设置视口
    await page.setViewport({
        'width': settings.puppeteer_viewport_width,
        'height': settings.puppeteer_viewport_height,
        'deviceScaleFactor': settings.puppeteer_device_scale_factor
    })

    # 跳转到目标页面
    await page.goto(url)

    return ''

# 运行 asyncio 程序
# asyncio.get_event_loop().run_until_complete(main())

