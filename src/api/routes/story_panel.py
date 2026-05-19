import logging
import os
import re
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import httpx
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from core.response import success, fail
from core.error_codes import ErrorCode

logger = logging.getLogger(__name__)
router = APIRouter()

PANEL_ROOT = Path("docs/故事任务面板")
NAME_KEBAB_RE = re.compile(r"^[a-z][a-z0-9]*(-[a-z][a-z0-9]*)*$")  # kebab-case


def _validate_name(name: str) -> None:
    if name != os.path.basename(name) or name.startswith(".") or ".." in name:
        raise HTTPException(status_code=422, detail=f"name 含非法路径字符: {name}")
    if not NAME_KEBAB_RE.match(name):
        raise HTTPException(status_code=400, detail=f"name 必须为 kebab-case: {name}")


def _list_story_dirs() -> list[Path]:
    if not PANEL_ROOT.exists():
        return []
    return sorted(p for p in PANEL_ROOT.iterdir() if p.is_dir())


def _file_ends_with(story_dir: Path, suffix: str) -> bool:
    """检查目录下是否存在以 suffix 结尾的 .md 文件（兼容有无 project 前缀的旧命名）"""
    return any(f.name.endswith(suffix) for f in story_dir.iterdir() if f.suffix == ".md")


def _determine_status(story_dir: Path) -> str:
    if not _file_ends_with(story_dir, "01-故事任务.md"):
        return "not_started"

    has_02 = _file_ends_with(story_dir, "02-用户使用场景.md")
    has_05 = _file_ends_with(story_dir, "05-测试用例评审.md")
    has_03 = _file_ends_with(story_dir, "03-后端技术评审.md")
    has_04 = _file_ends_with(story_dir, "04-前端技术评审.md")
    docs_baseline = has_02 and has_05

    type_file = story_dir / ".memory" / "story-type.json"
    story_type = _read_story_type(type_file)
    if story_type in ("backend", "fullstack"):
        docs_baseline = docs_baseline and has_03
    if story_type in ("frontend", "fullstack"):
        docs_baseline = docs_baseline and has_04

    if not docs_baseline:
        return "docs_in_progress"

    has_06 = _file_ends_with(story_dir, "06-后端实施报告.md")
    has_07 = _file_ends_with(story_dir, "07-前端实施报告.md")
    has_impl_report = has_06 or has_07

    if not has_impl_report:
        return "docs_done"

    has_08 = _file_ends_with(story_dir, "08-测试用例报告.md")
    if not has_08:
        return "code_in_progress"

    state_file = story_dir / ".memory" / "rui-state.json"
    if state_file.exists():
        try:
            state = json.loads(state_file.read_text())
            if state.get("blocked"):
                return "blocked"
        except Exception:
            pass

    return "code_done"


def _infer_type(story_dir: Path) -> str:
    has_03 = _file_ends_with(story_dir, "03-后端技术评审.md")
    has_04 = _file_ends_with(story_dir, "04-前端技术评审.md")
    has_06 = _file_ends_with(story_dir, "06-后端实施报告.md")
    has_07 = _file_ends_with(story_dir, "07-前端实施报告.md")
    if (has_03 or has_06) and (has_04 or has_07):
        return "fullstack"
    if has_03 or has_06:
        return "backend"
    if has_04 or has_07:
        return "frontend"
    return "meta"


def _read_story_type(path: Path) -> str:
    try:
        data = json.loads(path.read_text())
        return data.get("type", "meta")
    except Exception:
        return "meta"


def _count_md_files(story_dir: Path) -> int:
    return len([f for f in story_dir.iterdir() if f.suffix == ".md"])


def _last_modified(story_dir: Path) -> str:
    max_mtime = 0.0
    for f in story_dir.rglob("*"):
        if f.is_file():
            mtime = f.stat().st_mtime
            if mtime > max_mtime:
                max_mtime = mtime
    if max_mtime == 0.0:
        return ""
    return datetime.fromtimestamp(max_mtime, tz=timezone.utc).isoformat()


def _get_branch(name: str) -> Optional[str]:
    branch_name = f"feat/{name}"
    try:
        result = subprocess.run(
            ["git", "branch", "--list", branch_name],
            capture_output=True, text=True, timeout=5,
        )
        output = result.stdout.strip()
        if output:
            return output.lstrip("*").strip()
    except Exception:
        pass
    return None


def _parse_story_path(name: str) -> Path:
    return PANEL_ROOT / name


# --- Request models ---

class SyncRequest(BaseModel):
    names: Optional[list[str]] = Field(default=None, description="故事名列表 (kebab-case)，为空时返回推荐列表")


# --- Routes ---

