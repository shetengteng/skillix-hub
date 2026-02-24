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
node tool.js run '{{PARAMS_EXAMPLE}}'
```

## LLM 执行协议

### 正常路径

调用 `node tool.js run '{{PARAMS_EXAMPLE}}'`，返回 `completed: true` 时任务完成。

### 自愈路径（run 返回 completed: false 时）

tool.js 的 `run` 命令会尝试所有可用的元素定位方式。如果全部失败，会返回：
- `failedStep.intent`：这步要实现什么目标（含上下文和期望结果）
- `failedStep.allLocators`：录制时采集到的所有定位信息
- `failedStep.screenshot`：失败时的页面截图路径（如有）
- `recovery.nextStartFrom`：手动处理后应从哪步恢复

**处理步骤：**

1. 查看 `failedStep.intent` 了解操作目标
2. 如有截图路径，读取截图了解页面状态；或调用 playwright snapshot 获取可访问性树：
   ```bash
   node ~/.cursor/skills/playwright/tool.js snapshot '{}'
   ```
3. 根据 intent 在当前页面中定位目标元素，使用 playwright skill 手动执行该步骤
4. 确认操作效果符合预期（页面状态变化）
5. 从下一步恢复自动化执行：
   ```bash
   node tool.js run '{"startFrom": <recovery.nextStartFrom>, ...其他参数}'
   ```

### 通用等待原则

任何步骤执行前，若页面有加载状态（spinner、骨架屏、进度条），先等待加载完成再操作：

```bash
node ~/.cursor/skills/playwright/tool.js waitFor '{"selectorGone": ".loading-spinner", "timeout": 15000}'
```

## 触发词

- {{WORKFLOW_NAME}}
- 执行{{WORKFLOW_NAME}}
