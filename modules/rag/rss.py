import os, feedparser # type: ignore
from typing import Dict, List

from haystack import Document, Pipeline # type: ignore
from haystack.components.builders import ChatPromptBuilder # type: ignore
from haystack.components.retrievers.in_memory import InMemoryBM25Retriever # type: ignore
from haystack.document_stores.in_memory import InMemoryDocumentStore # type: ignore
from haystack.dataclasses import ChatMessage # type: ignore
from haystack_integrations.components.generators.ollama import OllamaChatGenerator # type: ignore

# Dict of website RSS feeds
urls = {
  'techcrunch': 'https://techcrunch.com/feed',
  'mashable': 'https://mashable.com/feeds/rss/all',
  'cnet': 'https://cnet.com/rss/news',
  'engadget': 'https://engadget.com/rss.xml',
  'zdnet': 'https://zdnet.com/news/rss.xml',
  'venturebeat': 'https://feeds.feedburner.com/venturebeat/SZYF',
  'readwrite': 'https://readwrite.com/feed/',
  'wired': 'https://wired.com/feed/rss',
  'gizmodo': 'https://gizmodo.com/rss',
}

NUM_WEBSITES = 3
NUM_TITLES = 1

def get_titles(urls: Dict[str, str], num_sites: int, num_titles: int) -> List[str]:
    titles: List[str] = []
    sites = list(urls.keys())[:num_sites]
    for site in sites:
        feed = feedparser.parse(urls[site])
        entries = feed.entries[:num_titles]
        for entry in entries:
            titles.append(entry.title)
    return titles

titles = get_titles(urls, NUM_WEBSITES, NUM_TITLES)


document_store = InMemoryDocumentStore()
document_store.write_documents(
    [
        Document(content=title) for title in titles
    ]
)

template = [
    ChatMessage.from_user("""
标题:
{% for document in documents %}
    {{ document.content }}
{% endfor %}

请求: {{ query }}
""")
]

pipe = Pipeline()

pipe.add_component("retriever", InMemoryBM25Retriever(document_store=document_store))
pipe.add_component("prompt_builder", ChatPromptBuilder(template=template, required_variables=["documents", "query"]))
ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
ollama_model = os.getenv("OLLAMA_MODEL", "qwq")
llm = OllamaChatGenerator(model=ollama_model, url=ollama_url)
pipe.add_component("llm", llm)
pipe.connect("retriever", "prompt_builder.documents")
pipe.connect("prompt_builder.prompt", "llm.messages")

query = f"请用三个词总结提供的{NUM_WEBSITES * NUM_TITLES}个标题中的每一个。"

response = pipe.run({"prompt_builder": {"query": query}, "retriever": {"query": query}})

print(response["llm"]["replies"])

