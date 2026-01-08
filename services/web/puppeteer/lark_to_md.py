import json
from typing import List, Dict, Any
from enum import Enum

class BlockType(Enum):
    PAGE = 'page'
    HEADING1 = 'heading1'
    HEADING2 = 'heading2'
    HEADING3 = 'heading3'
    HEADING4 = 'heading4'
    HEADING5 = 'heading5'
    HEADING6 = 'heading6'
    HEADING7 = 'heading7'
    HEADING8 = 'heading8'
    HEADING9 = 'heading9'
    CODE = 'code'
    DIVIDER = 'divider'
    IMAGE = 'image'
    BULLET = 'bullet'
    ORDERED = 'ordered'
    TODO = 'todo'
    QUOTE = 'quote'
    QUOTE_CONTAINER = 'quote_container'
    TABLE = 'table'
    CELL = 'table_cell'
    TEXT = 'text'
    VIEW = 'view'
    ISV = 'isv'
    CALLOUT = 'callout'
    UNKNOWN = 'unknown'

class LarkToMarkdownConverter:
    """Lark 文档转 Markdown 工具类"""
    def __init__(self):
        """初始化 LarkToMarkdownConverter"""
        pass

    def convert(self, doc_json: Dict[str, Any]) -> str:
        """
        将 Lark 文档 JSON 转换为 Markdown
        
        Args:
            doc_json: Lark 文档 JSON 数据
            
        Returns:
            str: Markdown 字符串

        Example:
            >>> converter = LarkToMarkdownConverter()
            >>> doc = {"type": "page", "children": [{"type": "heading1", "zoneState": {"ops": [{"insert": "Title"}]}}]}
            >>> converter.convert(doc)
            '# Title'
        """
        # If the input is the root block (PAGE), process its children
        if doc_json.get('type') == BlockType.PAGE.value:
            return self._process_blocks(doc_json.get('children', []))

        # If it's a list of blocks
        if isinstance(doc_json, list):
            return self._process_blocks(doc_json)

        return ""

    def _process_blocks(self, blocks: List[Dict[str, Any]]) -> str:
        """
        处理块列表
        
        Args:
            blocks: 块数据列表
            
        Returns:
            str: Markdown 字符串

        Example:
            >>> blocks = [{"type": "text", "zoneState": {"ops": [{"insert": "Hello"}]}}]
            >>> self._process_blocks(blocks)
            'Hello'
        """
        output = []

        i = 0
        while i < len(blocks):
            block = blocks[i]
            block_type = block.get('type')

            # Handle lists (grouping adjacent list items)
            if block_type in [BlockType.BULLET.value, BlockType.ORDERED.value, BlockType.TODO.value]:
                list_items = [block]
                j = i + 1
                while j < len(blocks):
                    next_block = blocks[j]
                    if next_block.get('type') == block_type:
                        list_items.append(next_block)
                        j += 1
                    else:
                        break
                output.append(self._process_list(list_items))
                i = j
                continue

            # Handle other blocks
            markdown = self._process_block(block)
            if markdown:
                output.append(markdown)
            i += 1

        return "\n\n".join(filter(None, output))

    def _process_block(self, block: Dict[str, Any]) -> str:
        """
        处理单个块
        
        Args:
            block: 块数据字典
            
        Returns:
            str: 该块对应的 Markdown

        Example:
            >>> block = {"type": "heading1", "zoneState": {"ops": [{"insert": "Header"}]}}
            >>> self._process_block(block)
            '# Header'
        """
        block_type = block.get('type')

        if block_type == BlockType.PAGE.value:
            return self._process_blocks(block.get('children', []))

        elif block_type in [
            BlockType.HEADING1.value, BlockType.HEADING2.value, BlockType.HEADING3.value,
            BlockType.HEADING4.value, BlockType.HEADING5.value, BlockType.HEADING6.value,
            BlockType.HEADING7.value, BlockType.HEADING8.value, BlockType.HEADING9.value
        ]:
            return self._process_heading(block)

        elif block_type == BlockType.CODE.value:
            return self._process_code(block)

        elif block_type == BlockType.DIVIDER.value:
            return "---"

        elif block_type == BlockType.QUOTE_CONTAINER.value or block_type == BlockType.CALLOUT.value:
            return self._process_quote(block)

        elif block_type == BlockType.TEXT.value:
            return self._process_text_block(block)

        elif block_type == BlockType.IMAGE.value:
            return self._process_image(block)

        elif block_type == BlockType.TABLE.value:
            return self._process_table(block)

        # Fallback for container blocks or unknown blocks that might have children
        children = block.get('children', [])
        if children:
            return self._process_blocks(children)

        return ""

    def _get_block_content(self, block: Dict[str, Any]) -> str:
        """
        从块的 zoneState.ops 中提取文本内容
        
        Args:
            block: 块数据字典
            
        Returns:
            str: 提取的 Markdown 文本

        Example:
            >>> block = {"zoneState": {"ops": [{"insert": "Text"}]}}
            >>> self._get_block_content(block)
            'Text'
        """
        zone_state = block.get('zoneState')
        if not zone_state:
            return ""

        content = zone_state.get('content')
        if not content:
            return ""

        ops = content.get('ops', [])
        return self._ops_to_markdown(ops)

    def _ops_to_markdown(self, ops: List[Dict[str, Any]]) -> str:
        """
        将操作列表转换为 Markdown 字符串，处理粗体、斜体、链接等属性
        
        Args:
            ops: 操作列表
            
        Returns:
            str: 格式化后的 Markdown 字符串

        Example:
            >>> ops = [{"insert": "Bold", "attributes": {"bold": True}}]
            >>> self._ops_to_markdown(ops)
            '**Bold**'
        """
        result = ""
        for op in ops:
            insert = op.get('insert', '')
            attributes = op.get('attributes', {})

            if not insert:
                continue

            # Handle inline component (like doc mention)
            if attributes.get('inline-component'):
                try:
                    comp = json.loads(attributes['inline-component'])
                    if comp.get('type') == 'mention_doc':
                        attributes['link'] = comp['data']['raw_url']
                        insert += comp['data']['title']
                except:
                    pass

            text = insert

            # Apply formatting
            if attributes.get('code') or attributes.get('inlineCode'):
                text = f"`{text}`"
            else:
                # Math
                if attributes.get('equation'):
                    text = f"${attributes['equation']}$"

                if attributes.get('bold'):
                    text = f"**{text}**"

                if attributes.get('italic'):
                    text = f"*{text}*"

                if attributes.get('strikethrough'):
                    text = f"~~{text}~~"

                if attributes.get('link'):
                    url = attributes['link']
                    text = f"[{text}]({url})"

            result += text

        return result

    def _process_heading(self, block: Dict[str, Any]) -> str:
        """处理标题块"""
        level = int(block['type'].replace('heading', ''))
        content = self._get_block_content(block)
        return f"{'#' * level} {content}"

    def _process_code(self, block: Dict[str, Any]) -> str:
        """
        处理代码块
        
        Args:
            block: 代码块数据
            
        Returns:
            str: Markdown 代码块

        Example:
            >>> block = {"language": "python", "zoneState": {"ops": [{"insert": "print('hello')"}]}}
            >>> self._process_code(block)
            '```python\\nprint('hello')\\n```'
        """
        language = block.get('language', '').lower()
        content = self._get_block_content(block)
        if not content.endswith('\n'):
            content += '\n'
        return f"```{language}\n{content}```"

    def _process_quote(self, block: Dict[str, Any]) -> str:
        """
        处理引用块
        
        Args:
            block: 引用块数据
            
        Returns:
            str: Markdown 引用
        """
        children = block.get('children', [])
        content = self._process_blocks(children)
        # Add > to each line
        quoted = "\n".join([f"> {line}" if line else ">" for line in content.split('\n')])
        return quoted

    def _process_text_block(self, block: Dict[str, Any]) -> str:
        """
        处理文本块
        
        Args:
            block: 文本块数据
            
        Returns:
            str: Markdown 文本
        """
        return self._get_block_content(block)

    def _process_image(self, block: Dict[str, Any]) -> str:
        """
        处理图片块
        
        Args:
            block: 图片块数据
            
        Returns:
            str: Markdown 图片链接
        """
        # TODO: Implement image processing based on actual data structure
        return "![Image](image_url)"

    def _process_table(self, block: Dict[str, Any]) -> str:
        """
        处理表格块
        
        Args:
            block: 表格块数据
            
        Returns:
            str: Markdown 表格
        """
        # TODO: Implement table processing
        return "\n[Table]\n"

    def _process_list(self, list_items: List[Dict[str, Any]]) -> str:
        """
        处理列表块（无序列表、有序列表、待办事项）
        
        Args:
            list_items: 连续的列表项块列表
            
        Returns:
            str: Markdown 列表
        """
        output = []
        for i, block in enumerate(list_items):
            content = self._get_block_content(block)
            block_type = block.get('type')
            
            if block_type == BlockType.ORDERED.value:
                output.append(f"{i+1}. {content}")
            elif block_type == BlockType.TODO.value:
                # 尝试从 props 获取选中状态，默认为未选中
                try:
                    checked = block.get('props', {}).get('todo', {}).get('isChecked', False)
                except:
                    checked = False
                mark = "x" if checked else " "
                output.append(f"- [{mark}] {content}")
            else: # BULLET
                output.append(f"- {content}")
                
            # 处理嵌套子块
            children = block.get('children', [])
            if children:
                child_content = self._process_blocks(children)
                # 缩进子内容
                indented = "\n".join(["    " + line for line in child_content.split('\n')])
                output.append(indented)
                
        return "\n".join(output)

def convert_lark_to_md(params: Dict[str, Any]) -> str:
    """
    将 Lark 文档 JSON 转换为 Markdown
    
    Args:
        params: 参数字典
            - doc_json (Dict): Lark 文档 JSON 数据
            
    Returns:
        str: Markdown 字符串
        
    Example:
        GET /?module_name=services.web.puppeteer.lark_to_md&method_name=convert_lark_to_md&parameters={"doc_json": {"type": "page", "children": [...]}}
    """
    doc_json = params.get('doc_json', {})
    converter = LarkToMarkdownConverter()
    return converter.convert(doc_json)

