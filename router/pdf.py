import os
import logging
import tempfile
import zipfile
from typing import List, Dict, Tuple
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import Response, StreamingResponse
from pypdf import PdfReader
from pypdf.errors import PdfReadError
import io

from Resp import RespOk, RespFail, InvalidParams, ServerError

# 配置日志
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/pdf",
    tags=["PDF处理"],
    responses={404: {"description": "未找到"}},
)


class PDFChapter:
    """PDF章节信息"""
    def __init__(self, title: str, page_start: int, page_end: int = None):
        self.title = title
        self.page_start = page_start
        self.page_end = page_end


def get_page_number_from_destination(pdf_reader: PdfReader, destination) -> int:
    """从destination对象中提取页码"""
    try:
        if destination is None:
            return 0
        
        # 如果destination是整数，直接返回
        if isinstance(destination, int):
            return destination
        
        # 如果destination是页面对象，查找其在PDF中的索引
        if hasattr(destination, 'indirect_reference'):
            try:
                for idx, page in enumerate(pdf_reader.pages):
                    if hasattr(page, 'indirect_reference') and page.indirect_reference == destination.indirect_reference:
                        return idx + 1
            except:
                pass
        
        # 如果destination是列表或元组，尝试提取第一个元素
        if isinstance(destination, (list, tuple)) and len(destination) > 0:
            page_obj = destination[0]
            if hasattr(page_obj, 'indirect_reference'):
                try:
                    for idx, page in enumerate(pdf_reader.pages):
                        if hasattr(page, 'indirect_reference') and page.indirect_reference == page_obj.indirect_reference:
                            return idx + 1
                except:
                    pass
        
        # 如果destination是字典，尝试获取/Page键
        if isinstance(destination, dict):
            page_ref = destination.get('/Page') or destination.get('Page')
            if page_ref:
                return get_page_number_from_destination(pdf_reader, page_ref)
        
    except Exception as e:
        logger.debug(f"提取页码时出错: {str(e)}")
    
    return 0


def extract_outline(pdf_reader: PdfReader) -> List[PDFChapter]:
    """从PDF中提取目录结构"""
    chapters = []
    
    try:
        # 获取PDF的目录（outline）
        outline = pdf_reader.outline
        
        if not outline:
            logger.warning("PDF中没有找到目录结构")
            return chapters
        
        def process_outline_item(item, parent_page: int = 0):
            """递归处理目录项"""
            if isinstance(item, list):
                # 如果是列表，递归处理每个元素
                for sub_item in item:
                    process_outline_item(sub_item, parent_page)
            elif isinstance(item, dict):
                # 如果是字典，提取标题和页码
                title = item.get('/Title', item.get('Title', '未命名章节'))
                if isinstance(title, bytes):
                    title = title.decode('utf-8', errors='ignore')
                elif not isinstance(title, str):
                    title = str(title)
                
                # 获取页码
                page_num = parent_page
                destination = item.get('/Dest') or item.get('Dest') or item.get('/A')
                if destination:
                    page_num = get_page_number_from_destination(pdf_reader, destination)
                
                if page_num == 0:
                    page_num = parent_page
                
                # 只添加有效的章节（有标题和页码）
                if title and page_num > 0:
                    chapters.append(PDFChapter(title=title, page_start=page_num))
                    parent_page = page_num
                
                # 处理子项
                children = item.get('/First') or item.get('First')
                if children:
                    process_outline_item(children, parent_page)
                
                # 处理兄弟项
                next_item = item.get('/Next') or item.get('Next')
                if next_item:
                    process_outline_item(next_item, parent_page)
            else:
                # 如果是对象（pypdf的OutlineItem），尝试获取属性
                try:
                    # pypdf 3.x中，outline项通常是对象，有title和page属性
                    title = getattr(item, 'title', None)
                    if title is None:
                        title = str(item)
                    
                    if isinstance(title, bytes):
                        title = title.decode('utf-8', errors='ignore')
                    elif not isinstance(title, str):
                        title = str(title)
                    
                    page_num = parent_page
                    
                    # 尝试获取页码
                    if hasattr(item, 'page') and item.page is not None:
                        page_num = get_page_number_from_destination(pdf_reader, item.page)
                    
                    if page_num == 0:
                        page_num = parent_page
                    
                    if title and page_num > 0:
                        chapters.append(PDFChapter(title=title, page_start=page_num))
                        parent_page = page_num
                    
                    # 处理子项（pypdf的outline可能有children属性）
                    if hasattr(item, 'children') and item.children:
                        process_outline_item(item.children, parent_page)
                except Exception as e:
                    logger.debug(f"处理outline项时出错: {str(e)}")
        
        process_outline_item(outline)
        
        # 去重并排序章节（按页码）
        unique_chapters = {}
        for chapter in chapters:
            # 使用页码作为key去重
            if chapter.page_start not in unique_chapters:
                unique_chapters[chapter.page_start] = chapter
            else:
                # 如果页码相同，保留标题更长的（通常更详细）
                if len(chapter.title) > len(unique_chapters[chapter.page_start].title):
                    unique_chapters[chapter.page_start] = chapter
        
        chapters = sorted(unique_chapters.values(), key=lambda x: x.page_start)
        
        # 为每个章节设置结束页码（下一个章节的开始页码-1）
        for i in range(len(chapters) - 1):
            chapters[i].page_end = chapters[i + 1].page_start - 1
        
        # 最后一个章节的结束页码是PDF的最后一页
        if chapters:
            chapters[-1].page_end = len(pdf_reader.pages)
        
        logger.info(f"提取到 {len(chapters)} 个章节")
        
    except Exception as e:
        logger.error(f"提取目录时出错: {str(e)}", exc_info=True)
        # 如果提取目录失败，至少返回一个包含所有页面的章节
        if pdf_reader.pages:
            chapters.append(PDFChapter(
                title="全部内容",
                page_start=1,
                page_end=len(pdf_reader.pages)
            ))
    
    return chapters


