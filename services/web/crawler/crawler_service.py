"""网页爬取与链接提取
- 使用 crawl4ai 获取页面 Markdown，再按规则提取有效链接
"""
import asyncio
import re
import argparse
from typing import List, Dict
# from crawl4ai import AsyncWebCrawler # 延迟导入
import logging
from tenacity import retry, stop_after_attempt, wait_exponential
from core.config import settings

logger = logging.getLogger(__name__)

class LinkExtractor:
    """对 Markdown 内容进行链接抽取与过滤"""
    def __init__(self, min_title_length: int = 24):
        self.min_title_length = min_title_length
        self.seen_titles = set()

    def extract_links(self, markdown_content: str) -> List[Dict[str, str]]:
        """从markdown内容中提取并过滤链接"""
        pattern = settings.crawler_markdown_link_pattern
        
        # 使用 finditer 以便检查匹配位置的前缀（识别图片链接）
        matches = re.finditer(pattern, markdown_content)
        links = []
        for m in matches:
            if len(m.groups()) >= 2:
                title, url = m.groups()[0], m.groups()[1]
                
                # 检查是否为图片链接 (![...])
                is_image = (m.start() > 0 and markdown_content[m.start()-1] == '!')
                
                # 如果是图片链接且配置为忽略，则跳过
                if is_image and settings.crawler_ignore_image_links():
                    continue
                    
                links.append((title, url))

        logger.info(f"共提取到 {len(links)} 个链接")

        link_objects: List[Dict[str, str]] = [
            {'title': title, 'url': url}
            for title, url in links
            if not (title in self.seen_titles or self.seen_titles.add(title))
        ]
        logger.info(f"过滤后剩余 {len(link_objects)} 个有效链接")

        filtered = [
            link for link in link_objects
            if len(link['title']) > self.min_title_length
        ]
        if settings.crawler_require_https():
            filtered = [link for link in filtered if str(link['url']).startswith('https://')]
        return filtered
@retry(
    stop=stop_after_attempt(settings.crawler_retry_attempts),
    wait=wait_exponential(
        multiplier=settings.crawler_retry_wait_multiplier,
        min=settings.crawler_retry_wait_min,
        max=settings.crawler_retry_wait_max
    ),
    reraise=True
)
async def fetch_page_content(params: Dict[str, any]) -> str:
    """
    抓取页面内容并返回 Markdown 文本
    
    Args:
        params: 参数字典
            - url (str): 目标页面 URL
            
    Returns:
        str: 页面 Markdown 内容
        
    Example:
        GET /?module_name=services.web.crawler.crawler_service&method_name=fetch_page_content&parameters={"url": "https://example.com"}
    """
    url = params.get("url")
    try:
        # 延迟导入，避免启动时加载及其副作用
        from crawl4ai import AsyncWebCrawler
        async with AsyncWebCrawler() as crawler:
            result = await crawler.arun(url=url)
            return result.markdown
    except Exception as e:
        logger.error(f"爬取页面失败: {str(e)}")
        raise

async def crawl_and_extract(params: Dict[str, any]) -> List[Dict[str, str]]:
    """
    入口：根据 URL 抓取并返回过滤后的链接列表
    
    Args:
        params: 参数字典
            - url (str): 目标页面 URL
            - min_title_length (int): 最小标题长度 (可选)
            
    Returns:
        List[Dict[str, str]]: 链接字典列表

    Example:
        GET /?module_name=services.web.crawler.crawler_service&method_name=crawl_and_extract&parameters={"url": "https://www.qbitai.com/"}
    """
    url = params.get("url")
    min_title_length = params.get("min_title_length", settings.crawler_min_title_length)

    logger.info(f"开始爬取URL: {url}, 最小标题长度: {min_title_length}")

    try:
        # 获取页面内容
        content = await fetch_page_content({"url": url})
        if not content:
            logger.error("未能获取到页面内容")
            return []

        # 提取链接
        extractor = LinkExtractor(min_title_length)
        long_titles = extractor.extract_links(content)

        # 打印结果
        for i, link in enumerate(long_titles):
            logger.info(f"链接 {i+1}: {link['title']} - {link['url']}")

        return long_titles

    except Exception as e:
        logger.error(f"爬取过程中发生错误: {str(e)}")
        return []

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='网页标题翻译工具')
    parser.add_argument('--url', type=str, default=settings.crawler_default_url, help='要爬取的网页URL')
    parser.add_argument('--min-title-length', type=int, default=settings.crawler_min_title_length, help='最小标题长度')

    logging.basicConfig(
        level=settings.get_logging_level_value(),
        format=settings.logging_format,
        datefmt=settings.logging_datefmt
    )

    args = parser.parse_args()
    params = {"url": args.url, "min_title_length": args.min_title_length}

    print(f"开始爬取 URL: {args.url}, 最小标题长度: {args.min_title_length}")
    results = asyncio.run(crawl_and_extract(params))
    print(f"爬取完成，共获取到 {len(results)} 个符合条件的链接")

