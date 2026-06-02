"""project_root 解析：6 级 fallback resolver。

设计原则:
    - workflow 是全局共享资产（YAML 放在 ~/.config/agent-workflow/workflows/），
      但每次 run 必须绑定到一个具体的"项目根"，否则 spawn 出来的 LLM CLI
      (claude / codex / opencode / cursor-agent) 会读到错误的 CLAUDE.md /
      AGENTS.md / .cursor/rules，导致产物不可复现。
    - 解析结果一次决定，写入 state.project_root + state.project_root_source，
      后续 advance / resume / retry 永远复用同一个，不再重新检测。

优先级（高 → 低）：
    1. caller 显式传 start params.project_root
    2. workflow YAML 顶层声明 workflow.project_root
    3. 环境变量 AGENT_WORKFLOW_PROJECT_ROOT
    4. IDE workspace 提示（CURSOR_WORKSPACE_LABEL / VSCODE_WORKSPACE_FOLDERS）
    5. 从当前 cwd 向上找 marker 文件（按权威性排序，git 最高）
    6. Path.cwd() 兜底（= 今天的行为，向后完全兼容）
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


# 按"权威性"排序的项目根 marker：找到第一个匹配就停。
# 排序原则：
#   1. .git 是事实标准，几乎所有工程项目都有 → 最权威
#   2. .agent-workflow 是本工具自留 marker（极少见但语义最强）
#   3. agent 规则文件（每家 LLM CLI 都会读，且通常放在项目根）
#   4. 各语言包管理文件（在 monorepo 子模块里可能误判，所以放最后）
MARKERS_BY_AUTHORITY: list[str] = [
    ".git",
    ".agent-workflow",
    "CLAUDE.md",
    "AGENTS.md",
    ".cursorrules",
    ".cursor",
    "pyproject.toml",
    "package.json",
    "Cargo.toml",
    "go.mod",
]


# project_root 解析来源标签，写入 state.project_root_source 供审计
SOURCE_CALLER_EXPLICIT = "caller_explicit"
SOURCE_WORKFLOW_YAML = "workflow_yaml"
SOURCE_ENV = "env"
SOURCE_IDE_LABEL = "ide_label"
SOURCE_MARKER_PREFIX = "marker:"
SOURCE_FALLBACK_CWD = "fallback_cwd"


@dataclass(frozen=True)
class ProjectRootDecision:
    """resolver 的解析结果。

    path   : 最终选定的 project_root 绝对路径
    source : 决策来源（见上方 SOURCE_* 常量；marker 命中时为 "marker:<filename>"）
    """

    path: Path
    source: str


def _find_upward(start: Path, marker: str) -> Path | None:
    """从 start 开始向上查找包含 marker 的最近父目录；找不到返回 None。"""
    try:
        cur = start.resolve()
    except (OSError, RuntimeError):
        return None
    for parent in [cur, *cur.parents]:
        if (parent / marker).exists():
            return parent
    return None


def _parse_vscode_workspace_folders(raw: str) -> list[str]:
    """解析 VSCODE_WORKSPACE_FOLDERS 的 JSON 数组；失败返回空。"""
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return []
    if isinstance(data, list):
        return [item for item in data if isinstance(item, str)]
    return []


def _resolve_from_ide_label(env: dict[str, str], cwd: Path) -> Path | None:
    """优先级:
    1. CURSOR_WORKSPACE_LABEL: 在 cwd 路径中反向找同名父目录
    2. VSCODE_WORKSPACE_FOLDERS: JSON 数组的第一个元素
    """
    cursor_label = env.get("CURSOR_WORKSPACE_LABEL")
    if cursor_label:
        pwd_raw = env.get("PWD") or str(cwd)
        try:
            pwd = Path(pwd_raw).resolve()
        except (OSError, RuntimeError):
            pwd = cwd
        for parent in [pwd, *pwd.parents]:
            if parent.name == cursor_label:
                return parent
    vscode_folders = env.get("VSCODE_WORKSPACE_FOLDERS")
    if vscode_folders:
        folders = _parse_vscode_workspace_folders(vscode_folders)
        if folders:
            try:
                return Path(folders[0]).expanduser().resolve()
            except (OSError, RuntimeError):
                return None
    return None


def resolve_project_root(
    *,
    caller_param: str | None = None,
    workflow: dict[str, Any] | None = None,
    env: dict[str, str] | None = None,
    cwd: Path | None = None,
) -> ProjectRootDecision:
    """按 6 级 fallback 解析 project_root。

    参数全部 optional，便于单元测试注入；默认从 os.environ 和 Path.cwd() 取。
    解析永远返回一个 Decision（最后兜底 Path.cwd()），不抛异常。
    """
    env_map = env if env is not None else dict(os.environ)
    cwd_path = cwd if cwd is not None else Path.cwd()

    # 1. caller 显式
    if caller_param:
        try:
            resolved = Path(caller_param).expanduser().resolve()
        except (OSError, RuntimeError):
            resolved = Path(caller_param).expanduser()
        return ProjectRootDecision(resolved, SOURCE_CALLER_EXPLICIT)

    # 2. workflow YAML 顶层 project_root
    if workflow:
        yaml_root = workflow.get("project_root")
        if isinstance(yaml_root, str) and yaml_root.strip():
            try:
                resolved = Path(yaml_root).expanduser().resolve()
            except (OSError, RuntimeError):
                resolved = Path(yaml_root).expanduser()
            return ProjectRootDecision(resolved, SOURCE_WORKFLOW_YAML)

    # 3. 环境变量
    env_root = env_map.get("AGENT_WORKFLOW_PROJECT_ROOT")
    if env_root and env_root.strip():
        try:
            resolved = Path(env_root).expanduser().resolve()
        except (OSError, RuntimeError):
            resolved = Path(env_root).expanduser()
        return ProjectRootDecision(resolved, SOURCE_ENV)

    # 4. IDE label
    ide_root = _resolve_from_ide_label(env_map, cwd_path)
    if ide_root is not None:
        return ProjectRootDecision(ide_root, SOURCE_IDE_LABEL)

    # 5. marker 向上搜索（按权威性顺序）
    for marker in MARKERS_BY_AUTHORITY:
        hit = _find_upward(cwd_path, marker)
        if hit is not None:
            return ProjectRootDecision(hit, f"{SOURCE_MARKER_PREFIX}{marker}")

    # 6. fallback to cwd（行为等价于今天）
    try:
        return ProjectRootDecision(cwd_path.resolve(), SOURCE_FALLBACK_CWD)
    except (OSError, RuntimeError):
        return ProjectRootDecision(cwd_path, SOURCE_FALLBACK_CWD)


__all__ = [
    "MARKERS_BY_AUTHORITY",
    "ProjectRootDecision",
    "resolve_project_root",
    "SOURCE_CALLER_EXPLICIT",
    "SOURCE_WORKFLOW_YAML",
    "SOURCE_ENV",
    "SOURCE_IDE_LABEL",
    "SOURCE_MARKER_PREFIX",
    "SOURCE_FALLBACK_CWD",
]
