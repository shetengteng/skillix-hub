# 命令: kc lint

对 wiki 运行健康检查。检测结构问题，可选自动修复。

## 用法

```
kc lint                  # 仅报告（只读，不修改任何文件）
kc lint --fix            # 报告并自动修复安全可修复的问题
```

---

## 步骤

1. **验证配置。** 检查 `.kc-config.json` 存在且 `wiki/` 目录有内容。

2. **加载质量门控定义。** 读取 [references/quality-gates.md](../references/quality-gates.md) 获取完整定义。

3. **运行 Hard Gate 检查：**

   | 检查项 | 操作 |
   |--------|------|
   | Frontmatter 完整 | 扫描每个 `wiki/concepts/*.md`，检查必需 YAML 字段：`id`、`title`、`sources`、`created`、`updated` |
   | 覆盖度标记 | 验证每个 `## 章节` 后有 `<!-- coverage: X -->` 注释 |
   | 来源引用有效 | 检查每个 `[source: path]` 指向的文件确实存在 |
   | Schema 一致性 | `wiki/concepts/` 中每个主题在 `wiki/schema.md` 中有对应条目 |
   | 非空内容 | 每个章节有实质内容（不仅仅是标题和覆盖度标记） |

4. **运行 Soft Gate 检查：**

   | 检查项 | 操作 |
   |--------|------|
   | 过期文章 | 对比源文件 mtime 与 `.compile-state.json`——标记自上次编译后有变更的源 |
   | 孤立页面 | 查找未被 INDEX.md 或其他文章通过 `[[链接]]` 引用的 wiki 页面 |
   | 缺失交叉引用 | 查找文章文本中提到但未用 `[[slug]]` 链接的其他主题 |
   | 低覆盖集群 | 标记所有章节都是 `low` 覆盖度的主题 |
   | 内容矛盾 | 识别不同主题文章中关于同一事物的矛盾说法 |
   | Schema 漂移 | 查找 schema.md 中有但无文件、或有文件但不在 schema 中的主题 |
   | 断裂链接 | 查找 `[[slug]]` 指向不存在页面的引用 |
   | 缺失可选 frontmatter | 缺少推荐但非必须的字段（tags、relations） |

5. **输出报告。**

   `kc lint`（不带 `--fix`）为**只读模式**。仅报告发现，不修改文件，不提示"是否修复"。

   ```
   kc lint 报告 — YYYY-MM-DD
   ──────────────────────────────────
   Hard Gates: X 通过, Y 失败
     [失败] wiki/concepts/rag.md — ## 注意事项 缺少覆盖度标记
     [失败] wiki/concepts/moe.md — [source: raw/old-file.md] 文件不存在

   Soft Gates: N 个警告
     [过期]   wiki/concepts/api-design.md — 源文件 5 天前有变更
     [孤立]   wiki/concepts/old-topic.md — 无入站链接
     [低覆盖] wiki/concepts/moe.md — 4/5 章节为低覆盖

   2 个可自动修复的问题。运行 `kc lint --fix` 修复。
   ```

6. **自动修复**（仅当 `--fix` 标志存在时）：
   - 添加缺失的 `<!-- coverage: low -->` 标记。
   - 添加缺失的主题到 schema.md。
   - 移除指向已删除文件的引用（附警告注释）。
   - 报告每个已应用的修复。不做交互式询问——`--fix` 意味着"修复所有安全可修复的问题"。

7. **记录日志。** 追加到 `wiki/log.md`：
   ```
   ## [YYYY-MM-DD] lint | X 个 hard gate 问题, Y 个 soft gate 警告, Z 个已修复
   ```
