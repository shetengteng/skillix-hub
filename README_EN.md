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

Memory Skill provides long-term memory capability for AI assistants with zero external dependencies.

### Core Features

- **Auto Retrieval**: Automatically retrieve relevant history based on user questions
- **Smart Saving**: Automatically judge conversation value and save important content
- **Keyword Matching**: Retrieval algorithm based on keywords + time decay
- **View Memories**: View today's/specific date/recent memories
- **Delete Memories**: Delete specific memories or clear all
- **Export/Import**: Backup and restore memory data
- **Auto Memory Rules**: Enable to auto-retrieve at conversation start and save at end

### Usage Examples

```bash
# Save memory
python3 ~/.cursor/skills/memory/scripts/save_memory.py '{"topic": "API Design", "key_info": ["Using FastAPI"], "tags": ["#api"]}'

# Search memory
python3 ~/.cursor/skills/memory/scripts/search_memory.py "API Design"

# View today's memories
python3 ~/.cursor/skills/memory/scripts/view_memory.py today

# Delete specific memory
python3 ~/.cursor/skills/memory/scripts/delete_memory.py '{"id": "2026-01-29-001"}'

# Export memories
python3 ~/.cursor/skills/memory/scripts/export_memory.py

# Import memories
python3 ~/.cursor/skills/memory/scripts/import_memory.py '{"input": "backup.json"}'

# Enable auto memory rules
python3 ~/.cursor/skills/memory/scripts/setup_auto_retrieve.py '{"action": "enable"}'

# Check auto memory status
python3 ~/.cursor/skills/memory/scripts/setup_auto_retrieve.py '{"action": "check"}'

# Update auto memory rules
python3 ~/.cursor/skills/memory/scripts/setup_auto_retrieve.py '{"action": "update"}'

# Disable auto memory rules
python3 ~/.cursor/skills/memory/scripts/setup_auto_retrieve.py '{"action": "disable"}'
```

### Trigger Words

- **Retrieval Triggers**: continue, last time, before, yesterday, we discussed
- **Save Triggers**: remember this, save this
- **Skip Save**: don't save, skip saving
- **View Memories**: view today's memories, view recent memories
- **Export/Import**: export memories, import memories
- **Auto Memory**: enable memory auto retrieve, disable memory auto retrieve

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
