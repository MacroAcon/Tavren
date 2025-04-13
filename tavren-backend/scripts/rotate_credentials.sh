#!/bin/bash

# Credential Rotation Script for Tavren
# Automatically rotates secrets and credentials for better security
# Usage: ./scripts/rotate_credentials.sh [--env-file .env.production] [--key JWT_SECRET_KEY]

# Terminal colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
ENV_FILE=".env"
BACKUP_DIR="./secrets/backups"
ROTATE_ALL=false
KEY_TO_ROTATE=""
DRY_RUN=false

# Process command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --env-file)
            ENV_FILE="$2"
            shift 2
            ;;
        --key)
            KEY_TO_ROTATE="$2"
            shift 2
            ;;
        --all)
            ROTATE_ALL=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  --env-file FILE    Specify the environment file to update (default: .env)"
            echo "  --key KEY          Specify a single key to rotate (e.g., JWT_SECRET_KEY)"
            echo "  --all              Rotate all secrets"
            echo "  --dry-run          Run without making changes (simulation mode)"
            echo "  --help             Show this help message"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Check if env file exists
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}Error: Environment file not found: $ENV_FILE${NC}"
    echo "Please specify a valid environment file using --env-file"
    exit 1
fi

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Create a backup of the current env file
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/$(basename ${ENV_FILE}).${TIMESTAMP}.bak"
cp "$ENV_FILE" "$BACKUP_FILE"
echo -e "${GREEN}Created backup: $BACKUP_FILE${NC}"

# Define the keys that can be rotated
ROTATABLE_KEYS=(
    "JWT_SECRET_KEY"
    "DATA_ENCRYPTION_KEY"
    "ADMIN_API_KEY"
    "REDIS_PASSWORD"
    "POSTGRES_PASSWORD_SECRET"
)

# Function to generate a new value for a key
generate_value() {
    local key=$1
    
    case $key in
        JWT_SECRET_KEY)
            echo $(openssl rand -hex 32)
            ;;
        DATA_ENCRYPTION_KEY)
            echo $(openssl rand -hex 16)
            ;;
        ADMIN_API_KEY)
            echo $(openssl rand -hex 24)
            ;;
        REDIS_PASSWORD|POSTGRES_PASSWORD_SECRET)
            echo $(openssl rand -base64 18 | tr -d '+/=' | cut -c1-16)
            ;;
        *)
            echo ""
            ;;
    esac
}

# Function to update a key in the env file
update_key() {
    local key=$1
    local new_value=$2
    local env_file=$3
    
    # Check if key exists in the file
    if grep -q "^${key}=" "$env_file"; then
        if [ "$DRY_RUN" = true ]; then
            echo -e "${YELLOW}Would update $key to new value in $env_file${NC}"
        else
            # Create a temporary file
            local temp_file=$(mktemp)
            
            # Replace the value in the temp file
            sed "s|^${key}=.*|${key}=${new_value}|" "$env_file" > "$temp_file"
            
            # Replace the original file
            mv "$temp_file" "$env_file"
            echo -e "${GREEN}Updated $key in $env_file${NC}"
        fi
    else
        echo -e "${YELLOW}Key $key not found in $env_file${NC}"
    fi
}

# Main rotation logic
if [ "$ROTATE_ALL" = true ]; then
    echo -e "${BLUE}Rotating all rotatable secrets...${NC}"
    for key in "${ROTATABLE_KEYS[@]}"; do
        new_value=$(generate_value "$key")
        if [ -n "$new_value" ]; then
            update_key "$key" "$new_value" "$ENV_FILE"
        fi
    done
elif [ -n "$KEY_TO_ROTATE" ]; then
    # Check if the key is rotatable
    if [[ " ${ROTATABLE_KEYS[*]} " =~ " ${KEY_TO_ROTATE} " ]]; then
        echo -e "${BLUE}Rotating $KEY_TO_ROTATE...${NC}"
        new_value=$(generate_value "$KEY_TO_ROTATE")
        if [ -n "$new_value" ]; then
            update_key "$KEY_TO_ROTATE" "$new_value" "$ENV_FILE"
        else
            echo -e "${RED}Could not generate value for $KEY_TO_ROTATE${NC}"
        fi
    else
        echo -e "${RED}Error: $KEY_TO_ROTATE is not a rotatable key${NC}"
        echo "Rotatable keys: ${ROTATABLE_KEYS[*]}"
        exit 1
    fi
else
    echo -e "${YELLOW}No keys specified for rotation.${NC}"
    echo "Use --all to rotate all secrets or --key KEY to rotate a specific key."
    exit 0
fi

echo -e "\n${GREEN}Credential rotation complete!${NC}"

# Provide next steps and reminders
echo -e "\n${BLUE}Next steps:${NC}"
echo "1. Validate the updated environment file:"
echo "   python scripts/validate_env.py --env-file $ENV_FILE"
echo "2. Deploy the updated environment to the appropriate services."
echo "3. Update dependent systems with the new credentials."
echo -e "${YELLOW}Note: You may need to update credentials in Render/Vercel dashboards.${NC}"

if [ "$DRY_RUN" = true ]; then
    echo -e "\n${YELLOW}This was a dry run. No changes were made.${NC}"
    echo "Run without --dry-run to make actual changes."
fi

exit 0 