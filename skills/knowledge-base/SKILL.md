---
name: knowledge-base
version: 0.1.0
description: 本地知识资料索引与 Wiki 编译
triggers:
  - 知识库
  - 之前的设计文档
  - 找之前的资料
  - 相关设计
  - knowledge base
  - kb
---

# Knowledge Base Skill

管理本地的设计资料、文档、数据集、代码仓库的位置索引，并通过 LLM 编译成结构化 Wiki（含反向链接、概念归类、知识图谱）。支持任意文件类型。

## 快速开始

```bash
SKILL_PATH="skills/knowledge-base"

# 添加单个资料
python3 $SKILL_PATH/main.py add /path/to/doc.md --tags "tag1,tag2" --category "分类"

# 导入项目 design/ 目录
python3 $SKILL_PATH/main.py import-project

# 查看索引
python3 $SKILL_PATH/main.py list

# 浏览知识库
python3 $SKILL_PATH/main.py browse

# 搜索
python3 $SKILL_PATH/main.py search "记忆架构"
```

## 命令列表

### 索引管理

| 命令 | 说明 |
|------|------|
| `add <path>` | 添加资料索引（支持 --title, --tags, --type, --category） |
| `add <dir> --type directory --pattern "*.md" --recursive` | 批量添加目录下的文件 |
| `list [--type X] [--tag X] [--category X] [--pending]` | 列出索引，支持过滤 |
| `remove <id>` | 移除索引条目 |
| `edit <id> [--title X] [--tags X] [--category X]` | 更新索引元数据 |
| `import-project [--dir design] [--pattern "*.md"]` | 快捷导入项目目录 |

### 编译

| 命令 | 说明 |
|------|------|
| `compile` | 增量编译 Wiki（生成 prompt 供 Agent 执行） |
| `compile --full` | 全量重新编译 |
| `compile --dry-run` | 预览待编译清单 |
| `compile --finalize` | 编译后处理（更新反向链接和知识图谱） |

### 浏览与搜索

| 命令 | 说明 |
|------|------|
| `browse` | 知识地图概览 |
| `browse <category>` | 查看分类下的概念 |
| `read <concept-id>` | 读取概念条目全文 |
| `source <source-id>` | 查看原始资料信息 |
| `search <query>` | 搜索知识库（索引 + 概念） |
| `status` | 知识库状态总览（条目统计、编译状态） |
| `check` | 路径有效性检查 |

### 知识图谱

| 命令 | 说明 |
|------|------|
| `graph` | 输出知识图谱（JSON） |
| `graph --format mermaid` | 输出 Mermaid 格式图谱 |
| `graph --center <id> --depth 2` | 以某概念为中心的子图 |

### 概念管理

| 命令 | 说明 |
|------|------|
| `concept list` | 列出所有概念 |
| `concept remove <concept-id>` | 删除概念 |
| `concept merge <id1> <id2>` | 合并两个概念 |
| `concept rename <concept-id> "新标题"` | 重命名概念 |

### 分类管理

| 命令 | 说明 |
|------|------|
| `category list` | 列出所有分类 |
| `category rename <old-name> <new-name>` | 重命名分类 |

### Skill 管理

| 命令 | 说明 |
|------|------|
| `install [--target <path>]` | 安装初始化（创建数据目录） |
| `update [--target <path>]` | 更新代码 |
| `uninstall` | 卸载 |

## 支持的资料类型

| 类型 | 扩展名 | 索引行为 |
|------|--------|---------|
| markdown | .md, .mdx, .rst | 读取全文，自动提取标题 |
| code | .py, .js, .ts, .java, .go, .rs, .vue 等 | 读取全文，返回文件名 |
| config | .yaml, .toml, .json, .xml, .env 等 | 读取全文，返回文件名 |
| text | .txt, .log, .tex | 读取全文 |
| dataset | .csv, .json, .jsonl, .tsv | 读取前 20 行预览 |
| image | .png, .jpg, .gif, .svg, .webp | 索引路径 + 文件大小 |
| binary | .pdf, .zip, .exe, .whl 等 | 索引路径 + 文件大小 |
| repo | 含 .git 的目录 | 读取 README + 目录结构 |
| directory | 普通目录 | 目录树（深度 2） |
| link | 外部 URL | 存储 URL + 手动摘要 |

未知扩展名自动通过二进制检测区分文本/二进制，**不限制文件类型**。

## 数据目录

运行时数据存储在 `skills/knowledge-base-data/`：

```
knowledge-base-data/
├── raw/
│   ├── index.jsonl       ← 索引清单
│   └── cache/            ← 内容缓存
├── wiki/
│   ├── index.md          ← 知识地图
│   ├── concepts/         ← 概念条目（Markdown + frontmatter）
│   ├── categories/       ← 分类索引
│   ├── backlinks.json    ← 反向链接
│   └── graph.json        ← 知识图谱
└── compile/
    ├── pending.json      ← 待编译清单
    └── history.jsonl     ← 编译历史
```

## 编译流程

1. `kb compile --dry-run` — 预览待编译清单
2. `kb compile` — 生成 prompt，Agent 分析内容、提取概念、写入 wiki/concepts/
3. `kb compile --finalize` — 构建反向链接、知识图谱、知识地图、分类索引
