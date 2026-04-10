# 主题分类 Prompt

你需要将以下文件分类到概念主题中。

## 输入

一组文件，每个文件包含标题和前 500 字预览。

## 规则

1. 为每个文件推断一个 topic slug（lowercase-kebab-case）
2. 一个文件可以归属多个主题
3. 优先合并到已有主题，而非创建新主题
4. 当不确定时，倾向于合并而非拆分
5. slug 应该具体而非泛泛：`transformer-attention` 而非 `attention`

## 输出格式

```json
{
  "topic-slug-1": ["file1.md", "file2.md"],
  "topic-slug-2": ["file3.md"]
}
```