@router.get("/api/story-panel/overview")
async def overview():
    """状态概览：按状态聚合 + 最近 5 个活动故事"""
    stories = []
    for sdir in _list_story_dirs():
        name = sdir.name
        status = _determine_status(sdir)
        modified = _last_modified(sdir)
        stories.append({
            "name": name,
            "status": status,
            "modified": modified,
        })

    summary = {
        "code_done": 0, "code_in_progress": 0, "docs_done": 0,
        "docs_in_progress": 0, "not_started": 0, "blocked": 0,
    }
    for s in stories:
        key = s["status"]
        if key in summary:
            summary[key] += 1
    summary["total"] = len(stories)

    stories.sort(key=lambda s: s["modified"] or "", reverse=True)
    recent = stories[:5]

    return success(data={"summary": summary, "recent": recent})


@router.get("/api/story-panel/stories")
async def list_stories():
    """进度全景：所有故事详情表格"""
    items = []
    for sdir in _list_story_dirs():
        name = sdir.name
        status = _determine_status(sdir)
        files = _count_md_files(sdir)
        last_modified = _last_modified(sdir)
        story_type = _infer_type(sdir)
        branch = _get_branch(name)
        items.append({
            "name": name,
            "status": status,
            "files": files,
            "last_modified": last_modified,
            "type": story_type,
            "branch": branch,
        })

    items.sort(key=lambda s: s["last_modified"] or "", reverse=True)
    return success(data={"stories": items})


@router.get("/api/story-panel/stories/{name}")
async def show_story(name: str):
    """单故事详情"""
    _validate_name(name)

    sdir = _parse_story_path(name)
    if not sdir.is_dir():
        return fail(error=ErrorCode.DATA_NOT_FOUND, message=f"故事不存在: {name}")

    files = []
    for f in sorted(sdir.iterdir()):
        if f.is_file() and f.suffix == ".md":
            stat = f.stat()
            files.append({
                "name": f.name,
                "size": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
            })

    story_type = _infer_type(sdir)
    branch = _get_branch(name)

    metadata = {"status": _determine_status(sdir), "stage": None, "block_reason": None}
    state_file = sdir / ".memory" / "rui-state.json"
    if state_file.exists():
        try:
            state = json.loads(state_file.read_text())
            metadata["stage"] = state.get("current_stage")
            metadata["block_reason"] = state.get("block_reason")
        except Exception:
            pass

    return success(data={
        "name": name,
        "directory": str(sdir) + "/",
        "type": story_type,
        "files": files,
        "branch": branch,
        "metadata": metadata,
    })


@router.post("/api/story-panel/stories/sync")
async def sync_stories(body: SyncRequest = SyncRequest()):
    """文档同步：指定 names 时从远端 API 下载文档覆盖本地；未指定时返回远端推荐列表"""
    if body.names:
        return await _do_sync_from_remote(body.names)

    token = os.environ.get("API_X_TOKEN", "")
    if not token:
        return success(data={"recommendations": [], "total": 0, "reason": "API_X_TOKEN 缺失"})

    sessions = await _query_remote_sessions()
    remote_dirs = _parse_story_dirs_from_remote(sessions)
    recommendations = [{"name": d["directory"], "files": d["file_count"]} for d in remote_dirs]
    return success(data={"recommendations": recommendations, "total": len(recommendations)})


async def _do_sync_from_remote(names: list[str]):
    """从远端 API 下载故事文档并覆盖本地文件"""
    token = os.environ.get("API_X_TOKEN", "")
    if not token:
        return success(data={"synced": False, "reason": "API_X_TOKEN 缺失"})

    for name in names:
        _validate_name(name)

    sessions = await _query_remote_sessions()
    if not sessions:
        return success(data={"synced": False, "reason": "远端无数据"})

    results = []
    total_written = 0
    total_failed = 0

    async with httpx.AsyncClient(timeout=30) as client:
        for name in names:
            story_files = [
                s for s in sessions
                if s.get("tags") and s["tags"][0] == "故事任务面板" and len(s["tags"]) > 1 and s["tags"][1] == name
            ]
            if not story_files:
                results.append({"name": name, "written": 0, "failed": 0, "reason": "远端无此故事"})
                continue

            written = 0
            failed = 0
            for sf in story_files:
                remote_path = sf.get("file_path", "")
                if not remote_path:
                    failed += 1
                    continue
                local_filename = os.path.basename(remote_path)
                try:
                    resp = await client.post(
                        f"{REMOTE_API_URL}/read-file",
                        json={"target_file": remote_path},
                        headers={"X-Token": token, "Content-Type": "application/json", "Accept": "application/json"},
                    )
                    data = resp.json()
                    if data.get("code") != 0:
                        failed += 1
                        continue
                    content = data.get("data", {}).get("content", "")
                except Exception:
                    failed += 1
                    continue

                local_dir = _parse_story_path(name)
                local_dir.mkdir(parents=True, exist_ok=True)
                local_path = local_dir / local_filename
                try:
                    local_path.write_text(content, encoding="utf-8")
                    written += 1
                except Exception:
                    failed += 1

            results.append({"name": name, "written": written, "failed": failed})
            total_written += written
            total_failed += failed

    return success(data={"synced": True, "results": results, "total_written": total_written, "total_failed": total_failed})


