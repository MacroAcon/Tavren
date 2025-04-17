# Development Environment Setup

This document outlines the standard practices for setting up and maintaining development environments for the Tavren project.

## Virtual Environment Conventions

### `.venv` is the Standard Virtual Environment Directory

Tavren standardizes on using `.venv` (with the leading dot) as the virtual environment directory name. This convention offers several advantages:

- The leading dot (`.`) makes it a hidden directory in Unix-like systems, reducing clutter in directory listings
- It's automatically recognized by common Python tools like VS Code, PyCharm, and Poetry
- It's clearly distinguished as a non-project directory that contains generated files
- It helps prevent accidental inclusion in packages or source control

**Do not** create or use alternative virtual environment directories like `venv`, `env`, or similar names to avoid confusion and disk space waste.

### Creating the Standard Virtual Environment

```bash
# Create the virtual environment
python -m venv .venv

# Activate on Windows
.\.venv\Scripts\activate

# Activate on macOS/Linux
source .venv/bin/activate
```

### Virtual Environment in Git

The `.venv` directory is excluded from Git via the `.gitignore` file. Never commit virtual environment directories to the repository as they:

- Are large (often >1GB)
- Contain platform-specific binaries
- Can be regenerated from requirements files
- Slow down Git operations

## Requirements Management

### Requirements Files

The `requirements.txt` file in the `tavren-backend` directory contains all dependencies needed to run the backend. This file should:

- Include precise version numbers (e.g., `fastapi==0.68.0`)
- Be updated whenever new dependencies are added to the project
- Be reviewed periodically to remove unused dependencies

### Updating Requirements

When installing new packages:

```bash
# Activate the virtual environment
source .venv/bin/activate

# Install the package
pip install new-package

# Update requirements.txt
pip freeze > requirements.txt
```

When working on specific features, consider creating `requirements-dev.txt` or similar for development-only dependencies.

### Validating Requirements

Before deployment, validate that the requirements file includes all necessary dependencies:

```bash
# Create a fresh test environment
python -m venv .venv-test
source .venv-test/bin/activate
pip install -r requirements.txt

# Test that the application runs with only these dependencies
python -m app.main
```

## Disk Space Management

To avoid accumulating unnecessary disk usage:

- Delete unused virtual environments (anything not named `.venv`)
- Clear cached Python files (`__pycache__` directories) when troubleshooting import issues
- Avoid committing large data files; use `.gitattributes` for Git LFS if necessary
- Regularly review the repository size with tools like `du -h --max-depth=1`

## IDE Configuration

The project includes configurations for common IDEs that automatically recognize the `.venv` directory:

- VS Code: `.vscode/settings.json` automatically uses `.venv` for Python interpreter
- PyCharm: `.idea/misc.xml` references the `.venv` Python interpreter

Always use the IDE's built-in virtual environment selection to ensure consistent execution environments. 