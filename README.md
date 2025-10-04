# TSKR

pronounced "tasker".

The CLI task manager for your AI coding agent.

## 📦 Installation

### macOS
```bash
# Create local bin directory if it doesn't exist
mkdir -p ~/.local/bin

# Download and install
curl -sSL https://github.com/tskr-dev/tskr/releases/download/v0.0.2/tskr-macos -o ~/.local/bin/tskr && chmod +x ~/.local/bin/tskr

# Add to PATH (add this to your ~/.zshrc or ~/.bash_profile)
export PATH="$HOME/.local/bin:$PATH"
```

### Linux
```bash
# Create local bin directory if it doesn't exist
mkdir -p ~/.local/bin

# Download and install
curl -sSL https://github.com/tskr-dev/tskr/releases/download/v0.0.2/tskr-linux -o ~/.local/bin/tskr && chmod +x ~/.local/bin/tskr

# Add to PATH (add this to your ~/.bashrc or ~/.zshrc)
export PATH="$HOME/.local/bin:$PATH"
```

## ✅ Verify Installation

```bash
tskr --help
```

## 🚀 Quick Start

```bash
# Initialize a project
tskr init .

# Add your first task
tskr add "Set up project documentation" --priority H

# List tasks
tskr ls

# Get help
tskr --help
```

## 📚 Documentation

For complete documentation, visit [docs/README.md](docs/README.md) or check out:

- [Getting Started Guide](docs/user-guide/getting-started.md)
- [Command Reference](docs/user-guide/basic-usage.md)
- [Advanced Features](docs/user-guide/advanced-features.md)

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and contribution guidelines.
