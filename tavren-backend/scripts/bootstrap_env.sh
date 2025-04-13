#!/bin/bash

# Bootstrap Environment for Tavren
# This script creates environment files for different deployment environments
# Usage: ./scripts/bootstrap_env.sh [development|staging|production]

# Terminal colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default mode
MODE=${1:-"development"}
VALID_MODES=("development" "staging" "production")

# Validate mode
if [[ ! " ${VALID_MODES[@]} " =~ " ${MODE} " ]]; then
    echo -e "${RED}Invalid mode: $MODE${NC}"
    echo "Usage: $0 [development|staging|production]"
    exit 1
fi

echo -e "${BLUE}Bootstrapping environment for ${MODE} deployment...${NC}"

# File to create
case $MODE in
    development)
        ENV_FILE=".env.development"
        ;;
    staging)
        ENV_FILE=".env.staging"
        ;;
    production)
        ENV_FILE=".env.production"
        ;;
esac

# Check if file already exists
if [ -f "$ENV_FILE" ]; then
    echo -e "${YELLOW}Warning: $ENV_FILE already exists.${NC}"
    read -p "Do you want to overwrite it? (y/n): " OVERWRITE
    if [[ "$OVERWRITE" != "y" && "$OVERWRITE" != "Y" ]]; then
        echo "Aborting."
        exit 0
    fi
fi

# Generate random secrets
JWT_SECRET=$(openssl rand -hex 32)
DATA_ENC_KEY=$(openssl rand -hex 16)
ADMIN_API_KEY=$(openssl rand -hex 24)
POSTGRES_USER="tavren_user"
POSTGRES_PASSWORD=$(openssl rand -base64 18 | tr -d '+/=' | cut -c1-16)
REDIS_PASSWORD=$(openssl rand -base64 18 | tr -d '+/=' | cut -c1-16)

# Create environment file with appropriate variables
echo -e "${BLUE}Creating $ENV_FILE...${NC}"

# Start with a header
cat > "$ENV_FILE" << EOF
# Tavren Environment Configuration for ${MODE^} Environment
# Generated on $(date)
# DO NOT COMMIT THIS FILE TO VERSION CONTROL

EOF

# Add environment-specific variables
case $MODE in
    development)
        cat >> "$ENV_FILE" << EOF
# Database connection (SQLite for development)
DATABASE_URL=sqlite+aiosqlite:///./tavren_dev.db

# Security settings
JWT_SECRET_KEY=$JWT_SECRET
DATA_ENCRYPTION_KEY=$DATA_ENC_KEY
ADMIN_API_KEY=$ADMIN_API_KEY
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Application settings
LOG_LEVEL=DEBUG
MINIMUM_PAYOUT_THRESHOLD=5.00
AUTO_PAYOUT_MIN_TRUST_SCORE=50.0
AUTO_PAYOUT_MAX_AMOUNT=100.0

# Environment indicator
ENVIRONMENT=development
EOF
        ;;
    staging)
        cat >> "$ENV_FILE" << EOF
# Database connection (PostgreSQL for staging)
# Update host and credentials for your staging database
DATABASE_URL=postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@localhost:5432/tavren_staging

# Security settings
JWT_SECRET_KEY=$JWT_SECRET
DATA_ENCRYPTION_KEY=$DATA_ENC_KEY
ADMIN_API_KEY=$ADMIN_API_KEY
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Docker PostgreSQL configuration
POSTGRES_USER_SECRET=${POSTGRES_USER}
POSTGRES_PASSWORD_SECRET=${POSTGRES_PASSWORD}

# Redis configuration (if used)
REDIS_PASSWORD=${REDIS_PASSWORD}
REDIS_URL=redis://:${REDIS_PASSWORD}@localhost:6379/0

# Application settings
LOG_LEVEL=INFO
MINIMUM_PAYOUT_THRESHOLD=5.00
AUTO_PAYOUT_MIN_TRUST_SCORE=50.0
AUTO_PAYOUT_MAX_AMOUNT=100.0

# Environment indicator
ENVIRONMENT=staging
EOF
        ;;
    production)
        cat >> "$ENV_FILE" << EOF
# Database connection (PostgreSQL for production)
# Update host and credentials for your production database
DATABASE_URL=postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@localhost:5432/tavren_production

# Security settings
JWT_SECRET_KEY=$JWT_SECRET
DATA_ENCRYPTION_KEY=$DATA_ENC_KEY
ADMIN_API_KEY=$ADMIN_API_KEY
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Docker PostgreSQL configuration
POSTGRES_USER_SECRET=${POSTGRES_USER}
POSTGRES_PASSWORD_SECRET=${POSTGRES_PASSWORD}

# Redis configuration (if used)
REDIS_PASSWORD=${REDIS_PASSWORD}
REDIS_URL=redis://:${REDIS_PASSWORD}@localhost:6379/0

# Application settings
LOG_LEVEL=WARNING
MINIMUM_PAYOUT_THRESHOLD=5.00
AUTO_PAYOUT_MIN_TRUST_SCORE=50.0
AUTO_PAYOUT_MAX_AMOUNT=100.0

# Environment indicator
ENVIRONMENT=production
EOF
        ;;
esac

# Add instructions
cat >> "$ENV_FILE" << EOF

# NVIDIA API settings (if needed)
# NVIDIA_API_KEY=your_nvidia_api_key
# NVIDIA_API_BASE_URL=https://api.nvidia.com/v1
# DEFAULT_LLM_MODEL=llama3-70b-instruct
# DEFAULT_EMBEDDING_MODEL=nvidia/embedding-model
EOF

# Make sure permissions are correct
chmod 600 "$ENV_FILE"

echo -e "${GREEN}Successfully created $ENV_FILE with secure values.${NC}"

# Generate verification command based on platform
if [ $(uname) == "Darwin" ] || [ $(uname) == "Linux" ]; then
    echo -e "${YELLOW}Verify file permissions (should be 600):${NC}"
    ls -l "$ENV_FILE"
fi

# Validate the environment file
echo -e "\n${BLUE}Validating the generated environment file...${NC}"
if command -v python3 &> /dev/null; then
    python3 ./scripts/validate_env.py --env-file "$ENV_FILE" --mode "$MODE"
else
    echo -e "${YELLOW}Python not found, skipping validation.${NC}"
    echo "To validate manually, run: python3 ./scripts/validate_env.py --env-file $ENV_FILE --mode $MODE"
fi

echo -e "\n${BLUE}Next steps:${NC}"
echo "1. Review the generated environment file: $ENV_FILE"
echo "2. Create a symlink to use this file: ln -sf $ENV_FILE .env"
echo "3. Start the application with this environment"

exit 0 