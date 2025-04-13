#!/bin/bash

# Install Git hooks for repository security
# This script installs the pre-commit hook to prevent credential leakage
# Usage: ./scripts/install_git_hooks.sh

# Terminal colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Installing Git hooks for Tavren security...${NC}"

# Find Git root directory
GIT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null)
if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Not in a Git repository.${NC}"
    echo "Please run this script within a Git repository."
    exit 1
fi

# Create hooks directory if it doesn't exist
HOOKS_DIR="$GIT_ROOT/.git/hooks"
if [ ! -d "$HOOKS_DIR" ]; then
    echo -e "${YELLOW}Creating hooks directory: $HOOKS_DIR${NC}"
    mkdir -p "$HOOKS_DIR"
fi

# Install pre-commit hook
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")
PRE_COMMIT_SRC="$SCRIPT_DIR/pre-commit"
PRE_COMMIT_DEST="$HOOKS_DIR/pre-commit"

if [ ! -f "$PRE_COMMIT_SRC" ]; then
    echo -e "${RED}Error: Could not find pre-commit hook at $PRE_COMMIT_SRC${NC}"
    echo "Make sure you run this script from the repository root or scripts directory."
    exit 1
fi

# Copy the hook
cp "$PRE_COMMIT_SRC" "$PRE_COMMIT_DEST"

# Make the hook executable
chmod +x "$PRE_COMMIT_DEST"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}Successfully installed pre-commit hook!${NC}"
    echo -e "The hook will check for credentials before each commit."
    echo -e "${YELLOW}Note:${NC} This hook can be bypassed with git commit --no-verify"
    echo -e "       Only use this if you're absolutely certain no credentials are being committed."
else
    echo -e "${RED}Failed to install pre-commit hook.${NC}"
    echo "Please check permissions and try again."
    exit 1
fi

# Optional: Additional hooks
echo ""
echo -e "${YELLOW}Would you like to enable additional security features?${NC}"
echo "1. Git attributes to detect large files (y/n)? "
read ADD_ATTRIBUTES

if [[ "$ADD_ATTRIBUTES" == "y" || "$ADD_ATTRIBUTES" == "Y" ]]; then
    # Add Git attributes for binary/large file detection
    ATTRIBUTES_FILE="$GIT_ROOT/.gitattributes"
    if [ ! -f "$ATTRIBUTES_FILE" ]; then
        cat > "$ATTRIBUTES_FILE" << EOF
# Git attributes for security
*.zip diff=zip
*.pdf diff=pdf
*.jpg diff=exif
*.png diff=exif
*.docx diff=word
*.xlsx diff=excel
*.pptx diff=pptx

# Treat these files as binary to avoid diff showing content
*.env binary
*.key binary
*.pem binary
EOF
        echo -e "${GREEN}Created .gitattributes file for improved binary file handling.${NC}"
    else
        echo -e "${YELLOW}Existing .gitattributes file found. Skipping.${NC}"
    fi
fi

echo ""
echo -e "${GREEN}Git security hooks installation complete!${NC}"
echo "Next steps:"
echo "1. Check your local .env files to ensure they are in .gitignore"
echo "2. Run ./scripts/scan_for_credentials.sh to check existing codebase"
echo "3. Consider setting up server-side hooks for additional protection"
exit 0 