"""沙箱中间件 — 文件系统和网络访问控制"""
import os
import logging
import builtins
from pathlib import Path
from contextlib import contextmanager
from typing import List, Optional

logger = logging.getLogger(__name__)


class SandboxViolation(Exception):
    """沙箱违规异常"""
    def __init__(self, path: str, reason: str):
        self.path = path
        self.reason = reason
        super().__init__(f"Sandbox blocked {path}: {reason}")


class SandboxMiddleware:
    """沙箱中间件：文件系统 allowlist 控制"""

    def __init__(
        self,
        fs_allowlist: Optional[List[str]] = None,
        network_allowlist: Optional[List[str]] = None,
    ):
        self.fs_allowlist = fs_allowlist or []
        self.network_allowlist = network_allowlist or []
        self._violations = 0

    def _resolve(self, path: str) -> Path:
        try:
            return Path(path).resolve()
        except (OSError, ValueError) as e:
            raise SandboxViolation(path, f"cannot resolve: {e}") from e

    def _check_path(self, path: str) -> None:
        resolved = self._resolve(path)
        for allowed in self.fs_allowlist:
            try:
                if resolved.is_relative_to(Path(allowed).resolve()):
                    return
            except (OSError, ValueError):
                continue
        self._violations += 1
        raise SandboxViolation(str(resolved), "path not in allowlist")

    def check_network(self, host: str) -> None:
        if not self.network_allowlist:
            return
        for allowed in self.network_allowlist:
            if host == allowed or host.endswith(f".{allowed}"):
                return
        self._violations += 1
        raise SandboxViolation(host, "host not in network allowlist")

    @property
    def violations_total(self) -> int:
        return self._violations


@contextmanager
def sandbox_context(
    fs_allowlist: Optional[List[str]] = None,
    network_allowlist: Optional[List[str]] = None,
):
    """沙箱上下文管理器：在执行期间替换 open()"""
    middleware = SandboxMiddleware(
        fs_allowlist=fs_allowlist,
        network_allowlist=network_allowlist,
    )
    original_open = builtins.open

    def _patched_open(file, *args, **kwargs):
        if isinstance(file, (str, os.PathLike)):
            middleware._check_path(str(file))
        return original_open(file, *args, **kwargs)

    builtins.open = _patched_open
    try:
        yield middleware
    finally:
        builtins.open = original_open
