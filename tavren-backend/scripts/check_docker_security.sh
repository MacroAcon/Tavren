#!/bin/bash

# Security check script for Docker Compose configuration
# This script checks for common security issues in the Docker Compose setup
# Usage: ./scripts/check_docker_security.sh

# Terminal colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo "Running Docker Compose security checks..."
echo "----------------------------------------"

DOCKER_COMPOSE_FILE="../docker-compose.yml"
ENV_DOCKER_FILE="../.env.docker"

# Check if we're in the correct directory
if [ ! -f "$DOCKER_COMPOSE_FILE" ]; then
    DOCKER_COMPOSE_FILE="docker-compose.yml"
    ENV_DOCKER_FILE=".env.docker"
    
    if [ ! -f "$DOCKER_COMPOSE_FILE" ]; then
        echo -e "${RED}Error: Cannot find docker-compose.yml file.${NC}"
        echo "Make sure you run this script from the project root or scripts directory."
        exit 1
    fi
fi

# Check 1: Default credentials in docker-compose.yml
CREDENTIAL_CHECK=$(grep -E "tavren_(user|password)" "$DOCKER_COMPOSE_FILE")
if [ -n "$CREDENTIAL_CHECK" ]; then
    echo -e "${RED}FAILED: Default credentials found in docker-compose.yml${NC}"
    echo "The following lines contain default credentials:"
    echo "$CREDENTIAL_CHECK"
    echo -e "${YELLOW}Fix: Use environment variables from .env.docker instead${NC}"
    HAS_ERRORS=1
else
    echo -e "${GREEN}PASSED: No default credentials found in docker-compose.yml${NC}"
fi

# Check 2: Redis password
REDIS_PASSWORD_CHECK=$(grep -E "requirepass.*tavren_redis_password" "$DOCKER_COMPOSE_FILE")
if [ -n "$REDIS_PASSWORD_CHECK" ]; then
    echo -e "${RED}FAILED: Default Redis password found in docker-compose.yml${NC}"
    echo "$REDIS_PASSWORD_CHECK"
    echo -e "${YELLOW}Fix: Use \${REDIS_PASSWORD} variable without default${NC}"
    HAS_ERRORS=1
else
    echo -e "${GREEN}PASSED: No default Redis password found${NC}"
fi

# Check 3: .env.docker file with placeholders
if [ -f "$ENV_DOCKER_FILE" ]; then
    PLACEHOLDER_CHECK=$(grep -c "PLACEHOLDER_REPLACE" "$ENV_DOCKER_FILE")
    if [ "$PLACEHOLDER_CHECK" -gt 0 ]; then
        echo -e "${RED}WARNING: .env.docker still contains placeholders${NC}"
        echo "Found $PLACEHOLDER_CHECK placeholder values that need to be replaced with real secrets."
        echo -e "${YELLOW}Fix: Generate secure random values and replace the placeholders${NC}"
        HAS_WARNINGS=1
    else
        echo -e "${GREEN}PASSED: .env.docker has no obvious placeholders${NC}"
    fi
else
    echo -e "${YELLOW}WARNING: .env.docker file not found${NC}"
    echo "Create an .env.docker file from the template for production deployments."
    HAS_WARNINGS=1
fi

# Final assessment
echo "----------------------------------------"
if [ "$HAS_ERRORS" == "1" ]; then
    echo -e "${RED}Security check failed with errors.${NC}"
    echo "Please fix the issues above before deploying."
    exit 1
elif [ "$HAS_WARNINGS" == "1" ]; then
    echo -e "${YELLOW}Security check passed with warnings.${NC}"
    echo "Consider addressing the warnings before production deployment."
    exit 0
else
    echo -e "${GREEN}All security checks passed!${NC}"
    exit 0
fi 