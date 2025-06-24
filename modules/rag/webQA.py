import os
from typing import Dict, List
from haystack import Pipeline # type: ignore
from haystack.components.fetchers.link_content import LinkContentFetcher # type: ignore
from haystack.components.converters import HTMLToDocument # type: ignore
from haystack.components.preprocessors import DocumentSplitter # type: ignore
from haystack.components.rankers import LostInTheMiddleRanker # type: ignore
from haystack.components.builders import ChatPromptBuilder # type: ignore
from haystack.dataclasses import ChatMessage # type: ignore
from haystack_integrations.components.generators.ollama import OllamaChatGenerator # type: ignore

def create_pipeline(model: str, ollama_url: str):
    """创建并配置Web QA管道"""
    # 增加连接超时配置
    fetcher = LinkContentFetcher(timeout=30, retry_attempts=3)
    converter = HTMLToDocument()
    document_splitter = DocumentSplitter(split_by="word", split_length=50)
    # 使用不需要网络连接的排序器
    ranker = LostInTheMiddleRanker(top_k=3)
    prompt_template = [
        ChatMessage.from_user("""
根据以下文档：

{% for doc in documents %}
  {{ doc.content }}
{% endfor %}

回答问题: {{question}}
回答:
""")
    ]
    prompt_builder = ChatPromptBuilder(template=prompt_template, required_variables=["documents", "question"])

    pipeline = Pipeline()
    pipeline.add_component("fetcher", fetcher)
    pipeline.add_component("converter", converter)
    pipeline.add_component("splitter", document_splitter)
    pipeline.add_component("ranker", ranker)
    pipeline.add_component("prompt_builder", prompt_builder)
    pipeline.add_component("llm", OllamaChatGenerator(model=model, url=ollama_url))

    pipeline.connect("fetcher.streams", "converter.sources")
    pipeline.connect("converter.documents", "splitter.documents")
    pipeline.connect("splitter.documents", "ranker.documents")
    pipeline.connect("ranker.documents", "prompt_builder.documents")
    pipeline.connect("prompt_builder.prompt", "llm.messages")
    
    return pipeline

# 示例请求:
# GET http://localhost:8000/api/?module_name=modules.rag.webQA&method_name=main&params={"question":"What do graphs have to do with Haystack?","urls":["https://haystack.deepset.ai/blog/introducing-haystack-2-beta-and-advent"],"model":"qwq"}
async def main(params: Dict[str, any]) -> List[Dict[str, str]]:
    """主函数
    
    Args:
        params (Dict[str, any]): 参数字典，包含:
            - question (str): 要查询的问题
            - urls (List[str]): 要抓取的网页URL列表
            - model (str): 要使用的模型名称
    """
    # 从参数字典中获取配置
    question = params.get("question", "What do graphs have to do with Haystack?")
    urls = params.get("urls", [""])
    model = params.get("model", "qwq")
    
    # 获取Ollama配置
    ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
    
    try:
        # 创建管道
        pipeline = create_pipeline(model, ollama_url)
        
        # 执行查询
        result = pipeline.run({
            "prompt_builder": {"question": question},
            "fetcher": {"urls": urls},
            "llm": {"generation_kwargs": {"max_new_tokens": 350}}
        })
        
        # 返回结果
        return [{"answer": result['llm']['replies'][0].text}]
        
    except Exception as e:
        return [{"error": f"处理请求时发生错误: {str(e)}"}]

if __name__ == "__main__":
    import asyncio
    params = {
        "question": "拒绝谎言，反抗逼迫是谁说的?",
        "urls": ["https://www.sohu.com/a/256084103_100020266"],
        "model": "qwq"
    }
    answer = asyncio.run(main(params))
    print(answer)

