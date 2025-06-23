from haystack import Pipeline, Document # type: ignore
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
import os

def init_document_store():
    """初始化文档存储"""
    return InMemoryDocumentStore()

def load_documents(data_files: dict = {"train": ["../../docs/**/*.md"]}):
    """加载并处理文档"""
    dataset = load_dataset("text", data_files=data_files, split="train")
    return [Document(content=doc["text"]) for doc in dataset] # type: ignore

def create_embeddings(docs):
    """为文档创建嵌入向量"""
    ollama_embedder_url = os.getenv("OLLAMA_EMBEDDER_URL", "http://localhost:11434")
    document_embedder = OllamaDocumentEmbedder(url=ollama_embedder_url, model="nomic-embed-text")
    return document_embedder.run(docs)["documents"]

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
    """初始化LLM和文本嵌入器"""
    ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
    ollama_embedder_url = os.getenv("OLLAMA_EMBEDDER_URL", "http://localhost:11434")
    return (
        OllamaChatGenerator(model=model, url=ollama_url),
        OllamaTextEmbedder(url=ollama_embedder_url, model="nomic-embed-text")
    )

def create_pipeline(text_embedder, retriever, prompt_builder, llm):
    """创建并配置RAG管道"""
    pipeline = Pipeline()
    
    # 添加组件并连接
    pipeline.add_component("text_embedder", text_embedder)
    pipeline.add_component("retriever", retriever)
    pipeline.add_component("prompt_builder", prompt_builder)
    pipeline.add_component("llm", llm)
    
    pipeline.connect("text_embedder.embedding", "retriever.query_embedding")
    pipeline.connect("retriever", "prompt_builder")
    pipeline.connect("prompt_builder.prompt", "llm.messages")
    
    return pipeline

# 示例请求:
# GET http://localhost:8000/api/?module_name=modules.rag.local&method_name=main&params={"question":"孙悟空是谁","model":"qwen3:0.6b","data_files":{"train":["docs/**/*.md"]}}
async def main(params: Dict[str, any]) -> List[Dict[str, str]]:
    # 获取配置
    question = params.get("question", "孙悟空是谁")
    model = params.get("model", "qwq")
    data_files = params.get("data_files", {"train": ["docs/**/*.md"]})
    
    # 初始化文档存储并加载文档
    docs_store = init_document_store()
    docs_with_embeddings = create_embeddings(load_documents(data_files))
    docs_store.write_documents(docs_with_embeddings, policy=DuplicatePolicy.OVERWRITE)
    
    # 初始化组件
    llm, text_embedder = init_components(model)
    retriever = InMemoryEmbeddingRetriever(docs_store)
    prompt_builder = ChatPromptBuilder(template=create_prompt_template())
    
    # 创建并执行管道
    pipeline = create_pipeline(text_embedder, retriever, prompt_builder, llm)
    result = pipeline.run(data={
        "prompt_builder": {"question": question},
        "text_embedder": {"text": question}
    })
    
    return [{"answer": result["llm"]["replies"][0].text}]

if __name__ == "__main__":
    import asyncio
    params = {
        "question": "孙悟空是谁",
        "model": "qwq",
        "data_files": {"train": ["../../docs/**/*.md"]}
    }
    answer = asyncio.run(main(params))
    print(answer)
