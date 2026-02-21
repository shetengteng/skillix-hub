# Skillix Hub

AI Programming Assistant Skills Repository - A collection of tools to enhance AI programming efficiency.

## What is AI Skill?

AI Skill is a reusable AI instruction set that helps AI programming assistants better complete specific tasks. Each Skill includes:
- Task description and trigger conditions
- Execution scripts and tools
- Usage examples

**Supported AI Assistants**: Cursor, Claude, Copilot, Codeium, etc.

## Available Skills

| Skill | Description |
|-------|-------------|
| [memory](./skills/memory/) | Long-term memory for AI assistants, auto-record conversations and retrieve relevant history |
| [behavior-prediction](./skills/behavior-prediction/) | Learn user behavior patterns, record sessions, predict next actions and provide smart suggestions |
| [continuous-learning](./skills/continuous-learning/) | Continuously learn from user-AI interactions, extract reusable knowledge, generate new skills |
| [swagger-api-reader](./skills/swagger-api-reader/) | Read and cache Swagger/OpenAPI docs with browser auth support |
| [uniapp-mp-generator](./skills/uniapp-mp-generator/) | uni-app mini-program code generator, auto-generate Vue3 pages, API, Store from requirements |
| [playwright](./skills/playwright/) | Browser automation via 48 CLI commands controlling a real browser. Navigate, click, fill forms, screenshot, manage cookies/storage, intercept network, and more |
| [api-tracer](./skills/api-tracer/) | Record and analyze browser network requests via CDP, capture full API info (URL, headers, cookies, request/response body), generate reports for automation |
| [web-content-reader](./skills/web-content-reader/) | Read web page content with automatic SPA detection and browser rendering fallback for Vue/React pages |

## Installation

### Method 1: Install via Cursor Natural Language (Recommended)

Simply tell Cursor AI in natural language to install the desired Skill:

**Global Installation** (Available for all projects):
```
Please install memory skill from https://github.com/shetengteng/skillix-hub, I want it available for all my projects
```

**Project Installation** (Available for current project only):
```
Please install memory skill from https://github.com/shetengteng/skillix-hub to current project
```

Cursor AI will automatically clone the repository, copy files, and install dependencies.

**Update Skill**:
```
Please update memory skill from https://github.com/shetengteng/skillix-hub
```

> **Note**: When updating, the Agent clones the latest code and runs `update.py` instead of directly overwriting files. This ensures placeholders are properly replaced and existing memory data and config are preserved.

Manual update command:
```bash
git clone https://github.com/shetengteng/skillix-hub.git /tmp/skillix-hub
python3 /tmp/skillix-hub/skills/memory/scripts/service/init/update.py --source /tmp/skillix-hub/skills/memory --project-path .
```

### Method 2: Manual Command Line Installation

#### Global Installation (Available for all projects)

```bash
# Clone repository
git clone https://github.com/shetengteng/skillix-hub.git

# Copy Memory Skill to Cursor skills directory
cp -r skillix-hub/skills/memory ~/.cursor/skills/

# Copy Swagger API Reader to Cursor skills directory
cp -r skillix-hub/skills/swagger-api-reader ~/.cursor/skills/

# Install Swagger API Reader dependencies
pip install -r ~/.cursor/skills/swagger-api-reader/scripts/requirements.txt
```

#### Project Installation (Available for current project only)

```bash
# In project root
mkdir -p .cursor/skills

# Copy desired Skills
cp -r skillix-hub/skills/memory .cursor/skills/
cp -r skillix-hub/skills/swagger-api-reader .cursor/skills/

# Install dependencies (if needed)
pip install -r .cursor/skills/swagger-api-reader/scripts/requirements.txt
```

## Memory Skill Usage

Memory Skill provides cross-session long-term memory for AI assistants with zero external dependencies. It uses Hook mechanisms to automatically save and recall memories throughout session lifecycles.

### Architecture

```
skills/memory/scripts/
├── core/           # Infrastructure: embedding vectors, file lock, utilities
├── storage/        # Storage layer: JSONL read/write, SQLite vector search, Markdown chunking
├── service/
│   ├── hooks/      # Hook entries: load_memory, flush_memory, prompt_session_save
│   ├── memory/     # Memory ops: save_fact, save_summary, search_memory, sync_index
│   ├── manage/     # Management: list, delete, edit, config, index
│   ├── init/       # One-click initialization
│   ├── config/     # Configuration management
│   └── logger/     # Logging system
```

### Core Features

