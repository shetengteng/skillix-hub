# Swagger API Reader Skill 设计文档

## 1. 概述

Swagger API Reader 是一个用于读取、解析和缓存 Swagger/OpenAPI 文档的 Cursor Skill。它能够从各种来源获取 API 文档，支持多种认证方式，并生成结构化的 Markdown 文档供 AI 模型使用。

### 1.1 核心功能

- **文档获取**：支持直接 URL、HTML 页面自动提取、浏览器模式（SSO/OAuth）
- **多种认证**：Bearer Token、Basic Auth、API Key
- **本地缓存**：避免重复请求，支持离线使用
- **文档生成**：自动生成结构化 Markdown API 文档
- **别名管理**：通过别名快速访问已缓存的 API

### 1.2 设计原则

- **灵活获取**：支持多种 API 文档来源和认证方式
- **智能解析**：自动识别 Swagger UI 页面并提取 API 文档 URL
- **结构化输出**：生成便于 AI 理解的 Markdown 文档
- **本地优先**：缓存到本地，减少网络依赖

## 2. 目录结构

```
~/.cursor/skills/swagger-api-reader/
├── SKILL.md                    # Skill 指令文件
├── scripts/
│   ├── swagger_reader.py       # 主脚本
│   ├── doc_generator.py        # 文档生成器
│   └── requirements.txt        # Python 依赖
└── cache/                      # 缓存目录（自动创建）
    ├── index.json              # API 索引
    └── {api_hash}/             # 每个 API 的缓存
        ├── raw.json            # 原始 Swagger 数据
        ├── api-doc.md          # 生成的 Markdown 文档
        └── meta.json           # 元数据
```

## 3. 核心模块

### 3.1 swagger_reader.py

主脚本，提供命令行接口和核心功能。

#### 命令

| 命令 | 说明 | 示例 |
|------|------|------|
| `add` | 添加新 API | `python swagger_reader.py add --url "URL" --alias "别名"` |
| `list` | 列出已缓存 API | `python swagger_reader.py list` |
| `read` | 读取 API 文档 | `python swagger_reader.py read --alias "别名"` |
| `refresh` | 刷新 API 缓存 | `python swagger_reader.py refresh --alias "别名"` |
| `remove` | 删除 API 缓存 | `python swagger_reader.py remove --alias "别名"` |

#### 认证参数

| 参数 | 说明 |
|------|------|
| `--auth-type bearer` | Bearer Token 认证 |
| `--token "TOKEN"` | Token 值 |
| `--auth-type basic` | Basic Auth 认证 |
| `--username "USER"` | 用户名 |
| `--password "PASS"` | 密码 |
| `--auth-type apikey` | API Key 认证 |
| `--key-name "X-API-Key"` | Key 名称 |
| `--key-value "KEY"` | Key 值 |
| `--key-in header/query` | Key 位置 |

#### 特殊参数

| 参数 | 说明 |
|------|------|
| `--browser` | 使用浏览器模式（SSO/OAuth） |
| `--browser-timeout 180` | 浏览器超时时间（秒） |
| `--no-verify` | 跳过 SSL 证书验证 |

### 3.2 doc_generator.py

文档生成器，将 Swagger/OpenAPI 数据转换为 Markdown 文档。

#### 主要函数

| 函数 | 说明 |
|------|------|
| `generate_api_doc()` | 生成完整 API 文档 |
| `get_base_url()` | 提取 Base URL |
| `get_security_info()` | 提取认证信息 |
| `format_parameters()` | 格式化参数表格 |
| `format_request_body()` | 格式化请求体 |
| `format_responses()` | 格式化响应表格 |
| `format_model()` | 格式化数据模型 |

## 4. 数据格式

### 4.1 index.json

```json
{
  "apis": [
    {
      "id": "abc123def456",
      "alias": "my-api",
      "url": "https://api.example.com/v3/api-docs",
      "title": "My API",
      "version": "1.0.0",
      "last_updated": "2026-01-29T10:30:00"
    }
  ]
}
```

### 4.2 meta.json

```json
{
  "url": "https://api.example.com/v3/api-docs",
  "alias": "my-api",
  "title": "My API",
  "version": "1.0.0",
  "description": "API 描述...",
  "endpoint_count": 25,
  "created_at": "2026-01-29T10:30:00",
  "updated_at": "2026-01-29T10:30:00",
  "auth_type": "bearer"
}
```

### 4.3 生成的 Markdown 文档结构

```markdown
# API 标题

> **版本**: 1.0.0
> **Base URL**: `https://api.example.com`
> **来源**: https://api.example.com/v3/api-docs
> **生成时间**: 2026-01-29 10:30:00

