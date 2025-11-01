import logging
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from qdrant_client.models import Distance

from modules.database.qdrantClient import QdrantClient

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/qdrant",
    tags=["Qdrant Vector Database"],
    responses={404: {"description": "未找到"}},
)

# 初始化 Qdrant 客户端
qdrant_client = QdrantClient()


class CreateCollectionRequest(BaseModel):
    collection_name: str
    vector_size: int = 768
    distance: str = "COSINE"  # COSINE, EUCLID, DOT


class PointStruct(BaseModel):
    id: str
    vector: List[float]
    payload: Optional[Dict[str, Any]] = None


class UpsertPointsRequest(BaseModel):
    collection_name: str
    points: List[PointStruct]


class SearchRequest(BaseModel):
    collection_name: str
    query_vector: List[float]
    limit: int = 10
    score_threshold: Optional[float] = None


class DeletePointsRequest(BaseModel):
    collection_name: str
    point_ids: List[str]


class UpdatePayloadRequest(BaseModel):
    collection_name: str
    point_id: str
    payload: Dict[str, Any]


class ScrollRequest(BaseModel):
    collection_name: str
    limit: int = 100
    offset: Optional[str] = None


@router.get("/status")
async def get_status():
    """检查 Qdrant 服务状态"""
    try:
        collections = qdrant_client.client.get_collections()
        return {
            "available": True,
            "collections_count": len(collections.collections),
            "message": "Qdrant 服务可用"
        }
    except Exception as e:
        logger.error(f"检查 Qdrant 状态失败: {str(e)}")
        return {
            "available": False,
            "message": f"Qdrant 服务不可用: {str(e)}"
        }


@router.get("/collections")
async def get_collections():
    """获取所有集合列表"""
    try:
        collections = qdrant_client.client.get_collections()
        collection_list = []
        for col in collections.collections:
            try:
                collection_info = qdrant_client.client.get_collection(col.name)
                collection_list.append({
                    "name": col.name,
                    "vectors_count": collection_info.points_count,
                    "config": {
                        "vector_size": collection_info.config.params.vectors.size if hasattr(collection_info.config.params.vectors, 'size') else None,
                        "distance": str(collection_info.config.params.vectors.distance) if hasattr(collection_info.config.params.vectors, 'distance') else None
                    }
                })
            except Exception as e:
                collection_list.append({
                    "name": col.name,
                    "error": str(e)
                })
        
        return JSONResponse(content={
            "success": True,
            "count": len(collection_list),
            "collections": collection_list
        })
    except Exception as e:
        logger.error(f"获取集合列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取集合列表失败: {str(e)}")


@router.post("/collection")
async def create_collection(request: CreateCollectionRequest):
    """创建集合"""
    try:
        # 转换距离类型
        distance_map = {
            "COSINE": Distance.COSINE,
            "EUCLID": Distance.EUCLID,
            "DOT": Distance.DOT
        }
        distance = distance_map.get(request.distance.upper(), Distance.COSINE)
        
        result = qdrant_client.create_collection(
            collection_name=request.collection_name,
            vector_size=request.vector_size,
            distance=distance
        )
        
        return JSONResponse(content={
            "success": True,
            "created": result,
            "message": f"集合 {request.collection_name} {'创建成功' if result else '已存在'}"
        })
    except Exception as e:
        logger.error(f"创建集合失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建集合失败: {str(e)}")


@router.post("/points")
async def upsert_points(request: UpsertPointsRequest):
    """插入或更新向量点"""
    try:
        from qdrant_client.models import PointStruct as QdrantPointStruct
        
        points = []
        for point in request.points:
            # 转换 ID 类型
            point_id = int(point.id) if point.id.isdigit() else point.id
            qdrant_point = QdrantPointStruct(
                id=point_id,
                vector=point.vector,
                payload=point.payload or {}
            )
            points.append(qdrant_point)
        
        result = qdrant_client.upsert_points(
            collection_name=request.collection_name,
            points=points
        )
        
        return JSONResponse(content={
            "success": result,
            "message": f"成功插入/更新 {len(points)} 个点"
        })
    except Exception as e:
        logger.error(f"插入/更新向量点失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"插入/更新向量点失败: {str(e)}")


@router.post("/search")
async def search_vectors(request: SearchRequest):
    """向量搜索"""
    try:
        results = qdrant_client.search(
            collection_name=request.collection_name,
            query_vector=request.query_vector,
            limit=request.limit,
            score_threshold=request.score_threshold
        )
        
        return JSONResponse(content={
            "success": True,
            "count": len(results),
            "results": results
        })
    except Exception as e:
        logger.error(f"向量搜索失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"向量搜索失败: {str(e)}")


@router.get("/point/{collection_name}/{point_id}")
async def get_point(collection_name: str, point_id: str):
    """获取单个点"""
    try:
        point = qdrant_client.get_point(
            collection_name=collection_name,
            point_id=point_id
        )
        
        if point is None:
            raise HTTPException(status_code=404, detail="点未找到")
        
        return JSONResponse(content={
            "success": True,
            "point": point
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取点失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取点失败: {str(e)}")


@router.put("/point/payload")
async def update_point_payload(request: UpdatePayloadRequest):
    """更新点的 payload"""
    try:
        result = qdrant_client.update_point_payload(
            collection_name=request.collection_name,
            point_id=request.point_id,
            payload=request.payload
        )
        
        return JSONResponse(content={
            "success": result,
            "message": "Payload 更新成功"
        })
    except Exception as e:
        logger.error(f"更新 payload 失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新 payload 失败: {str(e)}")


@router.delete("/points")
async def delete_points(request: DeletePointsRequest):
    """删除向量点"""
    try:
        result = qdrant_client.delete_points(
            collection_name=request.collection_name,
            point_ids=request.point_ids
        )
        
        return JSONResponse(content={
            "success": result,
            "message": f"成功删除 {len(request.point_ids)} 个点"
        })
    except Exception as e:
        logger.error(f"删除向量点失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除向量点失败: {str(e)}")


@router.post("/scroll")
async def scroll_points(request: ScrollRequest):
    """滚动获取点（分页）"""
    try:
        result = qdrant_client.scroll_points(
            collection_name=request.collection_name,
            limit=request.limit,
            offset=request.offset
        )
        
        return JSONResponse(content={
            "success": True,
            "count": len(result["points"]),
            "points": result["points"],
            "next_page_offset": result.get("next_page_offset")
        })
    except Exception as e:
        logger.error(f"滚动获取点失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"滚动获取点失败: {str(e)}")

