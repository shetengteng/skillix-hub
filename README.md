# Skillix Hub

Cursor Skills 技能仓库 - 提升 AI 编程效率的工具集合。

## 什么是 Cursor Skill？

Cursor Skill 是一种可复用的 AI 指令集，帮助 Cursor AI 更好地完成特定任务。每个 Skill 包含：
- 任务说明和触发条件
- 执行脚本和工具
- 使用示例

## 可用 Skills

| Skill | 描述 |
|-------|------|
| [swagger-api-reader](./swagger-api-reader/) | 读取并缓存 Swagger/OpenAPI 文档，支持浏览器认证 |

## 安装使用

### 方式一：个人级安装（所有项目可用）

```bash
# 克隆仓库
git clone https://github.com/shetengteng/skillix-hub.git

# 复制到 Cursor skills 目录
cp -r skillix-hub/swagger-api-reader ~/.cursor/skills/

# 安装依赖
pip install -r ~/.cursor/skills/swagger-api-reader/scripts/requirements.txt
```

### 方式二：项目级安装（仅当前项目可用）

```bash
# 在项目根目录
mkdir -p .cursor/skills
cp -r skillix-hub/swagger-api-reader .cursor/skills/

# 安装依赖
pip install -r .cursor/skills/swagger-api-reader/scripts/requirements.txt
```

## 贡献

欢迎提交 PR 添加新的 Skill！

### Skill 结构规范

```
skill-name/
├── SKILL.md              # 必需：主指令文件
├── scripts/              # 可选：执行脚本
│   ├── main.py
│   └── requirements.txt
└── templates/            # 可选：模板文件
```

### SKILL.md 格式

```markdown
---
name: skill-name
description: 简短描述，说明功能和触发条件
---

# Skill 标题

## 使用方法
...
```

## 许可证

MIT License
