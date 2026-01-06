import logging
import re
import uuid
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from bson import ObjectId
from pymongo import ReturnDocument

from core.database import db
from core.config import settings

logger = logging.getLogger(__name__)

class MongoDBService:
    """
    MongoDB 数据库服务封装
    提供通用的数据库操作方法和数据清洗工具
    """
    def __init__(self):
        """初始化 MongoDB 服务实例"""
        self.db_client = db

    async def ensure_initialized(self):
        """确保数据库连接已初始化"""
        await self.db_client.initialize()

    def is_valid_date(self, date_str: str) -> bool:
        """
        验证日期字符串格式是否有效 (YYYY-MM-DD)
        
        Args:
            date_str: 日期字符串
            
        Returns:
            bool: 是否有效
        """
        if not isinstance(date_str, str):
            return False
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            return True
        except ValueError:
            return False

    def is_number(self, value: Any) -> bool:
        """
        验证值是否为数字
        
        Args:
            value: 待验证的值
            
        Returns:
            bool: 是否为数字
        """
        if value is None:
            return False
        try:
            float(value)
            return True
        except (ValueError, TypeError):
            return False

    def parse_published_date(self, date_str: str) -> Optional[datetime]:
        """
        解析多种格式的发布日期
        
        Args:
            date_str: 日期字符串
            
        Returns:
            Optional[datetime]: 解析后的 datetime 对象，失败返回 None
        """
        if not date_str:
            return None

        date_formats = [
            '%a, %d %b %Y %H:%M:%S %z',
            '%a, %d %b %Y %H:%M:%S',
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d',
            '%d %b %Y',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%dT%H:%M:%S%z',
        ]

        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue

        return None

    def build_published_date_filter(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """
        构建发布日期查询过滤器
        
        Args:
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            
        Returns:
            Dict[str, Any]: MongoDB 查询条件
        """
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')

            month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                          'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

            date_patterns = []
            iso_date_values = []
            current_dt = start_dt

            while current_dt <= end_dt:
                year = current_dt.year
                month = current_dt.month
                day = current_dt.day
                month_name = month_names[month - 1]

                date_patterns.extend([
                    f'{year}-{month:02d}-{day:02d}',
                    f'{day:02d} {month_name} {year}',
                    f'{day} {month_name} {year}',
                ])

                iso_date_values.append(f'{year}-{month:02d}-{day:02d}')
                current_dt += timedelta(days=1)

            date_patterns = list(set(date_patterns))
            iso_date_values = list(set(iso_date_values))

            if not date_patterns:
                return {}

            or_conditions = []
            for pattern in date_patterns:
                or_conditions.append({'pubDate': {'$regex': pattern, '$options': 'i'}})
                or_conditions.append({'published': {'$regex': pattern, '$options': 'i'}})

            if iso_date_values:
                or_conditions.append({'isoDate': {'$in': iso_date_values}})
                for iso_date in iso_date_values:
                    or_conditions.append({'isoDate': {'$regex': iso_date, '$options': 'i'}})

            return {'$or': or_conditions}
        except ValueError:
            return {}

    def build_filter(self, query_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        根据查询参数构建 MongoDB 过滤条件
        
        Args:
            query_params: 查询参数字典
            
        Returns:
            Dict[str, Any]: MongoDB 过滤字典
        """
        filter_dict = {}

        for key, value in query_params.items():
            if not value:
                continue

            if key == 'isoDate' and isinstance(value, str):
                if ',' in value:
                    date_parts = [term.strip() for term in value.split(',') if term.strip()]
                    if len(date_parts) == 2:
                        start_date, end_date = date_parts
                        if self.is_valid_date(start_date) and self.is_valid_date(end_date):
                            published_filter = self.build_published_date_filter(start_date, end_date)
                            if published_filter:
                                filter_dict.update(published_filter)
                            continue
                else:
                    if self.is_valid_date(value):
                        published_filter = self.build_published_date_filter(value, value)
                        if published_filter:
                            filter_dict.update(published_filter)
                            continue

            if hasattr(value, '__iter__') and not isinstance(value, (str, bytes, dict)):
                value_list = list(value) if not isinstance(value, list) else value
                if not value_list:
                    continue

                if len(value_list) == 2:
                    start, end = value_list
                    if self.is_valid_date(start) and self.is_valid_date(end):
                        filter_dict[key] = {'$gte': start, '$lt': end}
                    elif self.is_number(start) and self.is_number(end):
                        filter_dict[key] = {'$gte': float(start), '$lt': float(end)}
                    elif self.is_number(start):
                        filter_dict[key] = {'$gte': float(start)}
                    elif self.is_number(end):
                        filter_dict[key] = {'$lt': float(end)}
                else:
                    filter_dict[key] = {'$in': value_list}

            elif isinstance(value, str):
                if ',' in value:
                    search_terms = [term.strip() for term in value.split(',') if term.strip()]
                    if search_terms:
                        if '$or' in filter_dict:
                            filter_dict['$or'].extend([
                                {key: re.compile(f'.*{re.escape(term)}.*', re.IGNORECASE)}
                                for term in search_terms
                            ])
                        else:
                            filter_dict['$or'] = [
                                {key: re.compile(f'.*{re.escape(term)}.*', re.IGNORECASE)}
                                for term in search_terms
                            ]
                else:
                    filter_dict[key] = re.compile(f'.*{re.escape(value)}.*', re.IGNORECASE)

            elif isinstance(value, (int, float, bool)):
                filter_dict[key] = value

        return filter_dict

    def get_current_time(self) -> str:
        """
        获取当前 UTC 时间字符串
        
        Returns:
            str: 格式化后的时间字符串 (YYYY-MM-DD HH:MM:SS)
        """
        return datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

    def validate_collection_name(self, cname: Optional[str]) -> str:
        """
        验证集合名称是否存在
        
        Args:
            cname: 集合名称
            
        Returns:
            str: 验证后的集合名称
            
        Raises:
            ValueError: 如果集合名称为空
        """
        if not cname:
            raise ValueError("必须提供集合名称(cname)")
        return cname

    def build_sort_list(self, sort_param: str, sort_order: int) -> List[tuple]:
        """
        构建排序列表
        
        Args:
            sort_param: 排序字段名
            sort_order: 排序方向 (1 或 -1)
            
        Returns:
            List[tuple]: 排序条件列表
        """
        sort_list = []
        if sort_param == 'order':
            sort_list.append(('order', 1))
        else:
            sort_list.append((sort_param, sort_order))

        if sort_param != 'updatedTime':
            sort_list.append(('updatedTime', -1))
        if sort_param != 'createdTime':
            sort_list.append(('createdTime', -1))
        
        return sort_list

    async def query_documents(self, cname: str, query_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        查询文档列表
        
        Args:
            cname: 集合名称
            query_params: 查询参数
            
        Returns:
            Dict[str, Any]: 包含列表数据和分页信息的字典
        """
        await self.ensure_initialized()
        
        cname = self.validate_collection_name(cname)
        
        fields_param = query_params.pop('fields', None) or query_params.pop('select', None)
        exclude_fields_param = query_params.pop('excludeFields', None) or query_params.pop('exclude', None)

        try:
            page_num = max(1, int(query_params.pop('pageNum', 1)))
            page_size = min(8000, max(1, int(query_params.pop('pageSize', 2000))))
        except ValueError:
            raise ValueError("分页参数必须是有效的整数")

        sort_param = query_params.pop('orderBy', 'timestamp' if cname == 'apis' else 'order')
        sort_order = -1 if query_params.pop('orderType', 'asc').lower() == 'desc' else 1

        filter_dict = self.build_filter(query_params)
        logger.info(f"Querying collection: {cname}, Filter: {filter_dict}")
        sort_list = self.build_sort_list(sort_param, sort_order)
        
        projection = {'_id': 0}
        if fields_param:
            fields = [f.strip() for f in str(fields_param).split(',') if f.strip()]
            if 'key' not in fields:
                fields.append('key')
            projection = {'_id': 0, **{f: 1 for f in fields}}
        elif exclude_fields_param:
            exclude_fields = [f.strip() for f in str(exclude_fields_param).split(',') if f.strip()]
            projection = {'_id': 0, **{f: 0 for f in exclude_fields}}

        collection = self.db_client.db[cname]
        
        cursor = collection.find(filter_dict, projection) \
            .sort(sort_list) \
            .skip((page_num - 1) * page_size) \
            .limit(page_size)

        data = [doc async for doc in cursor]
        total = await collection.count_documents(filter_dict)
        total_pages = (total + page_size - 1) // page_size

        return {
            'list': data,
            'total': total,
            'pageNum': page_num,
            'pageSize': page_size,
            'totalPages': total_pages
        }

    async def get_document_detail(self, cname: str, id: str) -> Dict[str, Any]:
        await self.ensure_initialized()
        
        collection = self.db_client.db[cname]
        document = await collection.find_one({'key': id}, {'_id': 0})

        if not document:
            raise ValueError(f"未找到ID为 {id} 的数据")
        
        return document

    async def create_document(self, cname: str, data: Dict[str, Any]) -> Dict[str, Any]:
        await self.ensure_initialized()
        
        cname = self.validate_collection_name(cname)
        if not data:
            raise ValueError("创建数据不能为空")

        collection = self.db_client.db[cname]

        if cname == 'rss':
            link = data.get('link')
            if link:
                existing_item = await collection.find_one({'link': link})
                if existing_item:
                    raise ValueError(f"link 字段值 '{link}' 已存在，不能重复创建")

        data_copy = {k: (str(v) if isinstance(v, ObjectId) else v) for k, v in data.items()}
        current_time = self.get_current_time()
        data_copy.update({
            'key': str(uuid.uuid4()),
            'createdTime': current_time,
            'updatedTime': current_time
        })

        try:
            max_order_doc = await collection.find_one(
                sort=[("order", -1)],
                projection={"order": 1}
            )
            max_order = max_order_doc.get("order", 0) if max_order_doc else 0
            data_copy['order'] = max_order + 1
        except Exception as e:
            logger.warning(f"获取最大排序值失败: {str(e)}")
            data_copy['order'] = 1

        try:
            await collection.insert_one(data_copy)
        except Exception as e:
            if 'duplicate key' in str(e).lower() or 'E11000' in str(e):
                if cname == 'rss':
                    raise ValueError(f"link 字段值 '{data_copy.get('link', '')}' 已存在，不能重复创建")
                else:
                    raise ValueError(f"数据创建失败: 唯一性约束冲突")
            raise

        return {'key': data_copy['key']}

    async def update_document(self, cname: str, data: Dict[str, Any]) -> str:
        """
        更新文档
        
        Args:
            cname: 集合名称
            data: 更新数据（必须包含 key 或 link）
            
        Returns:
            str: 更新后的文档 key
            
        Raises:
            ValueError: 缺少标识字段或违反约束
        """
        await self.ensure_initialized()
        
        cname = self.validate_collection_name(cname)
        
        key = data.get('key')
        link = data.get('link')
        content = data.get('content')

        if key:
            query_filter = {'key': key}
            identifier = key
            identifier_type = 'key'
        elif link:
            query_filter = {'link': link}
            identifier = link
            identifier_type = 'link'
        else:
            raise ValueError("更新数据时必须提供key字段或link字段")

        excluded_fields = ['key'] if key else []
        data_for_check = {k: v for k, v in data.items() if k not in excluded_fields}
        if not data_for_check:
            raise ValueError("更新数据不能为空")

        collection = self.db_client.db[cname]

        if cname == settings.collection_rss:
            new_link = data.get('link')
            if new_link:
                existing_item = await collection.find_one({'link': new_link})
                if existing_item:
                    existing_key = existing_item.get('key')
                    if key:
                        if existing_key != key:
                            raise ValueError(f"link 字段值 '{new_link}' 已被其他记录使用（key: {existing_key}）")
                    elif link:
                        if new_link != link and existing_key:
                            raise ValueError(f"link 字段值 '{new_link}' 已被其他记录使用（key: {existing_key}）")
            
            if key:
                data['key'] = key
            
            if content:
                data['contentHash'] = hashlib.md5(content.encode('utf-8')).hexdigest()

        update_data = {k: v for k, v in data.items() if k not in (['key'] if key else [])}
        update_data['updatedTime'] = self.get_current_time()

        try:
            result = await collection.find_one_and_update(
                query_filter,
                {"$set": update_data},
                return_document=ReturnDocument.AFTER
            )
        except Exception as e:
            if 'duplicate key' in str(e).lower() or 'E11000' in str(e):
                if cname == settings.collection_rss:
                    new_link = data.get('link')
                    raise ValueError(f"link 字段值 '{new_link}' 已存在，不能重复")
                else:
                    raise ValueError(f"数据更新失败: 唯一性约束冲突")
            raise

        if not result:
            raise ValueError(f"未找到{identifier_type}为 {identifier} 的数据")

        return result.get('key', identifier)

    async def delete_document(self, cname: str, id: str) -> bool:
        """
        删除文档
        
        Args:
            cname: 集合名称
            id: 文档 Key
            
        Returns:
            bool: 是否删除成功
            
        Raises:
            ValueError: 删除失败（未找到）
        """
        await self.ensure_initialized()
        
        cname = self.validate_collection_name(cname)
        
        collection = self.db_client.db[cname]
        result = await collection.delete_one({'key': id})
        
        if result.deleted_count == 0:
            raise ValueError(f"未找到ID为 {id} 的数据，删除失败")
            
        return True

