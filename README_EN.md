# Skillix Hub

Cursor Skills Repository - A collection of tools to enhance AI programming efficiency.

## What is Cursor Skill?

Cursor Skill is a reusable AI instruction set that helps Cursor AI better complete specific tasks. Each Skill includes:
- Task description and trigger conditions
- Execution scripts and tools
- Usage examples

## Available Skills

| Skill | Description |
|-------|-------------|
| [memory](./skills/memory/) | Long-term memory for Cursor, auto-record conversations and retrieve relevant history |
| [swagger-api-reader](./skills/swagger-api-reader/) | Read and cache Swagger/OpenAPI docs with browser auth support |

## Installation

### Method 1: Global Installation (Available for all projects)

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

### Method 2: Project Installation (Available for current project only)

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

Memory Skill provides long-term memory capability for Cursor with zero external dependencies.

### Core Features

- **Auto Retrieval**: Automatically retrieve relevant history based on user questions
- **Smart Saving**: Automatically judge conversation value and save important content
- **Keyword Matching**: Retrieval algorithm based on keywords + time decay
- **View Memories**: View today's/specific date/recent memories
- **Delete Memories**: Delete specific memories or clear all
- **Export/Import**: Backup and restore memory data

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
```

### Trigger Words

- **Retrieval Triggers**: continue, last time, before, yesterday, we discussed
- **Save Triggers**: remember this, save this
- **Skip Save**: don't save, skip saving
- **View Memories**: view today's memories, view recent memories
- **Export/Import**: export memories, import memories

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