# --- Remote query ---

REMOTE_API_URL = os.environ.get("IMPORT_DOCS_API_URL", "https://api.effiy.cn")


async def _query_remote_sessions() -> list[dict]:
    token = os.environ.get("API_X_TOKEN", "")
    if not token:
        return []
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{REMOTE_API_URL}/",
                json={
                    "module_name": "services.database.data_service",
                    "method_name": "query_documents",
                    "parameters": {"cname": "sessions", "limit": 10000},
                },
                headers={"X-Token": token, "Content-Type": "application/json", "Accept": "application/json"},
            )
            data = resp.json()
        return data.get("data", {}).get("list", [])
    except Exception as e:
        logger.warning(f"remote query failed: {e}")
        return []


def _parse_story_dirs_from_remote(sessions: list[dict]) -> list[dict]:
    """从远端 sessions 中提取 tags[0]=='故事任务面板' 的故事目录列表"""
    stories = [s for s in sessions if s.get("tags") and s["tags"][0] == "故事任务面板"]

    dirs: dict[str, dict] = {}
    for s in stories:
        tags = s.get("tags", [])
        story_dir = tags[1] if len(tags) > 1 else "unknown"
        if story_dir not in dirs:
            dirs[story_dir] = []
        dirs[story_dir].append(s.get("file_path", ""))

    result = []
    for dirname, file_list in sorted(dirs.items()):
        result.append({
            "directory": dirname,
            "file_count": len(file_list),
            "files": sorted(file_list),
        })
    return result


@router.get("/api/story-panel/remote")
async def remote_stories(
    source: str = Query(default="all", description="数据源: local(本地), remote(远端API), all(全部)"),
):
    """远端故事查询：从文档 API 查询 tags[0]='故事任务面板' 的故事目录列表"""
    local_dirs = []
    remote_dirs = []

    if source in ("local", "all"):
        for sdir in _list_story_dirs():
            name = sdir.name
            files = sorted([f.name for f in sdir.iterdir() if f.suffix == ".md"])
            local_dirs.append({
                "directory": name,
                "file_count": len(files),
                "files": files,
            })

    if source in ("remote", "all"):
        token = os.environ.get("API_X_TOKEN", "")
        if not token:
            if source == "remote":
                return success(data={
                    "source": "remote", "api_url": REMOTE_API_URL,
                    "total_sessions": 0, "filtered_stories": 0,
                    "story_directories": [], "remote_available": False,
                    "reason": "API_X_TOKEN 缺失",
                })
            return success(data={
                "source": source, "local": local_dirs,
                "remote": [], "remote_available": False,
                "reason": "API_X_TOKEN 缺失",
            })

        sessions = await _query_remote_sessions()
        if sessions:
            remote_dirs = _parse_story_dirs_from_remote(sessions)

        if source == "remote":
            return success(data={
                "source": "remote",
                "api_url": REMOTE_API_URL,
                "total_sessions": len(sessions),
                "filtered_stories": sum(d["file_count"] for d in remote_dirs),
                "story_directories": remote_dirs,
            })

    return success(data={
        "source": source,
        "local": local_dirs,
        "remote": remote_dirs,
        "remote_api": REMOTE_API_URL if remote_dirs else None,
    })


# --- Help ---

@router.get("/api/story-panel/help")
async def help_info():
    """API 帮助信息"""
    return success(data={
        "description": "故事任务面板管理 API — 查询与同步",
        "namespace": "docs/故事任务面板/",
        "naming": "kebab-case（如 rui-story）",
        "endpoints": {
            "GET /api/story-panel/overview": "状态概览：按六状态聚合计数 + 最近活动故事列表",
            "GET /api/story-panel/stories": "进度全景：所有故事详情表格（状态/文件数/最后修改/类型/分支）",
            "GET /api/story-panel/stories/{name}": "单故事详情：文件清单/状态/元数据/关联分支（name 为 kebab-case）",
            "POST /api/story-panel/stories/sync": "文档同步：指定 names[] 时从远端下载覆盖本地文件；不指定时返回远端推荐列表",
            "GET /api/story-panel/remote": "远端故事查询：从文档 API 查询 tags[0]='故事任务面板' 的故事目录列表。?source=local|remote|all（默认 all）",
            "GET /api/story-panel/help": "本帮助信息",
        },
        "status_model": {
            "not_started": "01-故事任务.md 不存在",
            "docs_in_progress": "01 存在，文档基线不完整",
            "docs_done": "文档基线齐全，实施报告不存在",
            "code_in_progress": "06 或 07 存在，08 不存在",
            "code_done": "08 存在，未阻断",
            "blocked": ".memory/rui-state.json 含 blocked=true",
        },
        "boundaries": {
            "allowed": ["查询故事状态与进度", "从远端同步文档到本地（批量）"],
            "forbidden": ["创建故事文档内容（使用 /rui doc）", "修改源码（使用 /rui code）", "创建/切换 git 分支"],
        },
    })
