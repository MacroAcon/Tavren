# Security Scripts for Tavren Backend

This directory contains scripts for managing security in the Tavren backend deployment.

## Available Scripts

### `check_docker_security.sh`

Checks Docker Compose configuration for security issues:
- Default credentials in environment variables
- Hardcoded passwords
- Placeholders in configuration files

Usage:
```bash
./scripts/check_docker_security.sh
```

### `generate_docker_secrets.sh`

Generates secure random values for Docker deployment:
- Creates a new `.env.docker.generated` file with random values
- Replaces placeholders with cryptographically secure values
- Uses OpenSSL for random value generation

Usage:
```bash
./scripts/generate_docker_secrets.sh
```

## Security Implementation Plan

These scripts implement Phase 1 of our security implementation plan:

1. ✅ Removed default credentials from docker-compose.yml
2. ✅ Created a flexible environment template
3. ✅ Added validation tools for security checking
4. ✅ Implemented secure secret generation

## Usage Instructions

For local development:
```bash
# Generate secure values
./scripts/generate_docker_secrets.sh

# Review and rename the generated file
mv .env.docker.generated .env.docker

# Start services with secure values
docker-compose --env-file .env.docker up -d
```

For production:
```bash
# Check security before deployment
./scripts/check_docker_security.sh

# If issues are found, fix them before continuing
# Run docker compose with secure environment
docker-compose --env-file .env.docker up -d
``` 