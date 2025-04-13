# Security Scripts for Tavren Backend

This directory contains scripts for managing security in the Tavren backend deployment.

## Available Scripts

### Phase 1: Docker Compose Security

#### `check_docker_security.sh`

Checks Docker Compose configuration for security issues:
- Default credentials in environment variables
- Hardcoded passwords
- Placeholders in configuration files

Usage:
```bash
./scripts/check_docker_security.sh
```

#### `generate_docker_secrets.sh`

Generates secure random values for Docker deployment:
- Creates a new `.env.docker.generated` file with random values
- Replaces placeholders with cryptographically secure values
- Uses OpenSSL for random value generation

Usage:
```bash
./scripts/generate_docker_secrets.sh
```

### Phase 2: Version Control Security

#### `scan_for_credentials.sh`

Scans the repository for potential hardcoded credentials:
- Finds API keys, tokens, and passwords in code
- Checks for sensitive files
- Reports all findings with context

Usage:
```bash
./scripts/scan_for_credentials.sh [path]
```

#### `pre-commit`

Git pre-commit hook to prevent accidental credential commits:
- Blocks commits that contain potential credentials
- Checks file patterns for sensitive files
- Can be bypassed with `--no-verify` if needed

#### `install_git_hooks.sh`

Installs security-focused Git hooks for the repository:
- Sets up the pre-commit hook for credential scanning
- Configures optional Git attributes for binary file handling
- Improves repository security practices

Usage:
```bash
./scripts/install_git_hooks.sh
```

### Phase 3: Environment Variables Management

#### `validate_env.py`

Python script to validate environment variables for deployment:
- Checks for required environment variables
- Validates format and content of variables
- Reports errors, warnings, and suggests fixes

Usage:
```bash
python scripts/validate_env.py [--env-file .env] [--mode production|staging|development]
```

#### `bootstrap_env.sh`

Creates environment files for different deployment environments:
- Generates secure random values for secrets
- Creates environment-specific configuration
- Validates the generated environment

Usage:
```bash
./scripts/bootstrap_env.sh [development|staging|production]
```

### Phase 4: Secrets Management Pipeline

#### `rotate_credentials.sh`

Rotates credentials and secrets automatically:
- Updates secrets with new secure random values
- Creates backups of previous values
- Supports selective or complete rotation

Usage:
```bash
# Rotate a specific credential
./scripts/rotate_credentials.sh --env-file .env.production --key JWT_SECRET_KEY

# Rotate all rotatable credentials
./scripts/rotate_credentials.sh --env-file .env.production --all

# Dry run (simulation mode)
./scripts/rotate_credentials.sh --env-file .env.production --all --dry-run
```

#### `sync_secrets.py`

Synchronizes environment variables to cloud platforms:
- Syncs local .env files to Render and Vercel
- Handles platform-specific variable formatting
- Supports selective platform syncing

Usage:
```bash
# Sync to all platforms
python scripts/sync_secrets.py --env-file .env.production

# Sync to specific platform
python scripts/sync_secrets.py --env-file .env.production --platform render

# Dry run (simulation mode)
python scripts/sync_secrets.py --env-file .env.production --dry-run
```

## Security Implementation Plan

### Phase 1: Docker Compose Security ✅
1. ✅ Removed default credentials from docker-compose.yml
2. ✅ Created a flexible environment template
3. ✅ Added validation tools for security checking
4. ✅ Implemented secure secret generation

### Phase 2: Version Control Security ✅
1. ✅ Repository scanning for sensitive information
2. ✅ Pre-commit hooks to prevent credential leaks
3. ✅ CI pipeline integration for continuous security checks
4. ✅ Git allowlist for false positive management

### Phase 3: Environment Variables Management ✅
1. ✅ Deployment checklist in `DEPLOYMENT_CHECKLIST.md`
2. ✅ Environment validation through `validate_env.py`
3. ✅ Environment bootstrapping via `bootstrap_env.sh`

### Phase 4: Secrets Management Pipeline ✅
1. ✅ Automated credential rotation via `rotate_credentials.sh`
2. ✅ Cloud platform secrets synchronization via `sync_secrets.py`
3. ✅ Credential rotation policy in `CREDENTIAL_ROTATION_POLICY.md`

## Usage Instructions

### Docker Security (Phase 1)
For local development:
```bash
# Generate secure values
./scripts/generate_docker_secrets.sh

# Review and rename the generated file
mv .env.docker.generated .env.docker

# Start services with secure values
docker-compose --env-file .env.docker up -d
```

### Git Security (Phase 2)
Set up repository protection:
```bash
# Install Git hooks
./scripts/install_git_hooks.sh

# Scan existing codebase for credentials
./scripts/scan_for_credentials.sh

# For CI/CD pipeline:
# - GitHub Actions workflow is available at .github/workflows/security-scan.yml
```

### Environment Management (Phase 3)
Set up and validate environments:
```bash
# Bootstrap a new environment (development, staging, or production)
./scripts/bootstrap_env.sh production

# Validate an existing environment file
python scripts/validate_env.py --env-file .env.production --mode production

# Verify your deployment readiness
# Open DEPLOYMENT_CHECKLIST.md and review all items
```

### Secrets Management (Phase 4)
Manage and rotate credentials:
```bash
# Rotate credentials as per policy
./scripts/rotate_credentials.sh --env-file .env.production --all

# Sync updated credentials to cloud platforms
python scripts/sync_secrets.py --env-file .env.production

# Review credential rotation policy
# See CREDENTIAL_ROTATION_POLICY.md for schedules and procedures
```

## Best Practices

- Never commit sensitive information to version control
- Use environment variables for all secrets
- Run security scans before major releases
- Regularly rotate production credentials
- Review CI/CD pipeline security scan results
- Validate environment variables before deployment
- Use appropriate environment settings for each deployment target
- Follow the credential rotation policy for all environments
- Keep secrets synchronized across all platforms
- Document all security incidents and rotation activities 