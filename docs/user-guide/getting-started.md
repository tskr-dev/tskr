# Getting Started with Tskr

Welcome to Tskr! This guide will help you get up and running with the clean, developer-friendly task management CLI.

## 📦 Installation

### Option 1: Install from PyPI (Recommended)

```bash
pip install tskr
```

### Option 2: Install from Source

```bash
git clone https://github.com/tskr-dev/tskr.git
cd tskr
pip install -e .
```

### Option 3: Download Binary

Download pre-built binaries from our [releases page](https://github.com/tskr-dev/tskr/releases):

- **Linux**: `tskr-linux`
- **macOS**: `tskr-macos`
- **Windows**: `tskr-windows.exe`

## ✅ Verify Installation

```bash
tskr --help
```

You should see the main help message with available commands.

## 🚀 First Steps

### 1. Initialize Your First Project

Navigate to your project directory and initialize Tskr:

```bash
cd your-project
tskr init .
```

This creates a `.tskr/` directory with:

- `project.json` - Project metadata
- `tasks.jsonl` - Task storage
- `events.log` - Event history
- `config.json` - User preferences

### 2. Add Your First Task

```bash
tskr add "Set up project documentation" --priority H
```

### 3. List Your Tasks

```bash
tskr ls
```

You should see your first task listed with its ID, title, and priority.

### 4. Claim and Work on a Task

```bash
# Claim the task (use the actual task ID from ls command)
tskr claim abc12345

# Check your current task
tskr current
```

### 5. Complete the Task

```bash
tskr done abc12345
```

### 6. View Project Status

```bash
tskr status
```

## 🎯 Basic Workflow

Here's the typical Tskr workflow:

```bash
# 1. Add tasks to your backlog
tskr add "Fix login bug" --priority H --tag bug
tskr add "Write API documentation" --due friday --tag docs
tskr add "Review PR #123" --review

# 2. View and filter tasks
tskr ls                           # All tasks
tskr ls --status backlog         # Only backlog tasks
tskr ls --priority H             # High priority tasks
tskr ls --tag bug                # Bug-related tasks

# 3. Claim a task to work on
tskr claim abc12345

# 4. Add progress updates
tskr comment abc12345 "Fixed the validation logic"

# 5. Complete the task
tskr done abc12345

# 6. Monitor progress
tskr status                      # Project dashboard
tskr events                      # Recent activity
```

## 🏷️ Understanding Task Properties

Every task has these properties:

- **ID**: Unique identifier (8-character short ID for display)
- **Title**: Brief description of the task
- **Status**: `backlog`, `pending`, `completed`, `archived`
- **Priority**: `H` (High), `M` (Medium), `L` (Low), or none
- **Tags**: Flexible labels for categorization
- **Due Date**: Optional deadline
- **Description**: Detailed information
- **Claimed By**: Who's working on it
- **Discussion**: Comments and updates

## 🔧 Configuration

### Global Settings

```bash
# Set your default author name
tskr config set default_author "Your Name"

# Configure display preferences
tskr config set show_tags_in_list true
tskr config set max_description_length 60
```

### Project Settings

Edit `.tskr/config.json` in your project:

```json
{
  "default_author": "Your Name",
  "auto_tags": {
    "bug": ["urgent", "bug"],
    "feature": ["feature"],
    "meeting": ["meeting"]
  }
}
```

## 🤝 Team Collaboration

Tskr works great with teams:

### Git Integration

```bash
# Commit your task changes
git add .tskr/
git commit -m "Add new feature tasks"
git push
```

### Claiming Tasks

```bash
# See who's working on what
tskr ls --status pending

# Claim available tasks
tskr ls --status backlog
tskr claim def67890
```

### Communication

```bash
# Add comments to tasks
tskr comment abc12345 "Need help with the database schema"

# View task discussions
tskr show abc12345
```

## 🎨 Customization

### Auto-tagging

Use command flags for automatic tagging:

```bash
tskr add "Memory leak in parser" --bug      # Adds: urgent, bug
tskr add "User dashboard" --feature         # Adds: feature
tskr add "Team standup" --meeting          # Adds: meeting
tskr add "Review PR #456" --review         # Adds: review, code
```

### Natural Language Dates

```bash
tskr add "Deploy to production" --due tomorrow
tskr add "Team meeting" --due friday
tskr add "Quarterly review" --due "2024-03-15"
tskr add "Sprint planning" --due "next monday"
```

## 🔍 Finding Tasks

### Filtering

```bash
# By status
tskr ls --status backlog
tskr ls --status pending
tskr ls --status completed

# By priority
tskr ls --priority H

# By tags
tskr ls --tag bug
tskr ls --tag urgent --tag bug    # Multiple tags (AND)

# By assignee
tskr ls --claimed-by "alice"
tskr ls --unclaimed              # Available tasks

# By due date
tskr ls --due-before "2024-01-15"
tskr ls --due-after "2024-01-01"
```

### Searching

```bash
# Search in title and description
tskr ls --search "authentication"
tskr ls --search "bug" --priority H
```

### Sorting

```bash
# By urgency (default)
tskr ls

# By due date
tskr ls --sort due

# By priority
tskr ls --sort priority

# By creation date
tskr ls --sort created
```

## 📊 Monitoring Progress

### Dashboard

```bash
tskr status
```

Shows:

- Task counts by status
- Overdue tasks
- Due today/this week
- Team activity
- Hot tasks (high urgency)

### Event Log

```bash
tskr events
tskr events --limit 50
```

Shows recent activity:

- Task creation/completion
- Claims and assignments
- Comments and updates

## 🆘 Getting Help

### Command Help

```bash
tskr --help                    # Main help
tskr add --help               # Command-specific help
tskr ls --help                # List command options
```

### Task Details

```bash
tskr show abc12345            # Full task information
```

### Troubleshooting

Common issues:

1. **"Not in a project"** → Run `tskr init .` first
2. **"Task not found"** → Check task ID with `tskr ls`
3. **Permission errors** → Check file permissions on `.tskr/` directory

## 🎉 Next Steps

Now that you're set up:

1. **Explore [Basic Usage](basic-usage.md)** for detailed command reference
2. **Learn [Advanced Features](advanced-features.md)** for power user tips
3. **Set up [Team Collaboration](team-collaboration.md)** if working with others
4. **Check out [LLM Integration](llm-integration.md)** for AI assistant workflows

---

## Ready to boost your productivity? Start adding tasks and get organized! 🚀
