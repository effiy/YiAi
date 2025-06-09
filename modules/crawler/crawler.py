import asyncio
import re
import argparse
from typing import List, Dict
from crawl4ai import AsyncWebCrawler # type: ignore # https://github.com/unclecode/crawl4ai
import logging

# 配置日志
logger = logging.getLogger(__name__)
# 设置日志级别和格式
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def main(params):
    """
    主函数：从指定URL爬取网页内容，提取并过滤链接标题
    
    参数:
        params (dict): 包含url和min_title_length的参数字典
    
    返回:
        List[Dict[str, str]]: 过滤后的长标题链接列表
    """
    # 从参数字典中获取URL和最小标题长度
    url = params.get("url")
    min_title_length = params.get("min_title_length")
    
    logger.info(f"开始爬取URL: {url}, 最小标题长度: {min_title_length}")

    try:
        async with AsyncWebCrawler() as crawler:
            # 爬取网页内容，crawler.arun会返回包含markdown格式的网页内容
            logger.info("正在爬取网页内容...")
            result = await crawler.arun(url=url)
            logger.info("网页内容爬取完成")

            # 使用正则表达式提取markdown中的链接，格式为[标题](链接URL)
            links = re.findall(r'\[(.*?)\]\((.*?)\)', result.markdown)
            logger.info(f"共提取到 {len(links)} 个链接")

            # 转换为字典列表,过滤掉图片链接
            # 使用集合去重,保留第一次出现的标题
            seen_titles = set()
            link_objects: List[Dict[str, str]] = [
                {'title': title, 'url': url}
                for title, url in links
                # 过滤条件：不是图片链接(不以![开头)且标题未曾出现过
                if not title.startswith('![') and not (title in seen_titles or seen_titles.add(title))
            ]
            logger.info(f"过滤后剩余 {len(link_objects)} 个有效链接")

            # 筛选标题长度大于min_title_length的链接
            long_titles = [
                link for link in link_objects
                if len(link['title']) > min_title_length
            ]
            logger.info(f"最终得到 {len(long_titles)} 个长标题链接")
            
            # 打印结果
            for i, link in enumerate(long_titles):
                logger.info(f"链接 {i+1}: {link['title']} - {link['url']}")
            
            # 返回筛选后的长标题链接列表
            return long_titles
    except Exception as e:
        logger.error(f"爬取过程中发生错误: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return []

if __name__ == '__main__':
    # 创建命令行参数解析器
    parser = argparse.ArgumentParser(description='网页标题翻译工具')
    # 添加URL参数，默认值为Synced Review网站
    parser.add_argument('--url', type=str, default="https://syncedreview.com/", help='要爬取的网页URL')
    # 添加最小标题长度参数，默认值为24
    parser.add_argument('--min-title-length', type=int, default=24, help='最小标题长度')

    # 解析命令行参数
    args = parser.parse_args()
    # 将参数转换为字典格式，与main函数期望的参数格式匹配
    params = {"url": args.url, "min_title_length": args.min_title_length}
    
    print(f"开始爬取 URL: {args.url}, 最小标题长度: {args.min_title_length}")
    
    # 运行主函数
    results = asyncio.run(main(params))
    
    print(f"爬取完成，共获取到 {len(results)} 个符合条件的链接")
