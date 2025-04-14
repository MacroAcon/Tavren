#!/bin/bash

# Linux Setup Script for Tavren Backend
# This script makes all shell scripts executable and installs git hooks
# Run this script after cloning the repository on a Linux/macOS system

# Terminal colors
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Setting up Tavren backend for Linux/macOS environment...${NC}"

# Check if we're in the correct directory structure
if [ ! -d "scripts" ]; then
    if [ -d "tavren-backend/scripts" ]; then
        cd tavren-backend
    else
        echo -e "${RED}Error: Cannot find scripts directory.${NC}"
        echo "Make sure you run this script from the project root or tavren-backend directory."
        exit 1
    fi
fi

# Make all shell scripts executable
echo -e "${YELLOW}Making shell scripts executable...${NC}"
find scripts -name "*.sh" -exec chmod +x {} \;
chmod +x scripts/pre-commit

# Install git hooks
echo -e "${YELLOW}Installing git hooks...${NC}"
if [ -d "../.git" ]; then
    # We're in the tavren-backend directory and the git repo is one level up
    cp scripts/pre-commit ../.git/hooks/
    chmod +x ../.git/hooks/pre-commit
    echo -e "${GREEN}Installed pre-commit hook to ../.git/hooks/${NC}"
elif [ -d ".git" ]; then
    # The git repo is in the current directory
    cp scripts/pre-commit .git/hooks/
    chmod +x .git/hooks/pre-commit
    echo -e "${GREEN}Installed pre-commit hook to .git/hooks/${NC}"
else
    echo -e "${RED}Warning: Could not locate .git directory to install hooks.${NC}"
    echo "You can manually install the pre-commit hook with:"
    echo "  cp scripts/pre-commit /path/to/your/.git/hooks/"
    echo "  chmod +x /path/to/your/.git/hooks/pre-commit"
fi

echo -e "${GREEN}Setup complete!${NC}"
echo "You can now run the following scripts:"
find scripts -name "*.sh" | sort 