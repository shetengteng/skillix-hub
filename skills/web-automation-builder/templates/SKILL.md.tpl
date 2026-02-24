---
name: {{SKILL_NAME}}
description: |
  自动化工作流：{{WORKFLOW_NAME}}。
  由 web-automation-builder 录制生成。
---

# {{WORKFLOW_NAME}}

{{DESCRIPTION}}

## 参数

{{PARAM_TABLE}}

## 操作步骤

{{STEPS_DESC}}

## 使用

```bash
# 批量执行（快速路径）
node tool.js run '{{PARAMS_EXAMPLE}}'

# LLM-First 逐步执行（推荐）
node tool.js steps '{}'
node tool.js step '{"step": 1, ...params}'
```

## LLM 执行协议（LLM-First）

本 Skill 的执行者是 LLM，具备视觉理解和推理能力。执行策略以 LLM 判断为主，工具辅助为辅。

### 执行流程

1. **阅读步骤**：调用 `node tool.js steps '{}'` 获取完整步骤列表，理解每步的 intent
2. **逐步执行**：对每一步，根据置信度选择执行方式：

   **方式 A — 工具执行**（适用于：navigate、有明确 text 的简单 click）：
   ```bash
   node tool.js step '{"step": N, {{PARAMS_KEYS}}}'
   ```
   返回 `success: true` 则继续下一步。

   **方式 B — LLM 直接操作**（适用于：modal 内操作、动态 ID 元素、表单填写、不确定的交互）：
   1. 调用 `playwright snapshot` 查看当前页面状态
   2. 根据步骤 intent 识别目标元素
   3. 使用 playwright skill 直接执行操作（click/fill/select 等）
   4. 确认操作效果

3. **失败处理**：如果 `step` 命令返回 `success: false`，不要重试——直接切换为方式 B 手动操作

### 批量快速路径（可选）

如果对所有步骤都有高置信度，可以一次性执行：
```bash
node tool.js run '{{PARAMS_EXAMPLE}}'
```
返回 `completed: true` 时任务完成。失败时按上述方式 B 处理，然后 `run '{"startFrom": N, ...}'` 恢复。

### 通用原则

- 任何操作前，若页面有加载状态（spinner、骨架屏），先等待加载完成
- 优先相信自己的视觉判断，不要盲目依赖录制时的 locator
- 每步执行后确认页面状态变化符合 intent 描述的预期

## 自我优化协议

本 Skill 支持执行后自我优化。每次执行完成后，按以下流程操作：

### 回放后总结

执行完所有步骤后（无论全部通过还是中途手动介入），回顾整个执行过程：

1. **识别差异**：哪些步骤直接用 `step` 命令成功？哪些需要切换到手动模式（snapshot + evaluate/click）？
2. **记录发现**：
   - 失效的 locator 和实际有效的替代方案（如 ariaLabel、精确 CSS）
   - waitAfter 超时但页面已就绪的情况
   - 需要额外操作（滚动、等待、处理多按钮歧义）的步骤
3. **提交报告**：

```bash
node tool.js report-replay '{"overallSuccess":true,"steps":[{"step":1,"method":"tool","issues":[]},{"step":2,"method":"llm-manual","issues":["locator失效"],"successLocator":{"type":"ariaLabel","value":"实际有效的值"}}]}'
```

### Trace 字段说明

| 字段 | 说明 |
|------|------|
| `step` | 步骤编号（1-based） |
| `method` | `"tool"` = step 命令直接成功，`"llm-manual"` = 切换到手动操作 |
| `issues` | 遇到的问题列表（字符串数组） |
| `successLocator` | 手动操作时实际有效的定位方式，`type` 可选：ariaLabel/css/text/role/testId/id |

### 优化触发

提交 trace 后，如果有可优化项，工具会返回优化建议。按提示决定是否应用优化。

## 触发词

- {{WORKFLOW_NAME}}
- 执行{{WORKFLOW_NAME}}
