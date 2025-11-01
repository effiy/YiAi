import os
import logging
import threading
from typing import List, Optional, Dict, Any
from qdrant_client import QdrantClient as QdrantClientLib
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class QdrantClient:
    """Qdrant 向量数据库客户端（线程安全的单例模式）"""
    _instance = None
    _client: Optional[QdrantClientLib] = None
    _initialized: bool = False
    _lock = threading.Lock()  # 线程锁，确保线程安全

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                # 双重检查锁定模式
                if cls._instance is None:
                    cls._instance = super(QdrantClient, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        # 使用类变量确保单例模式的连接共享，添加线程锁保护
        if not QdrantClient._initialized:
            with QdrantClient._lock:
                # 双重检查，防止多线程环境下重复初始化
                if not QdrantClient._initialized:
                    try:
                        qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
                        qdrant_api_key = os.getenv("QDRANT_API_KEY", None)
                        
                        # QdrantClient 内部使用 httpx，默认会复用连接
                        # 但我们需要确保单例模式正确，避免创建多个客户端实例
                        if qdrant_api_key:
                            QdrantClient._client = QdrantClientLib(
                                url=qdrant_url,
                                api_key=qdrant_api_key,
                                timeout=30.0  # 设置超时时间
                            )
                        else:
                            QdrantClient._client = QdrantClientLib(
                                url=qdrant_url,
                                timeout=30.0  # 设置超时时间
                            )
                        
                        QdrantClient._initialized = True
                        logger.info(f"QdrantClient 连接已初始化，URL: {qdrant_url}")
                        logger.info("提示: 如果遇到 'Too many open files' 错误，请增加系统文件描述符限制")
                        logger.info("临时解决: ulimit -n 65535")
                        logger.info("永久解决: 修改 /etc/security/limits.conf 文件")
                    except Exception as e:
                        logger.error(f"QdrantClient 连接初始化失败: {str(e)}")
                        QdrantClient._initialized = False
                        raise

    @property
    def client(self):
        if QdrantClient._client is None:
            raise RuntimeError("Qdrant 连接未初始化")
        return QdrantClient._client

    def create_collection(
        self,
        collection_name: str,
        vector_size: int = 768,
        distance: Distance = Distance.COSINE
    ) -> bool:
        """创建集合（如果不存在）"""
        try:
            collections = self.client.get_collections()
            collection_names = [col.name for col in collections.collections]
            
            if collection_name not in collection_names:
                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(
                        size=vector_size,
                        distance=distance
                    )
                )
                logger.info(f"集合 {collection_name} 创建成功")
                return True
            else:
                logger.info(f"集合 {collection_name} 已存在")
                return False
        except Exception as e:
            error_msg = str(e)
            logger.error(f"创建集合失败: {error_msg}")
            
            # 如果是 "Too many open files" 错误，提供详细的解决方案
            if "Too many open files" in error_msg or "os error 24" in error_msg:
                logger.error("=" * 70)
                logger.error("检测到 'Too many open files' 错误")
                logger.error("解决方案：")
                logger.error("1. 临时解决（当前会话有效）：")
                logger.error("   ulimit -n 65535")
                logger.error("2. 永久解决（macOS）：")
                logger.error("   编辑 ~/.zshrc 或 ~/.bash_profile，添加：")
                logger.error("   ulimit -n 65535")
                logger.error("   然后执行: source ~/.zshrc")
                logger.error("3. 永久解决（Linux）：")
                logger.error("   编辑 /etc/security/limits.conf，添加：")
                logger.error("   * soft nofile 65535")
                logger.error("   * hard nofile 65535")
                logger.error("=" * 70)
            
            raise

    def upsert_points(
        self,
        collection_name: str,
        points: List[PointStruct]
    ) -> bool:
        """插入或更新向量点"""
        try:
            self.client.upsert(
                collection_name=collection_name,
                points=points
            )
            logger.info(f"成功插入/更新 {len(points)} 个点")
            return True
        except Exception as e:
            logger.error(f"插入/更新向量点失败: {str(e)}")
            raise

    def search(
        self,
        collection_name: str,
        query_vector: List[float],
        limit: int = 10,
        filter: Optional[Filter] = None,
        score_threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """向量搜索"""
        try:
            search_result = self.client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=limit,
                query_filter=filter,
                score_threshold=score_threshold
            )
            
            results = []
            for point in search_result:
                results.append({
                    "id": point.id,
                    "score": point.score,
                    "payload": point.payload
                })
            
            return results
        except Exception as e:
            logger.error(f"向量搜索失败: {str(e)}")
            raise

    def delete_points(
        self,
        collection_name: str,
        point_ids: List[str]
    ) -> bool:
        """删除向量点"""
        try:
            # 将字符串 ID 转换为整数或 UUID
            ids = [int(id) if isinstance(id, str) and id.isdigit() else id for id in point_ids]
            
            self.client.delete(
                collection_name=collection_name,
                points_selector=ids
            )
            logger.info(f"成功删除 {len(ids)} 个点")
            return True
        except Exception as e:
            logger.error(f"删除向量点失败: {str(e)}")
            raise

    def get_point(
        self,
        collection_name: str,
        point_id: str
    ) -> Optional[Dict[str, Any]]:
        """获取单个点"""
        try:
            point_id_int = int(point_id) if isinstance(point_id, str) and point_id.isdigit() else point_id
            point = self.client.retrieve(
                collection_name=collection_name,
                ids=[point_id_int]
            )
            
            if point and len(point) > 0:
                p = point[0]
                return {
                    "id": str(p.id),
                    "payload": p.payload,
                    "vector": p.vector if hasattr(p, 'vector') else None
                }
            return None
        except Exception as e:
            logger.error(f"获取点失败: {str(e)}")
            raise

    def update_point_payload(
        self,
        collection_name: str,
        point_id: str,
        payload: Dict[str, Any]
    ) -> bool:
        """更新点的 payload"""
        try:
            point_id_int = int(point_id) if isinstance(point_id, str) and point_id.isdigit() else point_id
            
            self.client.set_payload(
                collection_name=collection_name,
                payload=payload,
                points=[point_id_int]
            )
            logger.info(f"成功更新点 {point_id} 的 payload")
            return True
        except Exception as e:
            logger.error(f"更新点 payload 失败: {str(e)}")
            raise

    def scroll_points(
        self,
        collection_name: str,
        limit: int = 100,
        filter: Optional[Filter] = None,
        offset: Optional[str] = None
    ) -> Dict[str, Any]:
        """滚动获取点（用于分页）"""
        try:
            result = self.client.scroll(
                collection_name=collection_name,
                limit=limit,
                scroll_filter=filter,
                offset=offset
            )
            
            points = []
            for point in result[0]:
                points.append({
                    "id": str(point.id),
                    "payload": point.payload,
                    "vector": point.vector if hasattr(point, 'vector') else None
                })
            
            return {
                "points": points,
                "next_page_offset": result[1]
            }
        except Exception as e:
            logger.error(f"滚动获取点失败: {str(e)}")
            raise