- **Auto Memory**: Auto-save facts and summaries via [Memory Flush] / [Session Save] Hooks
- **Semantic Search**: Local embedding model + SQLite FTS + vector similarity hybrid search
- **Fact Storage**: Categorized storage for W(World facts) / B(Biographical) / O(Opinions)
- **Memory Management**: List, search, delete, edit, export memories
- **Natural Language Config**: Modify configuration through conversation, no manual JSON editing

### Usage Examples

```bash
# One-click init (creates hooks, rules, data directory)
python3 ~/.cursor/skills/memory/scripts/service/init/index.py

# Save a fact
python3 ~/.cursor/skills/memory/scripts/service/memory/save_fact.py \
  --content "Project uses PostgreSQL" --type W --confidence 0.9

# Save session summary
python3 ~/.cursor/skills/memory/scripts/service/memory/save_summary.py \
  --topic "API Design Discussion" --summary "Discussed RESTful interface design"

# Search memory
python3 ~/.cursor/skills/memory/scripts/service/memory/search_memory.py "API Design"

# Manage memories (list, delete, edit, export, etc.)
python3 ~/.cursor/skills/memory/scripts/service/manage/index.py list
python3 ~/.cursor/skills/memory/scripts/service/manage/index.py delete --keyword "test"
python3 ~/.cursor/skills/memory/scripts/service/manage/index.py config show
python3 ~/.cursor/skills/memory/scripts/service/manage/index.py config set memory.facts_limit 30

# View SQLite index database
python3 ~/.cursor/skills/memory/scripts/service/manage/index.py db stats
python3 ~/.cursor/skills/memory/scripts/service/manage/index.py db show chunks --limit 10
python3 ~/.cursor/skills/memory/scripts/service/manage/index.py db browse  # Browser UI (requires datasette)
```

### Natural Language Configuration

After installation, manage configuration directly through natural language:

```
User: Show me the current memory configuration
User: Load more days of memory, set full load to 5 days
User: Set log level to DEBUG
User: Change facts loading limit to 30
User: Switch to a different embedding model, use BAAI/bge-base-zh-v1.5
User: Reset configuration to defaults
```

Full configuration reference available in `memory-data/README.md` after installation.

### Memory Types

| Type | Prefix | Description | Example |
|------|--------|-------------|---------|
| World | W | Objective facts | "Project uses PostgreSQL database" |
| Biographical | B | Project milestones | "2026-02-17 completed API refactoring" |
| Opinion | O | Preferences/judgments | "User prefers TypeScript (confidence: 0.9)" |
| Summary | S | Session summaries | "Discussed API design approach" |

### Trigger Words

- **Retrieval Triggers**: continue, last time, before, yesterday, we discussed
- **Save Triggers**: remember this, save this
- **View Memories**: view memories, search memories
- **Manage Memories**: delete memory, edit memory, export memory
- **Config Management**: view config, modify config, adjust load days
- **Database Viewer**: open database, view index contents, database statistics

## Behavior Prediction Skill V2 Usage

Behavior Prediction Skill V2 learns user behavior patterns, records session content, predicts next actions and provides smart suggestions.

### Core Features

- **Session Recording**: Record complete session content at session end
- **Pattern Learning**: Extract workflow, preferences, project patterns
- **Smart Prediction**: Predict next actions based on patterns
- **User Profile**: Generate comprehensive user profile
- **Auto Execute**: Support auto-execution for high-confidence predictions

### Usage Examples

```bash
# Initialize at session start
python3 ~/.cursor/skills/behavior-prediction/scripts/hook.py --init

# Record at session end
python3 ~/.cursor/skills/behavior-prediction/scripts/hook.py --finalize '{
  "session_summary": {
    "topic": "API Development",
    "workflow_stages": ["design", "implement", "test"]
  },
  "operations": {"files": {"created": ["user.py"], "modified": [], "deleted": []}, "commands": []},
  "conversation": {"user_messages": [], "message_count": 5},
  "time": {"start": "2026-01-31T10:00:00Z", "end": "2026-01-31T10:30:00Z"}
}'

# Get predictions
python3 ~/.cursor/skills/behavior-prediction/scripts/get_predictions.py '{"current_stage": "implement"}'

# View user profile
python3 ~/.cursor/skills/behavior-prediction/scripts/user_profile.py

# Update user profile
python3 ~/.cursor/skills/behavior-prediction/scripts/user_profile.py '{"action": "update"}'

# View behavior patterns
python3 ~/.cursor/skills/behavior-prediction/scripts/extract_patterns.py
```

### Trigger Words

- **View Patterns**: view my behavior patterns, view behavior statistics
- **View Profile**: view user profile, update user profile
- **Predict**: predict next step

## uni-app Mini Program Code Generator Usage

