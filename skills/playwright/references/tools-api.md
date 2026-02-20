# Playwright Skill - 完整工具 API 参考

所有命令格式：`node skills/playwright/tool.js <命令> '<JSON参数>'`

---

## 导航

### navigate
导航到指定 URL。
```json
{"url": "https://example.com"}
```

### goBack
返回上一页。
```json
{}
```

### goForward
前进到下一页。
```json
{}
```

### reload
重新加载当前页面。
```json
{}
```

---

## 快照与交互

### snapshot
获取页面无障碍树（含元素 ref）。
```json
{}
```
可选：`{"filename": "snapshot.yml"}` 保存到文件。

### click
通过 ref 点击元素。
```json
{"ref": "e42", "element": "提交按钮"}
```
可选参数：`doubleClick`（布尔）、`button`（"left"|"right"|"middle"）、`modifiers`（["Alt","Control","Shift","Meta"]）、`forceJsClick`（布尔，使用 JS `element.click()` 替代 Playwright click，适用于 Vue/React 自定义组件事件不触发的场景）

### drag
从一个元素拖拽到另一个元素。
```json
{"startRef": "e10", "startElement": "源元素", "endRef": "e20", "endElement": "目标元素"}
```

### hover
悬停在元素上。
```json
{"ref": "e42", "element": "菜单项"}
```

### selectOption
选择下拉选项。
```json
{"ref": "e15", "element": "国家", "values": ["CN"]}
```

### check
勾选复选框/单选框。
```json
{"ref": "e30", "element": "同意条款"}
```

### uncheck
取消勾选复选框。
```json
{"ref": "e30", "element": "同意条款"}
```

---

## 键盘

### type
向元素输入文本。自动 fallback：`fill()` 失败时尝试内部 `input/textarea`，再失败则用 `pressSequentially` 逐字输入。
```json
{"ref": "e10", "element": "邮箱输入框", "text": "user@example.com"}
```
可选：`submit`（布尔，输入后按回车）、`slowly`（布尔，逐字符输入）

### pressKey
按下键盘按键。
```json
{"key": "Enter"}
```

### pressSequentially
逐字符输入文本（无元素目标）。
```json
{"text": "hello", "submit": true}
```

### keydown / keyup
按下/释放按键。
```json
{"key": "Shift"}
```

---

## 表单

### fillForm
批量填写多个表单字段。`textbox` 类型自动 fallback（fill → 内部 input → pressSequentially）。`combobox` 类型自动兼容自定义下拉组件（selectOption 失败时改用 click 展开 → click option）。
```json
{
  "fields": [
    {"name": "邮箱", "type": "textbox", "ref": "e10", "value": "user@example.com"},
    {"name": "密码", "type": "textbox", "ref": "e11", "value": "secret"},
    {"name": "记住我", "type": "checkbox", "ref": "e12", "value": "true"},
    {"name": "国家", "type": "combobox", "ref": "e13", "value": "中国"}
  ]
}
```

---

## 鼠标

### mouseMove
```json
{"x": 100, "y": 200}
```

### mouseClick
在坐标位置点击。
```json
{"x": 100, "y": 200}
```

### mouseDrag
在坐标之间拖拽。
```json
{"startX": 100, "startY": 200, "endX": 300, "endY": 400}
```

### mouseDown / mouseUp
```json
{"button": "left"}
```

### mouseWheel
```json
{"deltaX": 0, "deltaY": 100}
```

---

## 截图

### screenshot
```json
{"type": "png"}
```
可选：`filename`、`fullPage`（布尔）、`ref`+`element`（元素截图）

---

## 等待

### waitFor
等待文本出现、文本消失或指定时间。默认超时 60 秒（navigation timeout）。
```json
{"text": "加载完成"}
```
```json
{"textGone": "加载中..."}
```
```json
{"time": 3}
```
可选：`timeout`（毫秒，自定义超时时间，如 `{"text":"加载完成","timeout":30000}`）

---

## 标签页

### tabs
管理浏览器标签页。
```json
{"action": "list"}
```
操作：`list`（列表）、`new`（新建）、`close`（关闭，可选 `index`）、`select`（选择，需要 `index`）

---

## 控制台与网络

### consoleMessages
```json
{"level": "error"}
```
级别：`error`、`warning`、`info`、`debug`

### consoleClear
```json
{}
```

### networkRequests
```json
{"includeStatic": false}
```

### networkClear
```json
{}
```

---

## 对话框与文件

### handleDialog
```json
{"accept": true, "promptText": "可选文本"}
```

### fileUpload
```json
{"paths": ["/绝对路径/文件.pdf"]}
```

---

## Cookie

### cookieList
```json
{}
```
可选：`domain`、`path` 过滤。

### cookieGet
```json
{"name": "session_id"}
```

### cookieSet
```json
{"name": "token", "value": "abc123", "domain": "example.com"}
```
可选：`path`、`expires`、`httpOnly`、`secure`、`sameSite`

### cookieDelete
```json
{"name": "token"}
```

### cookieClear
```json
{}
```

---

## 存储状态

### storageState
保存 Cookie + localStorage 到文件。
```json
{"filename": "state.json"}
```

### setStorageState
从文件恢复。
```json
{"filename": "state.json"}
```

---

## Web 存储

### localStorageList / sessionStorageList
```json
{}
```

### localStorageGet / sessionStorageGet
```json
{"key": "theme"}
```

### localStorageSet / sessionStorageSet
```json
{"key": "theme", "value": "dark"}
```

### localStorageDelete / sessionStorageDelete
```json
{"key": "theme"}
```

### localStorageClear / sessionStorageClear
```json
{}
```

---

## 网络拦截

### route
模拟网络请求。
```json
{"pattern": "**/api/users", "status": 200, "body": "{\"users\":[]}", "contentType": "application/json"}
```
修改请求头：`headers`（"Name: Value" 数组）、`removeHeaders`（逗号分隔）

### routeList
```json
{}
```

### unroute
```json
{"pattern": "**/api/users"}
```
省略 pattern 移除所有路由。

---

## 高级功能

### evaluate
在页面执行 JavaScript。
```json
{"function": "() => document.title"}
```
带元素：`{"function": "(el) => el.textContent", "ref": "e42", "element": "标题"}`

### runCode
执行 Playwright 代码片段。
```json
{"code": "async (page) => { await page.getByRole('button', { name: 'Submit' }).click(); return await page.title(); }"}
```

### pdf
将页面保存为 PDF（仅 Chromium）。
```json
{"filename": "page.pdf"}
```

### tracingStart / tracingStop
```json
{}
```

### startVideo
```json
{"size": {"width": 1280, "height": 720}}
```

### stopVideo
```json
{"filename": "recording.webm"}
```

---

## 测试/验证

### verifyElement
```json
{"role": "button", "accessibleName": "提交"}
```

### verifyText
```json
{"text": "欢迎回来"}
```

### verifyList
```json
{"ref": "e50", "element": "导航", "items": ["首页", "关于", "联系"]}
```

### verifyValue
```json
{"type": "textbox", "ref": "e10", "element": "邮箱", "value": "user@example.com"}
```

### generateLocator
为元素生成 Playwright 定位器字符串。
```json
{"ref": "e42", "element": "提交按钮"}
```

---

## 系统

### install
安装浏览器。
```json
{}
```

### getConfig
显示当前配置。
```json
{}
```

### devtoolsStart
启动 DevTools 服务器。
```json
{}
```

### close
关闭浏览器。
```json
{}
```

### resize
调整浏览器窗口大小。
```json
{"width": 1280, "height": 720}
```
