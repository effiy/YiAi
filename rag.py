from haystack import Pipeline
from haystack import Document
from datasets import load_dataset  # type: ignore
from haystack.document_stores.in_memory import InMemoryDocumentStore
from haystack.components.retrievers.in_memory import InMemoryEmbeddingRetriever
from haystack.document_stores.types import DuplicatePolicy

from haystack.components.builders import ChatPromptBuilder
from haystack.dataclasses import ChatMessage


from haystack_integrations.components.generators.ollama import OllamaChatGenerator
from haystack_integrations.components.embedders.ollama.text_embedder import OllamaTextEmbedder
from haystack_integrations.components.embedders.ollama.document_embedder import OllamaDocumentEmbedder

docs_store = InMemoryDocumentStore()

# 支持加载 text 和 md 文件
dataset = load_dataset("text", data_files={"train": ["./docs/**/*.md"]}, split="train")

docs = [Document(content=doc["text"]) for doc in dataset]

doc_embedder = OllamaDocumentEmbedder()

docs_with_embeddings = doc_embedder.run(docs)["documents"]

docs_store.write_documents(docs_with_embeddings, policy=DuplicatePolicy.OVERWRITE)

retriever = InMemoryEmbeddingRetriever(docs_store)

template = [
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

prompt_builder = ChatPromptBuilder(template=template)

llm = OllamaChatGenerator()
text_embedder = OllamaTextEmbedder()

basic_rag_pipeline = Pipeline()
# Add components to your pipeline
basic_rag_pipeline.add_component("text_embedder", text_embedder)
basic_rag_pipeline.add_component("retriever", retriever)
basic_rag_pipeline.add_component("prompt_builder", prompt_builder)
basic_rag_pipeline.add_component("llm", llm)

basic_rag_pipeline.connect("text_embedder.embedding", "retriever.query_embedding")
basic_rag_pipeline.connect("retriever", "prompt_builder")
basic_rag_pipeline.connect("prompt_builder.prompt", "llm.messages")

question = "yblog 是什么?"

# 运行RAG管道，处理用户查询
result = basic_rag_pipeline.run(data={"prompt_builder": {"question":question}, "text_embedder": {"text": question}})

# 打印生成的回答结果
print(result["llm"]["replies"][0].text)