uni-app mini-program code generator automatically generates code that conforms to project standards from requirements documents.

### Core Features

- **Page Generation**: Auto-generate Vue3 pages (list, detail, form)
- **API Generation**: Generate CRUD interface files
- **Store Generation**: Generate Pinia state management
- **Component Generation**: Generate card, filter components
- **Schema Generation**: Generate database collection definitions

### Usage

Provide requirements document, AI will auto-generate code:

```markdown
# Student Management Module

## Data Fields
- name: Name (required, string)
- phone: Phone (required, string)
- status: Status (required, enum: active/inactive)

## Pages
- Student list page
- Student detail page
- Add student page
```

### Trigger Words

- **Generate Code**: help me generate xxx module
- **From Requirements**: generate code from requirements document

## Continuous Learning Skill Usage

Continuous Learning Skill automatically extracts reusable knowledge from user-AI interactions and generates new skill files.

### Core Features

- **Observation Recording**: Record key actions and user feedback during sessions
- **Pattern Detection**: Identify user corrections, error resolutions, tool preferences
- **Instinct Generation**: Convert detected patterns into atomic instincts
- **Skill Evolution**: Aggregate related instincts into complete skill documents

### Pattern Types

| Pattern Type | Description | Example |
|-------------|-------------|---------|
| **User Corrections** | User corrects AI behavior | "Don't use class, use functions" |
| **Error Resolutions** | Solutions for specific errors | CORS error → configure proxy |
| **Tool Preferences** | User's preferred tools/methods | Prefer pytest over unittest |
| **Project Conventions** | Project-specific conventions | API paths use /api/v2 prefix |

### Usage Examples

```bash
# Initialize at session start
python3 ~/.cursor/skills/continuous-learning/scripts/observe.py --init

# Record observation
python3 ~/.cursor/skills/continuous-learning/scripts/observe.py --record '{"event": "tool_call", "tool": "Write"}'

# Save at session end
python3 ~/.cursor/skills/continuous-learning/scripts/observe.py --finalize '{"topic": "API Development"}'

# View instinct status
python3 ~/.cursor/skills/continuous-learning/scripts/instinct.py status

# Evolve instincts into skills
python3 ~/.cursor/skills/continuous-learning/scripts/instinct.py evolve

# Enable auto learning rules
python3 ~/.cursor/skills/continuous-learning/scripts/setup_rule.py '{"action": "enable"}'
```

### Trigger Words

- **Enable Learning**: enable continuous learning rules
- **Disable Learning**: disable continuous learning rules
- **View Knowledge**: view learned knowledge
- **Evolve Skills**: evolve instincts

## Playwright Skill

Playwright Skill provides 48 browser automation tools via CLI commands, controlling a real Chrome/Chromium browser. Replicated from Playwright MCP.

### Setup

```bash
cd skills/playwright && npm install && npx playwright install chromium
```

### Core Workflow

```bash
# Navigate to page
node skills/playwright/tool.js navigate '{"url":"https://example.com"}'

# Get page snapshot with element refs
node skills/playwright/tool.js snapshot '{}'

# Click element by ref
node skills/playwright/tool.js click '{"ref":"e6","element":"Learn more"}'

# Type text
node skills/playwright/tool.js type '{"ref":"e10","text":"hello@example.com"}'

# Take screenshot
node skills/playwright/tool.js screenshot '{"type":"png"}'
```

### Browser Management

```bash
node skills/playwright/tool.js start    # Launch browser
node skills/playwright/tool.js stop     # Close browser
node skills/playwright/tool.js status   # Check status
```

### MCP Tools Mapping (22 tools)

When `@playwright/mcp` is enabled, the following MCP tools map to Skill CLI commands. **Prefer Skill CLI commands**:

| MCP Tool -> Function | CLI Command |
|---------------------|-------------|
| `browser_navigate` -> Navigate | `navigate` |
| `browser_snapshot` -> Snapshot | `snapshot` |
| `browser_click` -> Click | `click` |
| `browser_type` -> Type | `type` |
| `browser_fill_form` -> Fill Form | `fillForm` |
| `browser_take_screenshot` -> Screenshot | `screenshot` |
| `browser_evaluate` -> Execute JS | `evaluate` |
| `browser_wait_for` -> Wait | `waitFor` |
| `browser_tabs` -> Tabs | `tabs` |
| `browser_network_requests` -> Network | `networkRequests` |
| `browser_close` -> Close | `close` |

### CLI Tools (48 total)

All commands: `node skills/playwright/tool.js <command> '<json_params>'`