## 概述
API 描述...

## 认证
- **bearerAuth**: HTTP Bearer

---

## 接口

### 用户管理

#### `GET` /users
**摘要**: 获取用户列表

**参数**:
| 名称 | 位置 | 类型 | 必填 | 描述 |
|------|------|------|------|------|
| `page` | query | integer | 否 | 页码 |

**响应**:
| 状态码 | 描述 | Schema |
|--------|------|--------|
| 200 | 成功 | [UserList](#model-userlist) |

---

## 数据模型

### UserList
| 属性 | 类型 | 必填 | 描述 |
|------|------|------|------|
| `items` | array[User] | 是 | 用户列表 |
| `total` | integer | 是 | 总数 |
```

## 5. 工作流程

### 5.1 添加 API 流程

```
用户执行 add 命令
    ↓
检查别名/URL 是否已存在
    ↓
获取 Swagger 文档
    ├── 直接 URL → 请求 JSON/YAML
    ├── HTML 页面 → 提取 API 文档 URL → 请求
    └── 浏览器模式 → 打开浏览器 → 等待登录 → 获取内容
    ↓
解析 Swagger/OpenAPI 数据
    ↓
生成 Markdown 文档
    ↓
保存到缓存目录
    ↓
更新索引
```

### 5.2 读取 API 流程

```
用户执行 read 命令
    ↓
通过别名/URL 查找 API
    ↓
读取缓存的 Markdown 文档
    ↓
输出到标准输出
```

### 5.3 浏览器模式流程

```
打开 Chrome 浏览器
    ↓
导航到 Swagger UI 页面
    ↓
等待用户完成登录（SSO/OAuth）
    ↓
检测 Swagger UI 加载完成
    ↓
提取 API 文档 URL
    ↓
获取 API 文档内容
    ↓
关闭浏览器
```

## 6. 支持的格式

### 6.1 输入格式

- **OpenAPI 3.x**：JSON/YAML
- **Swagger 2.x**：JSON/YAML
- **Swagger UI HTML**：自动提取 API 文档 URL

### 6.2 输出格式

- **Markdown**：结构化文档，包含接口、参数、响应、数据模型

## 7. 使用示例

### 7.1 添加公开 API

```bash
python swagger_reader.py add \
  --url "https://petstore.swagger.io/v2/swagger.json" \
  --alias "petstore"
```

### 7.2 添加需要认证的 API

```bash
# Bearer Token
python swagger_reader.py add \
  --url "https://api.example.com/v3/api-docs" \
  --alias "my-api" \
  --auth-type bearer \
  --token "your-token"

# Basic Auth
python swagger_reader.py add \
  --url "https://api.example.com/v3/api-docs" \
  --alias "my-api" \
  --auth-type basic \
  --username "user" \
  --password "pass"
```

### 7.3 添加 SSO 认证的 API

```bash
python swagger_reader.py add \
  --url "https://internal.example.com/swagger-ui/index.html" \
  --alias "internal-api" \
  --browser \
  --browser-timeout 180
```

### 7.4 读取 API 文档

```bash
# 输出到终端
python swagger_reader.py read --alias "petstore"

# 保存到文件
python swagger_reader.py read --alias "petstore" > petstore-api.md
```

### 7.5 刷新 API 缓存

```bash
python swagger_reader.py refresh --alias "petstore"
```

## 8. 依赖

```
requests>=2.28.0
pyyaml>=6.0
selenium>=4.0.0  # 仅浏览器模式需要
```

安装：
```bash
pip install -r scripts/requirements.txt
```

浏览器模式还需要安装 Chrome 浏览器和 ChromeDriver。

## 9. 错误处理

| 错误类型 | 处理方式 |
|----------|----------|
| 网络错误 | 显示错误信息，建议检查网络 |
| 认证失败 | 提示提供有效认证信息 |
| 解析失败 | 提示检查 URL 是否正确 |
| 别名冲突 | 提示使用 refresh 更新 |
| 超时 | 浏览器模式超时后关闭浏览器 |

## 10. 最佳实践

1. **使用有意义的别名**：便于记忆和使用
2. **定期刷新**：保持文档与实际 API 同步
3. **浏览器模式**：仅在需要 SSO/OAuth 时使用
4. **SSL 验证**：生产环境不建议跳过 SSL 验证
5. **缓存管理**：定期清理不再使用的 API 缓存

## 11. 后续改进

1. 支持更多认证方式（OAuth2 授权码流程）
2. 支持 API 文档版本对比
3. 支持批量添加/刷新
4. 支持导出为其他格式（HTML、PDF）
5. 支持 API 变更通知
