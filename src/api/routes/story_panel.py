import logging
import os
import re
import json
import asyncio
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from core.response import success, fail
from core.error_codes import ErrorCode

logger = logging.getLogger(__name__)
router = APIRouter()

PANEL_ROOT = Path("docs/故事任务面板")
NAME_RE = re.compile(r"^[A-Z][A-Za-z0-9]*$")  # PascalCase
NAME_KEBAB_RE = re.compile(r"^[a-z][a-z0-9]*(-[a-z][a-z0-9]*)*$")  # kebab-case


def _validate_name_segment(value: str, label: str) -> None:
    if value != os.path.basename(value) or value.startswith(".") or ".." in value:
        raise HTTPException(status_code=422, detail=f"{label} 含非法路径字符: {value}")


def _validate_project(project: str) -> None:
    _validate_name_segment(project, "project")
    if not NAME_RE.match(project):
        raise HTTPException(status_code=400, detail=f"project 必须为 PascalCase: {project}")


def _validate_name(name: str) -> None:
    _validate_name_segment(name, "name")
    if not NAME_KEBAB_RE.match(name):
        raise HTTPException(status_code=400, detail=f"name 必须为 kebab-case: {name}")


def _list_project_dirs() -> list[Path]:
    if not PANEL_ROOT.exists():
        return []
    return sorted(p for p in PANEL_ROOT.iterdir() if p.is_dir())


def _list_story_dirs() -> list[Path]:
    result = []
    for proj in _list_project_dirs():
        result.extend(sorted(p for p in proj.iterdir() if p.is_dir()))
    return result


def _determine_status(story_dir: Path) -> str:
    has_01 = (story_dir / "01-故事任务.md").exists()
    if not has_01:
        return "not_started"

    has_02 = (story_dir / "02-用户使用场景.md").exists()
    has_05 = (story_dir / "05-测试用例评审.md").exists()
    has_03 = (story_dir / "03-后端技术评审.md").exists()
    has_04 = (story_dir / "04-前端技术评审.md").exists()
    docs_baseline = has_02 and has_05

    type_file = story_dir / ".memory" / "story-type.json"
    story_type = _read_story_type(type_file)
    if story_type in ("backend", "fullstack"):
        docs_baseline = docs_baseline and has_03
    if story_type in ("frontend", "fullstack"):
        docs_baseline = docs_baseline and has_04

    if not docs_baseline:
        return "docs_in_progress"

    has_06 = (story_dir / "06-后端实施报告.md").exists()
    has_07 = (story_dir / "07-前端实施报告.md").exists()
    has_impl_report = has_06 or has_07

    if not has_impl_report:
        return "docs_done"

    has_08 = (story_dir / "08-测试用例报告.md").exists()
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
    has_03 = (story_dir / "03-后端技术评审.md").exists()
    has_04 = (story_dir / "04-前端技术评审.md").exists()
    has_06 = (story_dir / "06-后端实施报告.md").exists()
    has_07 = (story_dir / "07-前端实施报告.md").exists()
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


def _get_branch(project: str, name: str) -> Optional[str]:
    branch_name = f"feat/{project}-{name}"
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


def _parse_story_path(project: str, name: str) -> Path:
    return PANEL_ROOT / project / name


# --- Request models ---

class CreateStoryRequest(BaseModel):
    type: str = Field(default="meta", description="故事类型: frontend | backend | fullstack | meta")


class SyncRequest(BaseModel):
    name: str = Field(default="", description="故事全名 <Project>-<name>，空为全量同步")


class RenameRequest(BaseModel):
    new_project: str = Field(..., description="新 Project 名（PascalCase）")
    new_name: str = Field(..., description="新 name（kebab-case）")


# --- Routes ---

@router.get("/api/story-panel/overview")
async def overview():
    """状态概览：按状态聚合 + 最近 5 个活动故事"""
    stories = []
    for sdir in _list_story_dirs():
        name = sdir.name
        project = sdir.parent.name
        status = _determine_status(sdir)
        modified = _last_modified(sdir)
        stories.append({
            "project": project,
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
        project = sdir.parent.name
        status = _determine_status(sdir)
        files = _count_md_files(sdir)
        last_modified = _last_modified(sdir)
        story_type = _infer_type(sdir)
        branch = _get_branch(project, name)
        items.append({
            "project": project,
            "name": name,
            "status": status,
            "files": files,
            "last_modified": last_modified,
            "type": story_type,
            "branch": branch,
        })

    items.sort(key=lambda s: s["last_modified"] or "", reverse=True)
    return success(data={"stories": items})


@router.get("/api/story-panel/stories/{project}/{name}")
async def show_story(project: str, name: str):
    """单故事详情"""
    _validate_project(project)
    _validate_name(name)

    sdir = _parse_story_path(project, name)
    if not sdir.is_dir():
        return fail(error=ErrorCode.DATA_NOT_FOUND, message=f"故事不存在: {project}/{name}")

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
    branch = _get_branch(project, name)

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
        "directory": str(sdir) + "/",
        "type": story_type,
        "files": files,
        "branch": branch,
        "metadata": metadata,
    })


