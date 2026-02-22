"""
Memory Skill 初始化辅助函数：hooks 合并、rules/skill 安装、目录创建、依赖安装等。
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "../.."))
import json
import shutil
import subprocess

from service.config import _DEFAULTS, DAILY_DIR_NAME

_EMB_MODEL = _DEFAULTS["embedding"]["model"]
_MODEL_CACHE = os.path.expanduser(_DEFAULTS["embedding"]["cache_dir"])

SKILL_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..")
TEMPLATES_DIR = os.path.join(SKILL_ROOT, "templates")


def _replace_placeholders(text, replacements):
    """将文本中的占位符替换为实际值。"""
    for key, val in replacements.items():
        text = text.replace(key, val)
    return text


def merge_hooks(target_path, template_path, skill_root_rel):
    """
    将模板 hooks 与已有 hooks.json 合并，替换 {{SKILL_PATH}}。

    策略：按 skill 前缀匹配，替换本 skill 的所有 hook 条目（支持属性更新和废弃清理），
    保留其他 skill 或用户自定义的 hook 条目不变。
    """
    with open(template_path, "r", encoding="utf-8") as f:
        template = json.loads(f.read())

    for hook_type in template.get("hooks", {}):
        for cmd in template["hooks"][hook_type]:
            cmd["command"] = cmd["command"].replace(
                "{{SKILL_PATH}}", skill_root_rel
            )

    skill_prefix = f"python3 {skill_root_rel}/"

    if os.path.exists(target_path):
        with open(target_path, "r", encoding="utf-8") as f:
            existing = json.loads(f.read())
        existing.setdefault("hooks", {})

        all_hook_types = set(existing["hooks"].keys()) | set(template.get("hooks", {}).keys())

        for hook_type in all_hook_types:
            existing_cmds = existing["hooks"].get(hook_type, [])
            new_cmds = template.get("hooks", {}).get(hook_type, [])
            non_skill_cmds = [c for c in existing_cmds
                              if not c.get("command", "").startswith(skill_prefix)]
            existing["hooks"][hook_type] = non_skill_cmds + new_cmds

            if not existing["hooks"][hook_type]:
                del existing["hooks"][hook_type]

        result = existing
    else:
        result = template

    os.makedirs(os.path.dirname(target_path) or ".", exist_ok=True)
    with open(target_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
        f.write("\n")
    return target_path


def install_rules(target_dir, template_path, replacements):
    """将 memory-rules.mdc 模板写入 target_dir，替换占位符。"""
    os.makedirs(target_dir, exist_ok=True)
    target_path = os.path.join(target_dir, "memory-rules.mdc")
    with open(template_path, "r", encoding="utf-8") as f:
        content = f.read()
    content = _replace_placeholders(content, replacements)
    with open(target_path, "w", encoding="utf-8") as f:
        f.write(content)
    return target_path


def install_skill_md(skill_install_dir, source_path, replacements):
    """将 SKILL.md 安装到目标目录，替换占位符。"""
    target_path = os.path.join(skill_install_dir, "SKILL.md")
    with open(source_path, "r", encoding="utf-8") as f:
        content = f.read()
    content = _replace_placeholders(content, replacements)
    with open(target_path, "w", encoding="utf-8") as f:
        f.write(content)
    return target_path


def init_memory_dir(project_path):
    """创建 memory-data 目录结构，若 MEMORY.md / README.md 不存在则从模板复制或创建默认内容。"""
    memory_dir = os.path.join(project_path, _DEFAULTS["paths"]["data_dir"])
    daily_dir = os.path.join(memory_dir, DAILY_DIR_NAME)
    os.makedirs(daily_dir, exist_ok=True)

    memory_md = os.path.join(memory_dir, "MEMORY.md")
    if not os.path.exists(memory_md):
        template = os.path.join(TEMPLATES_DIR, "MEMORY.md")
        if os.path.exists(template):
            shutil.copy2(template, memory_md)
        else:
            with open(memory_md, "w", encoding="utf-8") as f:
                f.write("# 核心记忆\n\n## 用户偏好\n\n## 项目背景\n\n## 重要决策\n")

    readme_md = os.path.join(memory_dir, "README.md")
    if not os.path.exists(readme_md):
        readme_template = os.path.join(TEMPLATES_DIR, "memory-data-README.md")
        if os.path.exists(readme_template):
            shutil.copy2(readme_template, readme_md)

    return memory_dir


def install_skill_code(source_dir, target_dir, replacements):
    """将 skill 代码复制到安装目录，排除 __pycache__/templates 等，并处理 SKILL.md 占位符。

    templates/ 目录不复制到安装目录，因为其中的占位符由 merge_hooks / install_rules
    在安装时单独处理。原样复制会导致安装目录残留未替换的占位符。
    """
    if os.path.abspath(source_dir) == os.path.abspath(target_dir):
        install_skill_md(target_dir, os.path.join(source_dir, "SKILL.md"), replacements)
        return target_dir

    _SKIP = {"__pycache__", "logs", ".DS_Store", "templates"}

    os.makedirs(target_dir, exist_ok=True)
    for item in os.listdir(source_dir):
        if item in _SKIP:
            continue
        src = os.path.join(source_dir, item)
        dst = os.path.join(target_dir, item)
        if os.path.isdir(src):
            if os.path.exists(dst):
                shutil.rmtree(dst)
            shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        else:
            shutil.copy2(src, dst)

    install_skill_md(target_dir, os.path.join(source_dir, "SKILL.md"), replacements)
    return target_dir


def install_dependencies():
    """通过 pip 安装 sentence-transformers。"""
    print("  Installing dependencies (sentence-transformers)...")
    proc = subprocess.run(
        [sys.executable, "-m", "pip", "install", "sentence-transformers", "--progress-bar", "on"],
        capture_output=False,
    )
    if proc.returncode == 0:
        print("  ✓ sentence-transformers installed")
    else:
        raise RuntimeError("pip install failed")


def download_model(model_name):
    """下载嵌入模型到全局缓存目录，首次加载会预下载。"""
    os.makedirs(_MODEL_CACHE, exist_ok=True)
    print(f"\n  Downloading embedding model: {model_name}")
    print(f"  Cache dir: {_MODEL_CACHE}")
    print(f"  (Progress will be shown below)\n")
    os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "0"
    from sentence_transformers import SentenceTransformer
    SentenceTransformer(model_name, cache_folder=_MODEL_CACHE)
    print(f"\n  ✓ {model_name} downloaded successfully")
