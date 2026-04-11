# 命令: kc status

显示知识库健康状态和统计摘要。

## 用法

```
kc status
```

---

## 步骤

1. **验证配置。** 检查 `.kc-config.json` 是否存在。不存在则提示："未找到知识库。请先运行 `kc init`。"

2. **统计源文件。** 遍历 `.kc-config.json` 中配置的所有 source 目录：
   ```bash
   find {source_dirs} -name "*.md" | wc -l
   ```
   按目录分别统计数量。

3. **统计已编译主题：**
   ```bash
   ls wiki/concepts/*.md 2>/dev/null | wc -l
   ```

4. **读取覆盖度分布。** 扫描所有 `wiki/concepts/*.md` 文件，统计覆盖度标记：
   - 所有主题的总章节数
   - high / medium / low 各有多少

5. **检查新鲜度。** 读取 `.compile-state.json` 对比 mtime：
   - 上次编译后有多少源文件发生了变更？
   - 多少主题超过 30 天未更新？

6. **读取上次编译信息。** 从 `wiki/log.md` 读取最后一条记录。

7. **输出报告：**
   ```
   知识库状态
   ─────────────────────
   源文件:     42 个（designs: 12, decisions: 8, research: 15, notes: 7）
   主题:       18 个已编译概念
   覆盖度:     high 45% | medium 35% | low 20%
   新鲜度:     3 个源文件自上次编译后有变更
               2 个主题超过 30 天未更新
   上次编译:   2026-04-08（增量，更新 3 个主题）
   配置:       session_mode=recommended, language=zh

   建议操作:
     - 运行 `kc compile` 处理 3 个变更的源文件
     - 运行 `kc lint` 检查 2 个过期主题
   ```