def extract_text_from_pages(pdf_reader: PdfReader, start_page: int, end_page: int) -> str:
    """从PDF的指定页面范围提取文本"""
    text_content = []
    
    # 确保页码在有效范围内
    start_page = max(1, start_page)
    end_page = min(len(pdf_reader.pages), end_page)
    
    for page_num in range(start_page - 1, end_page):  # pypdf使用0-based索引
        try:
            page = pdf_reader.pages[page_num]
            text = page.extract_text()
            if text:
                text_content.append(text)
        except Exception as e:
            logger.warning(f"提取第 {page_num + 1} 页文本时出错: {str(e)}")
            continue
    
    return "\n\n".join(text_content)


def clean_filename(filename: str) -> str:
    """清理文件名，移除非法字符"""
    # 移除或替换非法字符
    illegal_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
    for char in illegal_chars:
        filename = filename.replace(char, '_')
    # 移除前后空格
    filename = filename.strip()
    # 限制文件名长度
    if len(filename) > 100:
        filename = filename[:100]
    return filename


def text_to_markdown(text: str, title: str = "") -> str:
    """将纯文本转换为Markdown格式"""
    lines = text.split('\n')
    markdown_lines = []
    
    # 添加标题
    if title:
        markdown_lines.append(f"# {title}\n")
    
    # 处理文本行
    for line in lines:
        line = line.strip()
        if not line:
            markdown_lines.append("")
            continue
        
        # 尝试识别标题（全大写或特定格式）
        if line.isupper() and len(line) > 3 and len(line) < 50:
            markdown_lines.append(f"## {line}\n")
        else:
            markdown_lines.append(line)
    
    return "\n".join(markdown_lines)


