import re
from copy import deepcopy
from typing import Any, Callable, Dict, List, Literal, Optional

import jieba
from haystack import Document, component, logging
from haystack.components.preprocessors.document_splitter import DocumentSplitter
from haystack.core.serialization import default_to_dict
from haystack.utils import serialize_callable

logger = logging.getLogger(__name__)


@component
class JiebaDocumentSplitter(DocumentSplitter):
    def __init__(  # pylint: disable=too-many-positional-arguments
        self,
        split_by: Literal["word", "sentence", "page", "passage", "function"] = "word",
        split_length: int = 200,
        split_overlap: int = 0,
        split_threshold: int = 0,
        respect_sentence_boundary: bool = False,
        splitting_function: Optional[Callable[[str], List[str]]] = None,
    ):
        """
        使用 jieba 或自定义逻辑对文档进行分割。

        :param split_by: 指定分割的单位。可选择：
            - `word` 按单词分割
            - `sentence` 按句子分割（使用正则逻辑）
            - `page` 按页分割（以换页符 "\\f" 为分割依据）
            - `passage` 按段落分割（以双换行符 "\\n\\n" 为分割依据）
            - `function` 使用自定义函数进行分割
        :param split_length: 每个分块的最大单位数（例如，最大单词数或句子数）。
        :param split_overlap: 每个分块之间的重叠单位数（例如，前后分块共享的单词数）。
        :param split_threshold: 分块的最小单位数。如果一个分块的单位数少于该值，则会合并到前一个分块中。
        :param respect_sentence_boundary: 是否在按单词分割时尊重句子边界。如果为 True，将确保分割发生在句子之间。
        :param splitting_function: 当 `split_by` 设置为 "function" 时，此参数需要传入一个自定义的分割函数。
        """

        super(JiebaDocumentSplitter, self).__init__(
            split_by=split_by,
            split_length=split_length,
            split_overlap=split_overlap,
            split_threshold=split_threshold,
            splitting_function=splitting_function,
        )

        self.respect_sentence_boundary = respect_sentence_boundary

    @staticmethod
    def _split_sentences_with_regex(text: str) -> List[str]:
        """
        使用正则表达式分割句子，支持中文句号（。）、问号（？）、感叹号（！）。
        """
        pattern = r'([^！？。]*[！？。])'  # 匹配以中文标点结束的句子
        sentences = re.findall(pattern, text)
        return [sentence.strip() for sentence in sentences if sentence.strip()]

    def _split_into_units(
        self, text: str, split_by: Literal["function", "page", "passage", "sentence", "word"]
    ) -> List[str]:
        """
        根据指定的 `split_by` 参数将文本分割成多个单元。

        :param text: 要分割的文本。
        :param split_by: 指定分割的单位。可选择 "word"（单词）、"sentence"（句子）、"page"（页）、"passage"（段落）或 "function"（自定义函数）。
        :returns: 分割后的单元列表。
        """
        if split_by == "page":
            self.split_at = "\f"  # 换页符
            units = text.split(self.split_at)
        elif split_by == "passage":
            self.split_at = "\n\n"  # 双换行符
            units = text.split(self.split_at)
        elif split_by == "sentence":
            # 使用正则表达式分割句子
            self.split_at = ""
            units = self._split_sentences_with_regex(text)
        elif split_by == "word":
            # 使用 jieba 进行单词分割
            self.split_at = " "
            units = list(jieba.cut(text))
        elif split_by == "function" and self.splitting_function is not None:
            # 使用自定义分割函数
            return self.splitting_function(text)
        else:
            raise NotImplementedError(
                "JiebaDocumentSplitter only supports 'function', 'page', 'passage', 'sentence', or 'word' as split units."
            )

        # 将分隔符添加回所有单元（最后一个单元除外）
        for i in range(len(units) - 1):
            units[i] += self.split_at
        return units

    @component.output_types(documents=List[Document])
    def run(self, documents: List[Document]) -> Dict[str, List[Document]]:
        """
        对文档进行分割处理。

        根据指定的分割方式（`split_by`），将文档分割为更小的部分。

        :param documents: 要分割的文档列表，每个文档是一个 `Document` 对象。

        :returns: 一个包含分割后文档的字典，结构如下：
            - `documents`: 分割后的文档列表。每个文档包含以下信息：
                - `source_id`: 原始文档的 ID，用于追踪来源。
                - 其他元数据字段保持不变。
        """
        if not isinstance(documents, list) or (documents and not isinstance(documents[0], Document)):
            raise TypeError("JiebaDocumentSplitter expects a list of Document objects as input.")

        split_docs = []
        for doc in documents:
            if doc.content is None:
                raise ValueError(
                    f"JiebaDocumentSplitter only works with text documents but content for document ID {doc.id} is None."
                )
            if doc.content == "":
                logger.warning("Document ID {doc_id} has an empty content. Skipping this document.", doc_id=doc.id)
                continue

            # 根据分割方式对文档内容进行分割
            units = self._split_into_units(doc.content, self.split_by)
            text_splits, splits_pages, splits_start_idxs = self._concatenate_units(
                elements=units,
                split_length=self.split_length,
                split_overlap=self.split_overlap,
                split_threshold=self.split_threshold,
            )
            metadata = deepcopy(doc.meta)
            metadata["source_id"] = doc.id
            split_docs += self._create_docs_from_splits(
                text_splits=text_splits, splits_pages=splits_pages, splits_start_idxs=splits_start_idxs, meta=metadata
            )
        logger.info(f"Document splitting completed. Total splits: {len(split_docs)}")
        return {"documents": split_docs}

    def to_dict(self) -> Dict[str, Any]:
        """
        将组件序列化为字典格式。

        :returns: 包含组件参数的字典。
        """
        serialized = default_to_dict(
            self,
            split_by=self.split_by,
            split_length=self.split_length,
            split_overlap=self.split_overlap,
            split_threshold=self.split_threshold,
            respect_sentence_boundary=self.respect_sentence_boundary,
        )
        if self.splitting_function:
            serialized["init_parameters"]["splitting_function"] = serialize_callable(self.splitting_function)
        return serialized