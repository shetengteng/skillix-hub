# Skill Store 测试设计

## 测试范围

| 模块 | 文件 | 说明 |
|------|------|------|
| config | lib/config.py | 路径管理、JSON 读写、默认值 |
| git_ops | lib/git_ops.py | Git 命令封装 |
| file_lock | lib/file_lock.py | 文件锁、带锁 JSON 读写 |
| version | lib/version.py | 版本比对、孤立检测 |
| dependency | lib/dependency.py | 依赖解析、循环检测 |
| index | scripts/index.py | SKILL.md 解析、索引构建、搜索 |
| registry | scripts/registry.py | 仓库配置增删改查 |
| install | scripts/install.py | 安装/卸载/更新 |
| hook | scripts/hook.py | 每日同步判断、状态展示 |
| main | main.py | 自身安装/更新/卸载 |

## 测试用例

### 模块：config

| 用例 | 输入 | 预期输出 | 类型 |
|------|------|----------|------|
| load_json 文件不存在 | 不存在的路径 | 返回 default | unit |
| load_json 文件损坏 | 非法 JSON 内容 | 返回 default | unit |
| load_json 正常文件 | 有效 JSON 文件 | 返回解析结果 | unit |
| save_json 创建目录 | 不存在的父目录 | 自动创建并写入 | unit |
| save_json 覆盖写入 | 已存在的文件 | 覆盖为新内容 | unit |
| ensure_data_dir | 空目录 | 创建 data 和 repos 目录 | unit |
| output_result 正常 | result={"a":1} | JSON stdout | unit |
| output_result 错误 | error="msg" | JSON stdout with error | unit |
| DATA_DIR 环境变量覆盖 | SKILL_STORE_DATA_DIR 设置 | 使用自定义路径 | unit |

### 模块：git_ops

| 用例 | 输入 | 预期输出 | 类型 |
|------|------|----------|------|
| run_git 正常命令 | ["--version"] | returncode=0 | unit |
| run_git git 不存在 | 模拟 FileNotFoundError | returncode=-1 | unit |
| clone 到新目录 | 有效 URL + 目标路径 | 成功 clone | integration |
| is_git_repo 正常 | .git 目录存在 | True | unit |
| is_git_repo 非 git | 普通目录 | False | unit |

### 模块：file_lock

| 用例 | 输入 | 预期输出 | 类型 |
|------|------|----------|------|
| locked_read_json 文件不存在 | 不存在的路径 | 返回 default | unit |
| locked_read_json 正常 | 有效 JSON | 返回内容 | unit |
| locked_write_json | 数据 + 路径 | 写入成功 | unit |
| locked_update_json | updater 函数 | 读取-修改-写入 | unit |
| file_lock 锁文件清理 | 使用后 | .lock 文件被删除 | unit |

### 模块：version

| 用例 | 输入 | 预期输出 | 类型 |
|------|------|----------|------|
| check_orphaned 无孤立 | 所有 target_path 存在 | 空列表 | unit |
| check_orphaned 有孤立 | target_path 不存在 | 返回孤立列表 | unit |
| clean_orphaned | 有孤立记录 | 移除孤立记录，返回数量 | unit |

### 模块：dependency

| 用例 | 输入 | 预期输出 | 类型 |
|------|------|----------|------|
| 无依赖 | skill 无 dependencies | 空 install_order | unit |
| 单层依赖 | A 依赖 B | [B, A] | unit |
| 多层依赖 | A→B→C | [C, B, A] | unit |
| 循环依赖 | A→B→A | warnings 包含循环提示 | unit |
| 依赖已安装 | B 已在 installed | 跳过 B | unit |
| 依赖不存在 | A 依赖 X（不在索引） | warnings 包含未找到 | unit |
| 多仓库同名 | B 在两个仓库 | 优先同仓库，warnings 提示 | unit |

### 模块：index (parse_skill_md)

| 用例 | 输入 | 预期输出 | 类型 |
|------|------|----------|------|
| 正常 SKILL.md | 完整 frontmatter | 解析出 name, description | unit |
| 多行 description | YAML 多行语法 | 合并为单行 | unit |
| 带 dependencies | frontmatter 含 dependencies | 解析出列表 | unit |
| 无 frontmatter | 纯 markdown | 返回 None | unit |
| 缺少 name | 只有 description | 返回 None | unit |
| 缺少 description | 只有 name | 返回 None | unit |
| 文件不存在 | 不存在的路径 | 返回 None | unit |

### 模块：index (search)

| 用例 | 输入 | 预期输出 | 类型 |
|------|------|----------|------|
| 关键词匹配 name | "pdf" | 匹配 pdf-processor | unit |
| 关键词匹配 description | "extract text" | 匹配含该描述的 skill | unit |
| 多关键词 | "pdf text" | 两个关键词都匹配的排前面 | unit |
| 无匹配 | "zzzzz" | 空结果 | unit |

### 模块：hook

| 用例 | 输入 | 预期输出 | 类型 |
|------|------|----------|------|
| 今天已同步 | last_sync = 今天 | 不启动 worker | unit |
| 今天未同步 | last_sync = 昨天 | 启动 worker | unit |
| last_sync 为 null | 首次运行 | 启动 worker | unit |
| config 不存在 | 未初始化 | 直接返回 | unit |
| worker 正在运行 | PID 文件存在且进程活着 | 跳过启动 | unit |
| PID 文件残留 | PID 文件存在但进程已死 | 清理并启动 | unit |

### 模块：main

| 用例 | 输入 | 预期输出 | 类型 |
|------|------|----------|------|
| install 到新目录 | 空目标路径 | 复制源码 + 创建数据目录 + 安装规则 | unit |
| install 排除项 | 源码含 __pycache__ | 目标不含 __pycache__ | unit |
| update 保留数据 | 已有数据目录 | 数据目录保留 | unit |
| uninstall 删除数据 | keep_data=False | 数据目录被删除 | unit |
| uninstall 保留数据 | keep_data=True | 数据目录保留 | unit |

## 测试策略

- 沙箱隔离：所有文件操作在 `testdata/runtime/` 下
- 环境变量覆盖：通过 `SKILL_STORE_DATA_DIR` 指向沙箱
- 模块覆盖：每个 lib/ 和 scripts/ 模块至少一个测试文件
- 不 mock Git 命令：git_ops 的 clone/pull 为集成测试，单元测试仅测 run_git 和 is_git_repo

## 不测试的范围

- 真实 Git 仓库的 clone/pull（需要网络，属于集成测试）
- async_worker.py 的完整流程（需要真实仓库）
- Cursor 会话 Hook 的实际触发（需要 Cursor 环境）
