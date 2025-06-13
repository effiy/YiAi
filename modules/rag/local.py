from haystack import Pipeline # type: ignore
from haystack import Document # type: ignore
from datasets import load_dataset  # type: ignore
from haystack.document_stores.in_memory import InMemoryDocumentStore # type: ignore
from haystack.components.retrievers.in_memory import InMemoryEmbeddingRetriever # type: ignore
from haystack.document_stores.types import DuplicatePolicy # type: ignore
from haystack.components.builders import ChatPromptBuilder # type: ignore
from haystack.dataclasses import ChatMessage # type: ignore
from haystack_integrations.components.generators.ollama import OllamaChatGenerator # type: ignore
from haystack_integrations.components.embedders.ollama.text_embedder import OllamaTextEmbedder # type: ignore
from haystack_integrations.components.embedders.ollama.document_embedder import OllamaDocumentEmbedder # type: ignore
from typing import Dict, List

def init_document_store():
    """初始化文档存储"""
    return InMemoryDocumentStore()

def load_documents(data_files: dict = {"train": ["../../docs/**/*.md"]}):
    """加载并处理文档
    
    Args:
        data_files (dict): 数据文件配置，默认为 {"train": ["../../docs/**/*.md"]}
    """
    dataset = load_dataset("text", data_files=data_files, split="train")
    return [Document(content=doc["text"]) for doc in dataset] # type: ignore

def create_embeddings(docs):
    """为文档创建嵌入向量"""
    doc_embedder = OllamaDocumentEmbedder()
    return doc_embedder.run(docs)["documents"]

def init_retriever(docs_store):
    """初始化检索器"""
    return InMemoryEmbeddingRetriever(docs_store)

def create_prompt_template():
    """创建提示模板"""
    return [
        ChatMessage.from_user(
"""
根据以下信息，回答问题。
上下文:
{% for document in documents %}
    {{ document.content }}
{% endfor %}

问题: {{question}}
回答:
"""
        )
    ]

def init_components(model: str):
    """初始化LLM和文本嵌入器
    
    Args:
        model (str): 要使用的模型名称
    """
    return (
        OllamaChatGenerator(model=model),
        OllamaTextEmbedder()
    )

def create_pipeline(text_embedder, retriever, prompt_builder, llm):
    """创建并配置RAG管道"""
    pipeline = Pipeline()
    
    # 添加组件
    pipeline.add_component("text_embedder", text_embedder)
    pipeline.add_component("retriever", retriever)
    pipeline.add_component("prompt_builder", prompt_builder)
    pipeline.add_component("llm", llm)
    
    # 连接组件
    pipeline.connect("text_embedder.embedding", "retriever.query_embedding")
    pipeline.connect("retriever", "prompt_builder")
    pipeline.connect("prompt_builder.prompt", "llm.messages")
    
    return pipeline

# 示例请求:
# GET http://localhost:8000/api/?module_name=modules.rag.local&method_name=main&params={"question":"孙悟空是谁","model":"qwen3:0.6b","data_files":{"train":["docs/**/*.md"]}}
#
# 参数说明:
# - question: 要查询的问题
# - model: 要使用的模型名称
# - data_files: 数据文件配置
async def main(params: Dict[str, any]) -> List[Dict[str, str]]:
    """主函数
    
    Args:
        params (Dict[str, any]): 参数字典，包含:
            - question (str): 要查询的问题
            - model (str): 要使用的模型名称
            - data_files (dict): 数据文件配置
    """
    # 从参数字典中获取配置
    question = params.get("question", "孙悟空是谁")
    model = params.get("model", "qwen3:0.6b")
    data_files = params.get("data_files", {"train": ["docs/**/*.md"]})
    
    # 初始化文档存储
    docs_store = init_document_store()
    
    # 加载和处理文档
    docs = load_documents(data_files)
    docs_with_embeddings = create_embeddings(docs)
    
    # 写入文档存储
    docs_store.write_documents(docs_with_embeddings, policy=DuplicatePolicy.OVERWRITE)
    
    # 初始化检索器
    retriever = init_retriever(docs_store)
    
    # 创建提示模板和构建器
    template = create_prompt_template()
    prompt_builder = ChatPromptBuilder(template=template)
    
    # 初始化LLM和文本嵌入器
    llm, text_embedder = init_components(model)
    
    # 创建管道
    pipeline = create_pipeline(text_embedder, retriever, prompt_builder, llm)
    
    # 执行查询
    result = pipeline.run(data={
        "prompt_builder": {"question": question},
        "text_embedder": {"text": question}
    })
    
    # 返回结果
    return [{"answer": result["llm"]["replies"][0].text}]

if __name__ == "__main__":
    import asyncio
    params = {
        "question": "孙悟空是谁",
        "model": "qwen3:0.6b",
        "data_files": {"train": ["../../docs/**/*.md"]}
    }
    answer = asyncio.run(main(params))
    print(answer)
