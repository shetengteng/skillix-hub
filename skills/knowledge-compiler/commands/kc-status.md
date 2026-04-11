# 命令: kc status

显示知识库健康状态和统计摘要。优先从 Registry 和 State 文件汇总，避免全文扫描。

## 用法

```
kc status
```

---

## 数据源优先级

1. `.kc-config.json` — 配置信息
2. `wiki/INDEX.md` Topic Registry — topic 元数据汇总
3. `.compile-state.json` — 编译状态和 mtime
4. `wiki/log.md` — 最近编译记录

> 不要默认扫描所有 `wiki/concepts/*.md` 文件。上述 4 个文件应包含足够信息。

---

## 步骤

1. **验证配置。** 检查 `.kc-config.json` 是否存在。不存在 → "未找到知识库。请先运行 `kc init`。"

2. **从 Registry 汇总 topic 统计：**
   - 总 topic 数
   - 按覆盖度分布（high/medium/low）
   - 按分类分布

3. **从 .compile-state.json 检查新鲜度：**
   - 对比源文件当前 mtime 与记录的 mtime
   - 统计自上次编译后变更的源文件数
   - 统计超过 30 天未更新的 topic 数

4. **从 .kc-config.json 读取配置信息：**
   - 源目录列表
   - 语言设置
   - 会话模式

5. **从 wiki/log.md 读取最近编译记录。**

6. **检索质量快检**（不做完整 lint，仅快速扫描 Registry）：
   - Registry 中是否有 summary 为空的 topic
   - Registry 中是否有 answers 为空的 topic
   - Registry 中是否有 tags 数量 <3 的 topic

7. **输出报告：**
   ```
   知识库状态
   ─────────────────────
   源目录:     doc/, design/
   语言:       zh
   模式:       recommended

   主题:       10 个已编译
   覆盖度:     high 70% | medium 20% | low 10%
   新鲜度:     2 个源文件自上次编译后有变更
               1 个主题超过 30 天未更新
   上次编译:   2026-04-08（增量，3 个主题更新）

   检索质量:   ✓ 全部 topic 有 summary
               ✗ 1 个 topic 缺少 answers
               ✗ 2 个 topic tags 不足 3 个

   建议操作:
     - 运行 `kc compile` 处理 2 个变更的源文件
     - 运行 `kc lint` 检查检索质量问题
   ```
