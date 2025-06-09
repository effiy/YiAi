import asyncio
import re
import argparse
from typing import List, Dict
from crawl4ai import AsyncWebCrawler # type: ignore # https://github.com/unclecode/crawl4ai

async def main(params):
    url = params.get("url")
    min_title_length = params.get("min_title_length")

    async with AsyncWebCrawler() as crawler:
        # 爬取网页内容
        result = await crawler.arun(url=url)

        # 提取markdown中的链接
        links = re.findall(r'\[(.*?)\]\((.*?)\)', result.markdown)

        # 转换为字典列表,过滤掉图片链接
        # 使用集合去重,保留第一次出现的标题
        seen_titles = set()
        link_objects: List[Dict[str, str]] = [
            {'title': title, 'url': url}
            for title, url in links
            if not title.startswith('![') and not (title in seen_titles or seen_titles.add(title))
        ]

        # 筛选长标题
        long_titles = [
            link for link in link_objects
            if len(link['title']) > min_title_length
        ]
        
        return long_titles

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='网页标题翻译工具')
    parser.add_argument('--url', type=str, default="https://syncedreview.com/", help='要爬取的网页URL')
    parser.add_argument('--min-title-length', type=int, default=24, help='最小标题长度')

    args = parser.parse_args()
    asyncio.run(main(args.url, args.min_title_length))

