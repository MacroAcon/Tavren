#!/bin/bash

# Credential scanner for Tavren repository
# Scans codebase for potential hardcoded credentials, API keys, and secrets
# Usage: ./scripts/scan_for_credentials.sh [path]

# Terminal colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Path to scan (default: current directory)
SCAN_PATH=${1:-.}

# Patterns to search for
PATTERNS=(
  # API Keys and tokens
  "api[_-]key[[:space:]]*=[[:space:]]*['\"][a-zA-Z0-9_\.\-]{16,}['\"]"
  "api[_-]secret[[:space:]]*=[[:space:]]*['\"][a-zA-Z0-9_\.\-]{16,}['\"]"
  "token[[:space:]]*=[[:space:]]*['\"][a-zA-Z0-9_\.\-]{16,}['\"]"
  "secret[[:space:]]*=[[:space:]]*['\"][a-zA-Z0-9_\.\-]{16,}['\"]"
  
  # AWS patterns
  "AKIA[0-9A-Z]{16}"
  "[a-zA-Z0-9/+]{40,}"
  
  # Database connection strings
  "postgres(ql)?://[a-zA-Z0-9_\.\-]+:[a-zA-Z0-9_\.\-]+@"
  "mysql://[a-zA-Z0-9_\.\-]+:[a-zA-Z0-9_\.\-]+@"
  "mongodb://[a-zA-Z0-9_\.\-]+:[a-zA-Z0-9_\.\-]+@"
  
  # Password patterns
  "password[[:space:]]*=[[:space:]]*['\"][^'\"]+['\"]"
  "passwd[[:space:]]*=[[:space:]]*['\"][^'\"]+['\"]"
  "pwd[[:space:]]*=[[:space:]]*['\"][^'\"]+['\"]"
  
  # Private keys
  "BEGIN (RSA|DSA|EC|OPENSSH) PRIVATE KEY"
  
  # OAuth patterns
  "oauth[_-]token[[:space:]]*=[[:space:]]*['\"][a-zA-Z0-9_\.\-]{16,}['\"]"
)

# Files to exclude from scanning
EXCLUDE=(
  ".git"
  "node_modules"
  "venv"
  "*.pyc"
  "*.bak"
  "*~"
  "*.md"
  "*.json.dist"
  "*.min.js"
  "*.min.css"
  "yarn.lock"
  "package-lock.json"
  ".env.example"
  ".env.docker"
  "tests/"
  "coverage/"
  "dist/"
  "__pycache__"
)

# Build the exclude pattern for grep
EXCLUDE_PATTERN=""
for pattern in "${EXCLUDE[@]}"; do
  EXCLUDE_PATTERN="${EXCLUDE_PATTERN} --exclude-dir=${pattern}"
done

# Store found issues
TOTAL_FINDINGS=0
FINDINGS=()

echo -e "${BLUE}Scanning repository for potential credentials...${NC}"
echo "Path: $SCAN_PATH"
echo "----------------------------------------"

# Check ignored files
echo -e "${YELLOW}Checking .gitignore for important exclusions...${NC}"
GIT_IGNORES=()
if [ -f "$SCAN_PATH/.gitignore" ]; then
  for required in ".env" ".env.*" "*.pem" "*.key"; do
    if ! grep -q "$required" "$SCAN_PATH/.gitignore"; then
      GIT_IGNORES+=("$required")
    fi
  done
fi

if [ ${#GIT_IGNORES[@]} -gt 0 ]; then
  echo -e "${RED}WARNING: These patterns should be in .gitignore:${NC}"
  for pattern in "${GIT_IGNORES[@]}"; do
    echo "  - $pattern"
  done
  echo ""
else
  echo -e "${GREEN}✓ .gitignore contains necessary exclusions${NC}"
  echo ""
fi

# Scan for each pattern
for pattern in "${PATTERNS[@]}"; do
  echo -e "${BLUE}Searching for: ${pattern}${NC}"
  
  # Find files matching the pattern, excluding specified directories
  RESULTS=$(grep -rn --include="*.*" $EXCLUDE_PATTERN -E "$pattern" "$SCAN_PATH" 2>/dev/null)
  
  if [ -n "$RESULTS" ]; then
    FINDING_COUNT=$(echo "$RESULTS" | wc -l)
    TOTAL_FINDINGS=$((TOTAL_FINDINGS + FINDING_COUNT))
    
    echo -e "${RED}Found $FINDING_COUNT potential credential(s):${NC}"
    echo "$RESULTS" | head -5  # Show only first 5 results to avoid flooding terminal
    
    if [ "$FINDING_COUNT" -gt 5 ]; then
      echo -e "${YELLOW}...and $((FINDING_COUNT - 5)) more matches. Run grep directly to see all.${NC}"
    fi
    
    FINDINGS+=("$pattern")
    echo ""
  else
    echo -e "${GREEN}✓ No matches found${NC}"
    echo ""
  fi
done

# Summary
echo "----------------------------------------"
if [ $TOTAL_FINDINGS -gt 0 ]; then
  echo -e "${RED}SECURITY RISK: Found $TOTAL_FINDINGS potential credential(s) in codebase${NC}"
  echo -e "${YELLOW}Patterns that matched:${NC}"
  for finding in "${FINDINGS[@]}"; do
    echo "  - $finding"
  done
  echo ""
  echo -e "${YELLOW}Recommendations:${NC}"
  echo "1. Move credentials to environment variables"
  echo "2. Replace hardcoded values with references to environment variables"
  echo "3. Check commit history and consider purging sensitive data with git-filter-branch"
  echo "4. For test credentials, use obviously fake values (e.g., 'test_api_key_123')"
  exit 1
else
  echo -e "${GREEN}No potential credentials found in codebase!${NC}"
  echo "Keep maintaining good security practices:"
  echo "- Use environment variables for all secrets"
  echo "- Never commit .env files to version control"
  echo "- Regularly rotate production credentials"
  exit 0
fi 