| Category | Tools |
|----------|-------|
| Navigation | navigate, goBack, goForward, reload |
| Interaction | snapshot, click, drag, hover, selectOption, check, uncheck, type, pressKey, fillForm |
| Mouse | mouseMove, mouseClick, mouseDrag, mouseDown, mouseUp, mouseWheel |
| Observation | screenshot, consoleMessages, networkRequests, waitFor |
| Tabs | tabs (list/new/close/select) |
| Data | cookieList/Get/Set/Delete/Clear, localStorage/sessionStorage ops, storageState |
| Network | route, routeList, unroute |
| Advanced | evaluate, runCode, pdf, tracingStart/Stop, startVideo/stopVideo |
| Testing | verifyElement, verifyText, verifyList, verifyValue, generateLocator |
| System | install, getConfig, close, resize |

### Trigger Words

- **Browser Ops**: open webpage, navigate to, click button
- **Screenshot**: take screenshot, capture screen
- **Forms**: fill form, type text
- **Testing**: verify element, check text

## API Tracer Skill

API Tracer records browser network requests, analyzes API endpoints, and generates reports for automation. It connects to the Playwright browser instance via CDP to capture full request/response information.

### Prerequisites

Requires Playwright Skill with a running browser. API Tracer connects to the same browser instance via CDP.

### Setup

```bash
cd skills/api-tracer && npm install
```

### Core Workflow

```bash
# 1. Open website with Playwright
node skills/playwright/tool.js navigate '{"url":"https://app.example.com"}'

# 2. Start API recording
node skills/api-tracer/tool.js start '{"name": "my-session", "filter": "api/"}'

# 3. Operate the page via Playwright (login, browse, etc.)
node skills/playwright/tool.js click '{"ref":"e5","element":"Login"}'

# 4. Stop recording
node skills/api-tracer/tool.js stop '{}'

# 5. Generate report
node skills/api-tracer/tool.js report '{"name": "my-session", "format": "markdown"}'
```

### Command Reference

| Command | Description |
|---------|-------------|
| `start` | Start recording (background daemon) |
| `stop` | Stop recording and save |
| `status` | Check recording status |
| `sessions` | List all historical sessions |
| `detail` | View session request list or single request details |
| `report` | Generate analysis report (json/markdown/curl) |
| `delete` | Delete historical session |

### Report Contents

- API endpoint list (auto-deduplicated)
- HTTP method and URL pattern per endpoint
- Request headers (key fields) and cookies
- Request/response body format and schema
- Auth method auto-detection (Bearer Token / API Key, etc.)
- curl command export

### Trigger Words

- **Recording**: start recording network requests, stop recording
- **Viewing**: recording status, show recorded requests
- **Reports**: generate API report, export as curl
- **Management**: list recordings, delete recording

## Web Content Reader Skill

Web Content Reader reads rendered content from any web page. It auto-detects SPA pages and falls back to browser rendering when HTTP fetch fails. Fully independent, no dependency on other Skills.

### Setup

```bash
cd skills/web-content-reader && npm install
```

Browser rendering mode requires Chrome/Chromium installed. If not available:

```bash
npx playwright install chromium
```

### Core Workflow

```bash
# Auto mode (fetch first, fallback to browser for SPA)
node skills/web-content-reader/tool.js read '{"url":"https://example.com"}'

# Force browser mode (known SPA page)
node skills/web-content-reader/tool.js read '{"url":"https://spa-app.com","mode":"browser"}'

# Extract specific area
node skills/web-content-reader/tool.js read '{"url":"https://example.com","selector":".content"}'

# Get full structured data (tables, links, meta)
node skills/web-content-reader/tool.js read '{"url":"https://example.com","output":"json"}'
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `url` | string | required | Target page URL |
| `mode` | string | `auto` | `auto`/`fetch`/`browser` |
| `selector` | string | - | CSS selector to extract specific area |
| `output` | string | `text` | `text`/`html`/`json` |
| `waitSelector` | string | - | Wait for this selector in browser mode |
| `timeout` | number | `15000` | Browser rendering timeout (ms) |

### Trigger Words

- **Read Page**: read this page, show me this webpage
- **SPA Page**: this is a Vue page, fetch can't get data
- **Extract Data**: extract page tables, get page links

## Contributing

PRs are welcome to add new Skills!

### Skill Structure

```
skill-name/
├── SKILL.md              # Required: Main instruction file
├── scripts/              # Optional: Execution scripts
│   ├── main.py
│   └── requirements.txt
└── templates/            # Optional: Template files
```

### SKILL.md Format

```markdown
---
name: skill-name
description: Brief description of functionality and trigger conditions
---

# Skill Title

## Usage
...
```

## License

MIT License
