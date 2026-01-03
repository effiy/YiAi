import asyncio
import re
import argparse
from typing import List, Dict, Optional
from crawl4ai import AsyncWebCrawler
import logging
from tenacity import retry, stop_after_attempt, wait_exponential
from resp import RespOk

# 配置日志
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class LinkExtractor:
    def __init__(self, min_title_length: int = 24):
        self.min_title_length = min_title_length
        self.seen_titles = set()

    def extract_links(self, markdown_content: str) -> List[Dict[str, str]]:
        """从markdown内容中提取并过滤链接"""
        links = re.findall(r'\[(.*?)\]\((.*?)\)', markdown_content)
        logger.info(f"共提取到 {len(links)} 个链接")

        link_objects: List[Dict[str, str]] = [
            {'title': title, 'url': url}
            for title, url in links
            if not title.startswith('![') and not (title in self.seen_titles or self.seen_titles.add(title))
        ]
        logger.info(f"过滤后剩余 {len(link_objects)} 个有效链接")

        return [
            link for link in link_objects
            if len(link['title']) > self.min_title_length
        ]
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    reraise=True
)
async def fetch_page_content(params: Dict[str, any]) -> str:
    url = params.get("url")
    try:
        async with AsyncWebCrawler() as crawler:
            result = await crawler.arun(url=url)
            return result.markdown
    except Exception as e:
        logger.error(f"爬取页面失败: {str(e)}")
        raise

async def main(params: Dict[str, any]) -> List[Dict[str, str]]:
    url = params.get("url")
    min_title_length = params.get("min_title_length", 24)

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

        return RespOk(data=long_titles)

    except Exception as e:
        logger.error(f"爬取过程中发生错误: {str(e)}")
        logger.error(traceback.format_exc())
        return RespOk(data=[])

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='网页标题翻译工具')
    parser.add_argument('--url', type=str, default="https://syncedreview.com/", help='要爬取的网页URL')
    parser.add_argument('--min-title-length', type=int, default=24, help='最小标题长度')

    args = parser.parse_args()
    params = {"url": args.url, "min_title_length": args.min_title_length}

    print(f"开始爬取 URL: {args.url}, 最小标题长度: {args.min_title_length}")
    results = asyncio.run(main(params))
    print(f"爬取完成，共获取到 {len(results)} 个符合条件的链接")

