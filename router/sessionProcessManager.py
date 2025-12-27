"""
会话管理业务流程管理模块
基于《有效需求分析（第2版）》和SOP标准

业务流程：
1. 会话创建流程
2. 会话更新流程
3. 会话查询流程
4. 会话删除流程
"""
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class SessionProcessManager:
    """会话管理业务流程管理器"""
    
    def __init__(self, session_service):
        self.session_service = session_service
    
    async def create_session_process(
        self,
        session_data: Dict[str, Any],
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        会话创建流程（参考SOP任务6-9：业务流程识别与分析）
        
        业务流程八要素：
        1. 流程起点：用户请求创建会话
        2. 流程终点：会话创建成功并返回
        3. 输入：会话数据（title, url, messages等）
        4. 输出：创建成功的会话数据
        5. 活动步骤：
           - 步骤1：验证输入数据
           - 步骤2：生成会话ID
           - 步骤3：准备会话文档
           - 步骤4：保存到数据库
           - 步骤5：返回结果
        6. 执行者：SessionService
        7. 依赖关系：顺序执行
        8. 管控点：数据验证、权限检查
        9. 异常处理：数据格式错误、数据库错误
        10. 监管需求：记录操作日志
        
        Args:
            session_data: 会话数据
            user_id: 用户ID
        
        Returns:
            创建结果
        """
        try:
            # 步骤1：验证输入数据（管控点）
            validation_result = self._validate_session_data(session_data)
            if not validation_result["valid"]:
                raise ValueError(f"数据验证失败: {validation_result['error']}")
            
            # 步骤2：生成会话ID
            session_id = self._generate_session_id(session_data)
            
            # 步骤3：准备会话文档
            session_doc = self._prepare_session_doc(session_data, session_id, user_id)
            
            # 步骤4：保存到数据库
            result = await self.session_service.save_session(session_data, user_id=user_id)
            
            # 步骤5：返回结果
            logger.info(f"会话创建流程完成: {session_id}")
            return {
                "success": True,
                "session_id": result["session_id"],
                "is_new": result.get("is_new", True),
                "process_steps": [
                    "数据验证",
                    "生成会话ID",
                    "准备会话文档",
                    "保存到数据库",
                    "返回结果"
                ]
            }
        except Exception as e:
            logger.error(f"会话创建流程失败: {str(e)}", exc_info=True)
            raise
    
    async def update_session_process(
        self,
        session_id: str,
        session_data: Dict[str, Any],
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        会话更新流程（参考SOP任务6-9：业务流程识别与分析）
        
        业务流程八要素：
        1. 流程起点：用户请求更新会话
        2. 流程终点：会话更新成功并返回
        3. 输入：会话ID和更新数据
        4. 输出：更新后的会话数据
        5. 活动步骤：
           - 步骤1：验证会话是否存在
           - 步骤2：验证更新数据
           - 步骤3：准备更新文档
           - 步骤4：更新数据库
           - 步骤5：返回结果
        6. 执行者：SessionService
        7. 依赖关系：顺序执行
        8. 管控点：权限检查、数据验证
        9. 异常处理：会话不存在、数据格式错误
        10. 监管需求：记录操作日志
        
        Args:
            session_id: 会话ID
            session_data: 更新数据
            user_id: 用户ID
        
        Returns:
            更新结果
        """
        try:
            # 步骤1：验证会话是否存在
            existing = await self.session_service.get_session(session_id, user_id=user_id)
            if not existing:
                raise ValueError(f"会话 {session_id} 不存在")
            
            # 步骤2：验证更新数据（管控点）
            validation_result = self._validate_update_data(session_data)
            if not validation_result["valid"]:
                raise ValueError(f"数据验证失败: {validation_result['error']}")
            
            # 步骤3：准备更新文档
            update_doc = self._prepare_update_doc(session_data, existing)
            
            # 步骤4：更新数据库
            result = await self.session_service.update_session(session_id, session_data, user_id=user_id)
            
            # 步骤5：返回结果
            logger.info(f"会话更新流程完成: {session_id}")
            return {
                "success": True,
                "session_id": result["session_id"],
                "process_steps": [
                    "验证会话存在",
                    "验证更新数据",
                    "准备更新文档",
                    "更新数据库",
                    "返回结果"
                ]
            }
        except Exception as e:
            logger.error(f"会话更新流程失败: {str(e)}", exc_info=True)
            raise
    
    async def query_session_process(
        self,
        session_id: str,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        会话查询流程（参考SOP任务6-9：业务流程识别与分析）
        
        业务流程八要素：
        1. 流程起点：用户请求查询会话
        2. 流程终点：返回会话数据
        3. 输入：会话ID
        4. 输出：会话数据
        5. 活动步骤：
           - 步骤1：验证会话ID
           - 步骤2：查询数据库
           - 步骤3：验证权限
           - 步骤4：格式化数据
           - 步骤5：返回结果
        6. 执行者：SessionService
        7. 依赖关系：顺序执行
        8. 管控点：权限检查
        9. 异常处理：会话不存在、权限不足
        10. 监管需求：记录查询日志
        
        Args:
            session_id: 会话ID
            user_id: 用户ID
        
        Returns:
            查询结果
        """
        try:
            # 步骤1：验证会话ID
            if not session_id:
                raise ValueError("会话ID不能为空")
            
            # 步骤2：查询数据库
            session_data = await self.session_service.get_session(session_id, user_id=user_id)
            
            # 步骤3：验证权限（如果会话不存在，可能是权限问题）
            if not session_data:
                logger.warning(f"会话 {session_id} 不存在或无权限访问")
                return {
                    "success": False,
                    "error": "会话不存在或无权限访问",
                    "process_steps": [
                        "验证会话ID",
                        "查询数据库",
                        "验证权限",
                        "返回结果"
                    ]
                }
            
            # 步骤4：格式化数据（已在service层完成）
            # 步骤5：返回结果
            logger.info(f"会话查询流程完成: {session_id}")
            return {
                "success": True,
                "session_data": session_data,
                "process_steps": [
                    "验证会话ID",
                    "查询数据库",
                    "验证权限",
                    "格式化数据",
                    "返回结果"
                ]
            }
        except Exception as e:
            logger.error(f"会话查询流程失败: {str(e)}", exc_info=True)
            raise
    
    async def delete_session_process(
        self,
        session_id: str,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        会话删除流程（参考SOP任务6-9：业务流程识别与分析）
        
        业务流程八要素：
        1. 流程起点：用户请求删除会话
        2. 流程终点：会话删除成功
        3. 输入：会话ID
        4. 输出：删除结果
        5. 活动步骤：
           - 步骤1：验证会话是否存在
           - 步骤2：验证权限
           - 步骤3：删除数据库记录
           - 步骤4：清理关联数据
           - 步骤5：返回结果
        6. 执行者：SessionService
        7. 依赖关系：顺序执行
        8. 管控点：权限检查、确认删除
        9. 异常处理：会话不存在、权限不足
        10. 监管需求：记录删除日志
        
        Args:
            session_id: 会话ID
            user_id: 用户ID
        
        Returns:
            删除结果
        """
        try:
            # 步骤1：验证会话是否存在
            existing = await self.session_service.get_session(session_id, user_id=user_id)
            if not existing:
                logger.warning(f"会话 {session_id} 不存在，无法删除")
                return {
                    "success": False,
                    "error": "会话不存在",
                    "process_steps": [
                        "验证会话存在",
                        "返回结果"
                    ]
                }
            
            # 步骤2：验证权限（已在service层完成）
            # 步骤3：删除数据库记录
            success = await self.session_service.delete_session(session_id, user_id=user_id)
            
            # 步骤4：清理关联数据（已在service层完成，如更新新闻状态）
            # 步骤5：返回结果
            if success:
                logger.info(f"会话删除流程完成: {session_id}")
                return {
                    "success": True,
                    "session_id": session_id,
                    "process_steps": [
                        "验证会话存在",
                        "验证权限",
                        "删除数据库记录",
                        "清理关联数据",
                        "返回结果"
                    ]
                }
            else:
                return {
                    "success": False,
                    "error": "删除失败",
                    "process_steps": [
                        "验证会话存在",
                        "验证权限",
                        "删除数据库记录",
                        "返回结果"
                    ]
                }
        except Exception as e:
            logger.error(f"会话删除流程失败: {str(e)}", exc_info=True)
            raise
    
    def _validate_session_data(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """验证会话数据"""
        if not session_data:
            return {"valid": False, "error": "会话数据不能为空"}
        
        # 基本验证
        if "title" in session_data and not isinstance(session_data["title"], str):
            return {"valid": False, "error": "标题必须是字符串"}
        
        if "messages" in session_data and not isinstance(session_data["messages"], list):
            return {"valid": False, "error": "消息必须是列表"}
        
        return {"valid": True}
    
    def _validate_update_data(self, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """验证更新数据"""
        if not update_data:
            return {"valid": False, "error": "更新数据不能为空"}
        
        # 基本验证
        if "title" in update_data and not isinstance(update_data["title"], str):
            return {"valid": False, "error": "标题必须是字符串"}
        
        if "messages" in update_data and not isinstance(update_data["messages"], list):
            return {"valid": False, "error": "消息必须是列表"}
        
        return {"valid": True}
    
    def _generate_session_id(self, session_data: Dict[str, Any]) -> str:
        """生成会话ID"""
        return self.session_service.generate_session_id(session_data.get("url"))
    
    def _prepare_session_doc(
        self,
        session_data: Dict[str, Any],
        session_id: str,
        user_id: Optional[str]
    ) -> Dict[str, Any]:
        """准备会话文档"""
        current_time = int(datetime.now(timezone.utc).timestamp() * 1000)
        return {
            "key": session_id,
            "user_id": user_id or "default_user",
            "url": session_data.get("url", ""),
            "title": session_data.get("title", ""),
            "pageTitle": session_data.get("pageTitle", ""),
            "pageDescription": session_data.get("pageDescription", ""),
            "pageContent": session_data.get("pageContent", ""),
            "messages": session_data.get("messages", []),
            "tags": session_data.get("tags", []),
            "isFavorite": session_data.get("isFavorite", False),
            "createdAt": session_data.get("createdAt") or current_time,
            "updatedAt": session_data.get("updatedAt") or current_time,
            "lastAccessTime": session_data.get("lastAccessTime") or current_time
        }
    
    def _prepare_update_doc(
        self,
        update_data: Dict[str, Any],
        existing: Dict[str, Any]
    ) -> Dict[str, Any]:
        """准备更新文档"""
        update_doc = {}
        current_time = int(datetime.now(timezone.utc).timestamp() * 1000)
        
        # 只更新有变化的字段
        for field in ["url", "title", "pageTitle", "pageDescription", "pageContent", "messages", "tags", "isFavorite"]:
            if field in update_data and update_data[field] != existing.get(field):
                update_doc[field] = update_data[field]
        
        if update_doc:
            update_doc["updatedAt"] = current_time
            update_doc["lastAccessTime"] = current_time
        
        return update_doc