@router.post("/convert-to-markdown")
async def convert_pdf_to_markdown(
    file: UploadFile = File(...)
):
    """
    上传PDF文件，根据目录结构导出对应章节的MD文件集合的ZIP
    
    功能：
    1. 接收PDF文件上传
    2. 提取PDF的目录结构
    3. 根据目录将PDF按章节分割
    4. 将每个章节转换为Markdown格式
    5. 将所有MD文件打包成ZIP返回
    """
    temp_pdf_path = None
    temp_dir = None
    
    try:
        # 记录请求信息
        logger.info(f"收到PDF转换请求: filename={file.filename}, content_type={file.content_type}")
        
        # 验证文件是否存在
        if file is None:
            logger.error("文件对象为空")
            return RespFail(InvalidParams.set_msg("未接收到文件"))
        
        # 验证文件类型
        if not file.filename:
            logger.error("文件名为空")
            return RespFail(InvalidParams.set_msg("文件名不能为空"))
        
        if not file.filename.lower().endswith('.pdf'):
            logger.error(f"不支持的文件格式: {file.filename}")
            return RespFail(InvalidParams.set_msg("只支持PDF文件格式"))
        
        # 创建临时目录
        temp_dir = tempfile.mkdtemp(prefix="pdf_to_md_")
        logger.info(f"创建临时目录: {temp_dir}")
        
        # 保存上传的PDF文件到临时目录
        temp_pdf_path = os.path.join(temp_dir, "input.pdf")
        try:
            content = await file.read()
            if len(content) == 0:
                logger.error("上传的文件为空")
                return RespFail(InvalidParams.set_msg("上传的文件为空，请选择有效的PDF文件"))
            
            with open(temp_pdf_path, "wb") as f:
                f.write(content)
        except Exception as e:
            logger.error(f"保存文件时出错: {str(e)}")
            return RespFail(InvalidParams.set_msg(f"保存文件失败: {str(e)}"))
        
        logger.info(f"PDF文件已保存: {temp_pdf_path}, 大小: {len(content)} bytes")
        
        # 读取PDF文件
        try:
            pdf_reader = PdfReader(temp_pdf_path)
            total_pages = len(pdf_reader.pages)
            logger.info(f"PDF总页数: {total_pages}")
        except PdfReadError as e:
            return RespFail(InvalidParams.set_msg(f"PDF文件读取失败: {str(e)}"))
        except Exception as e:
            return RespFail(ServerError.set_msg(f"处理PDF文件时出错: {str(e)}"))
        
        # 提取目录结构
        chapters = extract_outline(pdf_reader)
        
        # 如果没有找到目录结构，将整个PDF作为一个章节处理
        if not chapters:
            logger.info("PDF中没有找到目录结构，将整个PDF作为一个章节处理")
            # 使用PDF文件名（不含扩展名）作为章节标题
            pdf_name = Path(file.filename).stem if file.filename else "全部内容"
            chapters = [PDFChapter(
                title=pdf_name,
                page_start=1,
                page_end=total_pages
            )]
        
        # 为每个章节生成MD文件
        md_files = []
        for idx, chapter in enumerate(chapters):
            try:
                # 提取章节文本
                text_content = extract_text_from_pages(
                    pdf_reader,
                    chapter.page_start,
                    chapter.page_end or chapter.page_start
                )
                
                if not text_content.strip():
                    logger.warning(f"章节 '{chapter.title}' 没有提取到文本内容")
                    continue
                
                # 转换为Markdown
                markdown_content = text_to_markdown(text_content, chapter.title)
                
                # 生成文件名
                safe_title = clean_filename(chapter.title)
                if not safe_title:
                    safe_title = f"章节_{idx + 1}"
                
                md_filename = f"{idx + 1:02d}_{safe_title}.md"
                md_filepath = os.path.join(temp_dir, md_filename)
                
                # 保存MD文件
                with open(md_filepath, "w", encoding="utf-8") as f:
                    f.write(markdown_content)
                
                md_files.append((md_filename, md_filepath))
                logger.info(f"已生成MD文件: {md_filename} (页码: {chapter.page_start}-{chapter.page_end})")
                
            except Exception as e:
                logger.error(f"处理章节 '{chapter.title}' 时出错: {str(e)}")
                continue
        
        if not md_files:
            return RespFail(ServerError.set_msg("未能生成任何MD文件"))
        
        # 创建ZIP文件
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for md_filename, md_filepath in md_files:
                zip_file.write(md_filepath, md_filename)
        
        zip_buffer.seek(0)
        
        # 生成ZIP文件名
        pdf_name = Path(file.filename).stem
        zip_filename = f"{pdf_name}_chapters.zip"
        
        logger.info(f"已生成ZIP文件: {zip_filename}, 包含 {len(md_files)} 个MD文件")
        
        # 返回ZIP文件
        return StreamingResponse(
            io.BytesIO(zip_buffer.read()),
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename={zip_filename}"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"处理PDF文件时发生错误: {str(e)}", exc_info=True)
        return RespFail(ServerError.set_msg(f"处理PDF文件时发生错误: {str(e)}"))
    
    finally:
        # 清理临时文件
        try:
            if temp_pdf_path and os.path.exists(temp_pdf_path):
                os.remove(temp_pdf_path)
            if temp_dir and os.path.exists(temp_dir):
                import shutil
                shutil.rmtree(temp_dir)
                logger.info(f"已清理临时目录: {temp_dir}")
        except Exception as e:
            logger.warning(f"清理临时文件时出错: {str(e)}")

