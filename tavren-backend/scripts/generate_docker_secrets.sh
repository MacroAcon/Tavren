#!/bin/bash

# Generate secure random values for Docker deployment
# This script creates a secure .env.docker file with random values
# Usage: ./scripts/generate_docker_secrets.sh

# Terminal colors
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo "Generating secure Docker environment values..."
TEMPLATE_FILE=".env.docker"
OUTPUT_FILE=".env.docker.generated"

# Check if we're in the correct directory
if [ ! -f "$TEMPLATE_FILE" ]; then
    cd ..
    if [ ! -f "$TEMPLATE_FILE" ]; then
        echo "Error: Cannot find .env.docker template file."
        echo "Make sure you run this script from the project root or scripts directory."
        exit 1
    fi
fi

# Check if OpenSSL is available
if ! command -v openssl &> /dev/null; then
    echo "Error: OpenSSL is required but not installed."
    echo "Please install OpenSSL to generate secure random values."
    exit 1
fi

# Generate secure values
DB_USER="tavren_user_$(openssl rand -hex 4)"
DB_PASSWORD=$(openssl rand -base64 24 | tr -d '+/=' | cut -c1-20)
REDIS_PASSWORD=$(openssl rand -base64 24 | tr -d '+/=' | cut -c1-20)
JWT_SECRET=$(openssl rand -hex 32)
DATA_ENC_KEY=$(openssl rand -hex 16)
ADMIN_API_KEY=$(openssl rand -hex 24)

# Create a copy of the template with secure values
cp "$TEMPLATE_FILE" "$OUTPUT_FILE"

# Replace placeholders with secure values
sed -i.bak "s/secure_db_username/$DB_USER/g" "$OUTPUT_FILE"
sed -i.bak "s/PLACEHOLDER_REPLACE_WITH_SECURE_PASSWORD/$DB_PASSWORD/g" "$OUTPUT_FILE"
sed -i.bak "s/PLACEHOLDER_REPLACE_WITH_SECURE_PASSWORD/$REDIS_PASSWORD/g" "$OUTPUT_FILE"
sed -i.bak "s/PLACEHOLDER_REPLACE_WITH_SECURE_KEY/$JWT_SECRET/g" "$OUTPUT_FILE"
sed -i.bak "s/PLACEHOLDER_REPLACE_WITH_SECURE_KEY/$DATA_ENC_KEY/g" "$OUTPUT_FILE"
sed -i.bak "s/PLACEHOLDER_REPLACE_WITH_SECURE_KEY/$ADMIN_API_KEY/g" "$OUTPUT_FILE"

# Clean up backup file
rm -f "$OUTPUT_FILE.bak"

echo -e "${GREEN}Success!${NC} Secure environment file created as $OUTPUT_FILE"
echo -e "${YELLOW}IMPORTANT:${NC} Review the generated file and rename it to .env.docker before deployment."
echo "To use these values:"
echo "1. Review the generated file"
echo "2. Move it to your production environment"
echo "3. Rename: mv $OUTPUT_FILE .env.docker"
echo "4. Run docker-compose with: docker-compose --env-file .env.docker up -d" 