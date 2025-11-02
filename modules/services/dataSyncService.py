import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from modules.database.mongoClient import MongoClient

logger = logging.getLogger(__name__)

class DataSyncService:
    """数据同步服务 - 同步YiPet的各类数据到后端"""
    
    def __init__(self):
        self.mongo_client = MongoClient()
        self.collection_name = "pet_data_sync"
        
    async def initialize(self):
        """初始化服务"""
        await self.mongo_client.initialize()
    
    async def save_data(
        self,
        user_id: str,
        data_type: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        保存YiPet数据到后端
        
        Args:
            user_id: 用户ID
            data_type: 数据类型（petGlobalState, petSettings, petChatWindowState, roleConfigs, sessionSidebarWidth, contextSwitchEnabled）
            data: 数据内容
        
        Returns:
            保存结果
        """
        try:
            await self.initialize()
            
            # 构建文档
            document = {
                "user_id": user_id,
                "data_type": data_type,
                "data": data,
                "updated_at": datetime.now(timezone.utc),
                "created_at": datetime.now(timezone.utc)
            }
            
            # 检查是否已存在
            existing = await self.mongo_client.find_one(
                collection_name=self.collection_name,
                query={
                    "user_id": user_id,
                    "data_type": data_type
                }
            )
            
            if existing:
                # 更新现有文档
                document["created_at"] = existing.get("created_at", datetime.now(timezone.utc))
                result = await self.mongo_client.update_one(
                    collection_name=self.collection_name,
                    query={
                        "user_id": user_id,
                        "data_type": data_type
                    },
                    update=document
                )
                logger.info(f"已更新数据同步记录: user_id={user_id}, data_type={data_type}")
            else:
                # 创建新文档
                result = await self.mongo_client.insert_one(
                    collection_name=self.collection_name,
                    document=document
                )
                logger.info(f"已创建数据同步记录: user_id={user_id}, data_type={data_type}")
            
            return {
                "success": True,
                "user_id": user_id,
                "data_type": data_type,
                "message": "数据同步成功"
            }
        except Exception as e:
            logger.error(f"保存数据同步失败: {str(e)}", exc_info=True)
            raise
    
    async def get_data(
        self,
        user_id: str,
        data_type: str
    ) -> Optional[Dict[str, Any]]:
        """
        获取YiPet数据
        
        Args:
            user_id: 用户ID
            data_type: 数据类型
        
        Returns:
            数据内容，如果不存在返回None
        """
        try:
            await self.initialize()
            
            result = await self.mongo_client.find_one(
                collection_name=self.collection_name,
                query={
                    "user_id": user_id,
                    "data_type": data_type
                }
            )
            
            if result:
                return result.get("data")
            return None
        except Exception as e:
            logger.error(f"获取数据同步失败: {str(e)}", exc_info=True)
            raise
    
    async def get_all_data(
        self,
        user_id: str
    ) -> Dict[str, Any]:
        """
        获取用户的所有同步数据
        
        Args:
            user_id: 用户ID
        
        Returns:
            所有数据，按data_type分类
        """
        try:
            await self.initialize()
            
            results = await self.mongo_client.find_many(
                collection_name=self.collection_name,
                query={"user_id": user_id}
            )
            
            data_dict = {}
            for result in results:
                data_type = result.get("data_type")
                if data_type:
                    data_dict[data_type] = result.get("data", {})
            
            return data_dict
        except Exception as e:
            logger.error(f"获取所有数据同步失败: {str(e)}", exc_info=True)
            raise
    
    async def delete_data(
        self,
        user_id: str,
        data_type: Optional[str] = None
    ) -> bool:
        """
        删除数据同步记录
        
        Args:
            user_id: 用户ID
            data_type: 数据类型（如果为None，删除该用户的所有数据）
        
        Returns:
            是否删除成功
        """
        try:
            await self.initialize()
            
            query = {"user_id": user_id}
            if data_type:
                query["data_type"] = data_type
            
            result = await self.mongo_client.delete_many(
                collection_name=self.collection_name,
                query=query
            )
            
            return result > 0
        except Exception as e:
            logger.error(f"删除数据同步失败: {str(e)}", exc_info=True)
            raise
    
    async def batch_save_data(
        self,
        user_id: str,
        data_dict: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        批量保存多个类型的数据
        
        Args:
            user_id: 用户ID
            data_dict: 数据字典，key为data_type，value为data
        
        Returns:
            保存结果
        """
        try:
            results = []
            for data_type, data in data_dict.items():
                result = await self.save_data(
                    user_id=user_id,
                    data_type=data_type,
                    data=data
                )
                results.append(result)
            
            return {
                "success": True,
                "user_id": user_id,
                "count": len(results),
                "results": results
            }
        except Exception as e:
            logger.error(f"批量保存数据同步失败: {str(e)}", exc_info=True)
            raise

