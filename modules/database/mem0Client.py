import os
import json
import logging
import socket
import urllib.request
import urllib.error
from typing import Optional, Dict, Any, List
from urllib.parse import urlparse
from mem0 import Memory
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class Mem0Client:
    """Mem0 记忆管理客户端"""
    _instance = None
    _memory: Optional[Memory] = None
    _initialization_failed: bool = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Mem0Client, cls).__new__(cls)
            cls._instance._initialization_failed = False
        return cls._instance

    def _check_service_connection(self, url: str, service_name: str) -> bool:
        """检查服务是否可连接（支持本地和远程 URL）"""
        try:
            parsed = urlparse(url)
            scheme = parsed.scheme.lower()
            
            # 如果是 HTTPS 或远程 HTTP，使用 HTTP 请求检查
            if scheme in ['https'] or (scheme == 'http' and parsed.hostname not in ['localhost', '127.0.0.1', '0.0.0.0']):
                try:
                    # 尝试访问服务的健康检查端点
                    check_url = url.rstrip('/')
                    if service_name.lower() == "ollama":
                        check_url = f"{check_url}/api/tags"  # Ollama 的健康检查端点
                    elif service_name.lower() == "qdrant":
                        check_url = f"{check_url}/collections"  # Qdrant 的健康检查端点
                    
                    req = urllib.request.Request(check_url)
                    req.add_header('User-Agent', 'Mem0Client/1.0')
                    with urllib.request.urlopen(req, timeout=5) as response:
                        return response.status < 500
                except (urllib.error.URLError, urllib.error.HTTPError, Exception) as e:
                    logger.debug(f"HTTP 检查 {service_name} ({url}) 失败: {str(e)}")
                    # 对于远程服务，如果 HTTP 检查失败，仍然允许尝试连接（可能是网络问题）
                    # 返回 True 让 Mem0 自己处理连接错误
                    return True
            
            # 对于本地服务，使用 socket 检查
            else:
                host = parsed.hostname or "localhost"
                port = parsed.port or (6333 if "qdrant" in service_name.lower() else 11434)
                
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                result = sock.connect_ex((host, port))
                sock.close()
                return result == 0
        except Exception as e:
            logger.warning(f"检查 {service_name} 连接时出错: {str(e)}")
            # 对于远程服务，即使检查失败也允许尝试连接
            parsed = urlparse(url)
            if parsed.scheme in ['https', 'http'] and parsed.hostname not in ['localhost', '127.0.0.1', '0.0.0.0']:
                return True
            return False

    def __init__(self):
        if self._memory is None:
            # 保存原始的 OPENAI_API_KEY（如果存在）
            original_openai_key = os.environ.get("OPENAI_API_KEY")
            try:
                # Mem0 配置
                qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
                qdrant_api_key = os.getenv("QDRANT_API_KEY", None)
                
                ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
                ollama_embedding_model = os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")
                ollama_model_val = os.getenv("OLLAMA_MODEL", "qwen3")
                ollama_auth = os.getenv("OLLAMA_AUTH", None)  # 支持认证信息
                
                # 检查服务连接
                logger.info("检查依赖服务连接状态...")
                qdrant_available = self._check_service_connection(qdrant_url, "Qdrant")
                ollama_available = self._check_service_connection(ollama_url, "Ollama")
                
                if not qdrant_available:
                    logger.warning("=" * 70)
                    logger.warning(f"⚠️  Qdrant 服务不可用 ({qdrant_url})")
                    logger.warning("   启动命令: docker run -p 6333:6333 qdrant/qdrant")
                    logger.warning("   Mem0 功能将暂时不可用，但不影响其他功能运行")
                    logger.warning("=" * 70)
                    self._initialization_failed = True
                    return
                
                if not ollama_available:
                    logger.warning("=" * 70)
                    logger.warning(f"⚠️  Ollama 服务不可用 ({ollama_url})")
                    logger.warning("   启动命令: ollama serve")
                    logger.warning(f"   并确保已下载模型: ollama pull {ollama_embedding_model}")
                    logger.warning("   Mem0 功能将暂时不可用，但不影响其他功能运行")
                    logger.warning("=" * 70)
                    self._initialization_failed = True
                    return
                
                logger.info("✅ 所有依赖服务连接正常")
                
                # 临时设置一个假的 OPENAI_API_KEY，避免 Mem0 在初始化时检查失败
                # 但实际上我们会使用 Ollama，所以这个 key 不会被真正使用
                if not original_openai_key:
                    os.environ["OPENAI_API_KEY"] = "dummy-key-for-ollama-mode"
                    logger.info("临时设置虚拟 OPENAI_API_KEY 以通过 Mem0 初始化检查")
                
                # 构建配置，明确使用 Ollama
                qdrant_config = {
                    "url": qdrant_url
                }
                if qdrant_api_key:
                    qdrant_config["api_key"] = qdrant_api_key
                
                # 构建 Ollama embedding 配置
                # Mem0 的 Ollama 配置可能使用不同的参数名
                # 尝试多种可能的参数名：host, url, api_url
                embedding_config = {
                    "model": ollama_embedding_model
                }
                
                # 尝试使用 host 或 url 参数
                # 如果 URL 包含协议，可能需要提取主机和端口
                parsed_ollama = urlparse(ollama_url)
                if parsed_ollama.hostname:
                    # 尝试使用 host 参数（Mem0 可能期望这种格式）
                    if parsed_ollama.port:
                        embedding_config["host"] = f"{parsed_ollama.hostname}:{parsed_ollama.port}"
                    else:
                        embedding_config["host"] = parsed_ollama.hostname
                else:
                    # 如果没有解析到主机名，直接使用原 URL
                    embedding_config["host"] = ollama_url.replace("http://", "").replace("https://", "")
                
                # 构建 Ollama LLM 配置（同样方式）
                llm_config = {
                    "model": ollama_model_val
                }
                
                if parsed_ollama.hostname:
                    if parsed_ollama.port:
                        llm_config["host"] = f"{parsed_ollama.hostname}:{parsed_ollama.port}"
                    else:
                        llm_config["host"] = parsed_ollama.hostname
                else:
                    llm_config["host"] = ollama_url.replace("http://", "").replace("https://", "")
                
                config = {
                    "vector_store": {
                        "provider": "qdrant",
                        "config": qdrant_config
                    },
                    "embedding": {
                        "provider": "ollama",
                        "config": embedding_config
                    },
                    "llm": {
                        "provider": "ollama",
                        "config": llm_config
                    }
                }
                
                logger.info(f"Mem0Client 配置: Qdrant={qdrant_url}, Ollama={ollama_url}")
                logger.info(f"Embedding模型={ollama_embedding_model}, LLM模型={ollama_model_val}")
                
                # 尝试多种初始化方式
                try:
                    # 方式1: 使用 from_config
                    self._memory = Memory.from_config(config)
                    logger.info("Mem0Client 使用 from_config 初始化成功")
                except Exception as config_error:
                    error_msg = str(config_error)
                    logger.warning(f"from_config 失败: {error_msg}")
                    
                    # 如果错误是关于 base_url，尝试其他配置格式
                    if "base_url" in error_msg.lower() or "unexpected keyword" in error_msg.lower():
                        logger.info("尝试使用 url 参数替代 host...")
                        # 尝试使用 url 参数
                        try:
                            embedding_config_url = {"model": ollama_embedding_model, "url": ollama_url}
                            llm_config_url = {"model": ollama_model_val, "url": ollama_url}
                            config_url = {
                                "vector_store": config["vector_store"],
                                "embedding": {"provider": "ollama", "config": embedding_config_url},
                                "llm": {"provider": "ollama", "config": llm_config_url}
                            }
                            self._memory = Memory.from_config(config_url)
                            logger.info("Mem0Client 使用 url 参数初始化成功")
                            return  # URL 参数成功，直接返回
                        except Exception as url_error:
                            logger.warning(f"url 参数也失败: {str(url_error)}")
                            # 尝试最简单的配置（让 Mem0 使用默认设置）
                            try:
                                config_simple = {
                                    "vector_store": config["vector_store"],
                                    "embedding": {
                                        "provider": "ollama",
                                        "config": {"model": ollama_embedding_model}
                                    },
                                    "llm": {
                                        "provider": "ollama",
                                        "config": {"model": ollama_model_val}
                                    }
                                }
                                # 通过环境变量设置 URL
                                os.environ["OLLAMA_HOST"] = ollama_url
                                self._memory = Memory.from_config(config_simple)
                                logger.info("Mem0Client 使用简单配置+环境变量初始化成功")
                                return  # 成功则返回
                            except Exception as simple_error:
                                logger.warning(f"简单配置也失败: {str(simple_error)}")
                                # 继续尝试其他方式，不返回，让代码继续执行
                                pass
                    
                    # 如果不是 base_url 错误，继续尝试其他方式
                    if "base_url" not in error_msg.lower() and "unexpected keyword" not in error_msg.lower():
                        try:
                            # 方式2: 直接初始化 Memory，传递配置字典
                            self._memory = Memory(config=config)
                            logger.info("Mem0Client 使用直接初始化成功")
                        except Exception as direct_error:
                            logger.warning(f"直接初始化失败: {str(direct_error)}")
                        # 方式3: 尝试使用环境变量方式
                        # 确保环境变量设置正确
                        os.environ["MEM0_VECTOR_STORE_PROVIDER"] = "qdrant"
                        os.environ["MEM0_VECTOR_STORE_URL"] = qdrant_url
                        os.environ["MEM0_EMBEDDING_PROVIDER"] = "ollama"
                        os.environ["MEM0_EMBEDDING_MODEL"] = ollama_embedding_model
                        os.environ["MEM0_EMBEDDING_BASE_URL"] = ollama_url
                        
                        try:
                            self._memory = Memory.from_config(config)
                            logger.info("Mem0Client 使用环境变量方式初始化成功")
                        except Exception as env_error:
                            error_msg = str(env_error)
                            logger.error(f"所有初始化方式都失败: {error_msg}")
                            
                            # 提供更详细的错误信息
                            if "Connection refused" in error_msg or "[Errno 61]" in error_msg:
                                logger.error("=" * 60)
                                logger.error("连接被拒绝！请检查以下服务是否运行：")
                                logger.error(f"1. Qdrant: {qdrant_url}")
                                logger.error("   启动命令: docker run -p 6333:6333 qdrant/qdrant")
                                logger.error(f"2. Ollama: {ollama_url}")
                                logger.error("   启动命令: ollama serve")
                                logger.error("   并确保已下载 embedding 模型: ollama pull mxbai-embed-large")
                                logger.error("=" * 60)
                            
                            # 最后尝试：完全不设置 OPENAI_API_KEY，只使用向量存储
                            if "OPENAI_API_KEY" in os.environ:
                                del os.environ["OPENAI_API_KEY"]
                            # 只使用 Qdrant，不使用 embedding（如果 Mem0 支持）
                            minimal_config = {
                                "vector_store": config["vector_store"]
                            }
                            try:
                                self._memory = Memory.from_config(minimal_config)
                                logger.warning("Mem0Client 使用最小配置初始化（仅向量存储），embedding 功能可能不可用")
                            except Exception as minimal_error:
                                logger.error(f"最小配置也失败: {minimal_error}")
                                # 不抛出异常，允许系统继续运行
                                self._initialization_failed = True
                                logger.warning("Mem0 初始化失败，但系统将继续运行（Mem0 功能不可用）")
                
            except Exception as e:
                logger.error(f"Mem0Client 初始化失败: {str(e)}")
                self._initialization_failed = True
                logger.warning("Mem0 初始化失败，但系统将继续运行（Mem0 功能不可用）")
                # 恢复原始 OPENAI_API_KEY（如果存在）
                if original_openai_key:
                    os.environ["OPENAI_API_KEY"] = original_openai_key
                elif "OPENAI_API_KEY" in os.environ and os.environ["OPENAI_API_KEY"] == "dummy-key-for-ollama-mode":
                    del os.environ["OPENAI_API_KEY"]

    @property
    def memory(self):
        if self._memory is None:
            if self._initialization_failed:
                raise RuntimeError(
                    "Mem0 未初始化。请确保以下服务正在运行：\n"
                    "  - Qdrant: docker run -p 6333:6333 qdrant/qdrant\n"
                    "  - Ollama: ollama serve"
                )
            raise RuntimeError("Mem0 未初始化")
        return self._memory

    def is_available(self) -> bool:
        """检查 Mem0 是否可用"""
        return self._memory is not None and not self._initialization_failed

    def add_memory(
        self,
        memory: str,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """添加记忆（同步方法）"""
        if not self.is_available():
            logger.warning("Mem0 不可用，跳过添加记忆")
            return {"id": None, "status": "skipped", "reason": "Mem0 unavailable"}
        try:
            result = self._memory.add(memory, user_id=user_id, metadata=metadata)
            logger.info(f"成功添加记忆，用户ID: {user_id}")
            return result
        except Exception as e:
            logger.error(f"添加记忆失败: {str(e)}")
            raise

    def search_memories(
        self,
        query: str,
        user_id: Optional[str] = None,
        limit: int = 10,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """搜索相关记忆（同步方法）"""
        if not self.is_available():
            logger.warning("Mem0 不可用，返回空搜索结果")
            return []
        try:
            results = self._memory.search(
                query,
                user_id=user_id,
                limit=limit,
                metadata=metadata
            )
            logger.info(f"搜索到 {len(results)} 条相关记忆")
            # 转换为字典列表
            if results and isinstance(results[0], dict):
                return results
            else:
                # 如果不是字典，尝试转换
                return [{"id": getattr(r, "id", ""), "memory": getattr(r, "memory", str(r)), "metadata": getattr(r, "metadata", {})} for r in results]
        except Exception as e:
            logger.error(f"搜索记忆失败: {str(e)}")
            return []

    def get_memories(
        self,
        user_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """获取所有记忆（同步方法）"""
        if not self.is_available():
            logger.warning("Mem0 不可用，返回空列表")
            return []
        try:
            memories = self._memory.get_all(user_id=user_id, limit=limit)
            
            # 处理 None 或空列表的情况
            if not memories:
                logger.info(f"用户 {user_id} 没有记忆记录")
                return []
            
            logger.info(f"获取到 {len(memories)} 条记忆")
            
            # 转换为字典列表
            if isinstance(memories, list) and len(memories) > 0 and isinstance(memories[0], dict):
                return memories
            else:
                # 如果不是字典列表，尝试转换
                result = []
                for m in memories:
                    if isinstance(m, dict):
                        result.append(m)
                    else:
                        result.append({
                            "id": getattr(m, "id", ""),
                            "memory": getattr(m, "memory", str(m)),
                            "metadata": getattr(m, "metadata", {})
                        })
                return result
        except Exception as e:
            logger.error(f"获取记忆失败: {str(e)}", exc_info=True)
            raise

    def update_memory(
        self,
        memory_id: str,
        memory: str,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """更新记忆（同步方法）"""
        try:
            result = self._memory.update(memory_id, memory, user_id=user_id, metadata=metadata)
            logger.info(f"成功更新记忆 ID: {memory_id}")
            return result
        except Exception as e:
            logger.error(f"更新记忆失败: {str(e)}")
            raise

    def delete_memory(
        self,
        memory_id: str,
        user_id: Optional[str] = None
    ) -> bool:
        """删除记忆（同步方法）"""
        try:
            self._memory.delete(memory_id, user_id=user_id)
            logger.info(f"成功删除记忆 ID: {memory_id}")
            return True
        except Exception as e:
            logger.error(f"删除记忆失败: {str(e)}")
            raise

    def delete_all_memories(
        self,
        user_id: Optional[str] = None
    ) -> bool:
        """删除所有记忆（同步方法）"""
        try:
            self._memory.delete_all(user_id=user_id)
            logger.info(f"成功删除用户 {user_id} 的所有记忆")
            return True
        except Exception as e:
            logger.error(f"删除所有记忆失败: {str(e)}")
            raise

