# 命令: kc compile

触发知识库编译。实际编译工作委托给 [skills/wiki-compiler.md](../skills/wiki-compiler.md)。

## 用法

```
kc compile                 # 增量编译（仅处理变更的源文件）
kc compile --full          # 全量编译（重新处理所有源文件）
kc compile --dry-run       # 预览模式（不写入任何文件）
kc compile --topic <slug>  # 仅编译指定主题
```

---

## 步骤

1. **验证配置。** 检查 `.kc-config.json` 是否存在。不存在则提示："未找到知识库。请先运行 `kc init`。"

2. **解析标志。** 识别用户意图中的 flag：
   - "全量编译" / "重新编译所有" → `--full`
   - "先看看会改什么" / "预览一下" → `--dry-run`
   - "只编译 xxx" → `--topic <slug>`

3. **加载编译管道。** 读取 [skills/wiki-compiler.md](../skills/wiki-compiler.md)，按 5 阶段管道执行。

4. **报告结果：**
   ```
   编译完成: X 新建, Y 更新, Z 未变
   Hard Gates: 全部通过 / N 个问题已修复
   Soft Gates: N 个警告
   Wiki: wiki/INDEX.md
   ```
