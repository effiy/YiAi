import asyncio
import re
import argparse
from typing import List, Dict, Optional
from crawl4ai import AsyncWebCrawler # type: ignore
import logging
from tenacity import retry, stop_after_attempt, wait_exponential # type: ignore
from Resp import RespOk

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

"""
# 示例请求:
# GET http://localhost:8000/api/?module_name=modules.crawler.crawler&method_name=fetch_page_content&params={"url":"https://www.qbitai.com/"}
#
# curl 示例:
# curl -X GET "http://localhost:8000/api/?module_name=modules.crawler.crawler&method_name=fetch_page_content&params=%7B%22url%22%3A%22https%3A%2F%2Fwww.qbitai.com%2F%22%7D"
#
# 参数说明:
# - url: 要爬取的网页URL
"""
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    reraise=True
)
async def fetch_page_content(params: Dict[str, any]) -> str:
    """获取页面内容，带重试机制
    
    参数:
        params (dict): 包含url的参数字典
    
    返回:
        str: 页面的markdown内容
    """
    url = params.get("url")
    try:
        async with AsyncWebCrawler() as crawler:
            result = await crawler.arun(url=url)
            return result.markdown
    except Exception as e:
        logger.error(f"爬取页面失败: {str(e)}")
        raise

"""
# 示例请求:
# GET http://localhost:8000/api/?module_name=modules.crawler.crawler&method_name=main&params={"url":"https://www.qbitai.com/","min_title_length":24}
#
# curl 示例:
# curl -X GET "http://localhost:8000/api/?module_name=modules.crawler.crawler&method_name=main&params=%7B%22url%22%3A%22https%3A%2F%2Fwww.qbitai.com%2F%22%2C%22min_title_length%22%3A24%7D"
#
# 参数说明:
# - url: 要爬取的网页URL
# - min_title_length: 最小标题长度，默认为24
"""
async def main(params: Dict[str, any]) -> List[Dict[str, str]]:
    """
    主函数：从指定URL爬取网页内容，提取并过滤链接标题
    
    参数:
        params (dict): 包含url和min_title_length的参数字典
    
    返回:
        List[Dict[str, str]]: 过滤后的长标题链接列表
    """
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

