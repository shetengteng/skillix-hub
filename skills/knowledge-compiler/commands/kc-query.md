# 命令: kc query

基于 wiki 回答问题。以 INDEX.md 为入口，读取相关主题文章，合成带引用的回答。

## 用法

```
kc query <问题>
kc query <问题> --save       # 将回答保存到 wiki/analyses/
```

---

## 步骤

1. **验证配置。** 检查 `.kc-config.json` 和 `wiki/INDEX.md` 是否存在且有内容。如果 wiki 为空："未找到编译的 wiki。请先运行 `kc compile`。"

2. **读取 INDEX.md**，识别与问题相关的主题。

3. **读取主题文章**（`wiki/concepts/{slug}.md`）。

4. **按覆盖度分级处理**每个与问题相关的章节：

   | 覆盖度 | AI 行为 |
   |--------|--------|
   | `high` | 直接引用，无需附加说明。 |
   | `medium` | 引用但加注："基于单一来源，可能需补充"。如果是高风险决策问题，额外回查原始文件验证。 |
   | `low` | 必须先读取引用的原始文件再回答。如果原始文件有更多细节，补充到回答中。如果无法确认，明确说明覆盖度有限。 |

5. **合成回答**，附带引用：
   - Wiki 引用：`[wiki: wiki/concepts/topic-slug.md]`
   - 原始文件引用：`[source: doc/foo.md]`
   - 对 `medium` 章节：加注"*（基于单一来源，可能需补充）*"
   - 对 `low` 章节：加注"*（覆盖度有限，以上已从原始文件验证）*"

6. **按需保存。** 如果设置了 `--save`，或回答涉及多主题综合分析，询问：
   "这个回答值得保留。保存到 `wiki/analyses/`？(y/n)"

   如果是：
   - 创建 `wiki/analyses/{YYYY-MM-DD}-{question-slug}.md`
   - 在 `wiki/INDEX.md` 的分析记录区域添加条目

7. **记录日志。** 追加到 `wiki/log.md`：
   ```
   ## [YYYY-MM-DD] query | <问题摘要>
   ```

---

## 注意事项

- 查询命令通过覆盖度标签决定信任程度：`high` 直接信任，`medium` 带保留引用，`low` 必须回查原始文件。
- 保存的分析结果成为 wiki 的一部分，可被后续查询引用。
- `wiki/analyses/` 目录在首次保存时自动创建（如果不存在）。