@router.post("/api/story-panel/stories/{project}/{name}", status_code=201)
async def create_story(project: str, name: str, body: CreateStoryRequest = CreateStoryRequest()):
    """创建故事目录骨架"""
    _validate_project(project)
    _validate_name(name)

    allowed_types = {"frontend", "backend", "fullstack", "meta"}
    if body.type not in allowed_types:
        raise HTTPException(status_code=400, detail=f"type 必须为: {', '.join(sorted(allowed_types))}")

    sdir = _parse_story_path(project, name)
    if sdir.exists():
        raise HTTPException(status_code=409, detail=f"故事目录已存在: {project}/{name}")

    mem_dir = sdir / ".memory"
    mem_dir.mkdir(parents=True, exist_ok=True)
    story_type = {
        "type": body.type,
        "createdAt": datetime.now(timezone.utc).isoformat(),
    }
    (mem_dir / "story-type.json").write_text(json.dumps(story_type, ensure_ascii=False))

    return success(data={"created": True, "directory": str(sdir) + "/"})


@router.delete("/api/story-panel/stories/{project}/{name}")
async def delete_story(project: str, name: str):
    """删除故事目录"""
    _validate_project(project)
    _validate_name(name)

    sdir = _parse_story_path(project, name)
    if not sdir.is_dir():
        raise HTTPException(status_code=404, detail=f"故事目录不存在: {project}/{name}")

    warning = None
    branch = _get_branch(project, name)
    if branch:
        warning = f"git 分支 {branch} 需手动清理"

    shutil.rmtree(sdir)

    proj_dir = PANEL_ROOT / project
    if proj_dir.exists() and not any(proj_dir.iterdir()):
        proj_dir.rmdir()

    return success(data={"deleted": True, "directory": str(sdir) + "/", "warning": warning})


@router.post("/api/story-panel/stories/sync")
async def sync_stories(body: SyncRequest = SyncRequest()):
    """文档同步：委托 import-docs"""
    if not os.environ.get("API_X_TOKEN"):
        return success(data={"synced": False, "reason": "API_X_TOKEN 缺失，降级跳过"})

    dir_arg = PANEL_ROOT.as_posix()
    if body.name:
        parts = body.name.split("-", 1)
        if len(parts) == 2:
            dir_arg = str(PANEL_ROOT / parts[0] / parts[1])

    script = "skills/import-docs/sync.mjs"
    try:
        proc = await asyncio.create_subprocess_exec(
            "node", script, f"dir={dir_arg}",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=60)
        output = stdout.decode() + stderr.decode()

        created = 0
        overwritten = 0
        failed = 0
        m = re.search(r"created:\s*(\d+),\s*overwritten:\s*(\d+),\s*failed:\s*(\d+)", output)
        if m:
            created = int(m.group(1))
            overwritten = int(m.group(2))
            failed = int(m.group(3))

        return success(data={"synced": True, "created": created, "overwritten": overwritten, "failed": failed})
    except Exception as e:
        logger.warning(f"sync failed: {e}")
        return success(data={"synced": False, "reason": str(e)})


@router.put("/api/story-panel/stories/{project}/{name}/rename")
async def rename_story(project: str, name: str, body: RenameRequest):
    """重命名故事目录"""
    _validate_project(project)
    _validate_name(name)
    _validate_project(body.new_project)
    _validate_name(body.new_name)

    if project == body.new_project and name == body.new_name:
        raise HTTPException(status_code=400, detail="新旧名称相同")

    old_dir = _parse_story_path(project, name)
    if not old_dir.is_dir():
        raise HTTPException(status_code=404, detail=f"故事目录不存在: {project}/{name}")

    new_dir = _parse_story_path(body.new_project, body.new_name)
    if new_dir.exists():
        raise HTTPException(status_code=409, detail=f"目标已存在: {body.new_project}/{body.new_name}")

    warning = None
    branch = _get_branch(project, name)
    if branch:
        warning = f"git 分支 {branch} 需手动重命名"

    new_dir.parent.mkdir(parents=True, exist_ok=True)
    old_dir.rename(new_dir)

    old_proj = PANEL_ROOT / project
    if old_proj.exists() and not any(old_proj.iterdir()):
        old_proj.rmdir()

    return success(data={
        "renamed": True,
        "old": str(old_dir) + "/",
        "new": str(new_dir) + "/",
        "warning": warning,
    })
