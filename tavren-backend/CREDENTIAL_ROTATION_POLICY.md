# Tavren Credential Rotation Policy

This document outlines the credential rotation policy for Tavren's production and development environments.

## Overview

Regular rotation of credentials and secrets is a critical security practice that helps:
- Limit the impact of credential exposure
- Reduce the risk of unauthorized access
- Comply with security best practices and standards
- Protect against credential theft and brute-force attacks

## Credential Types and Rotation Schedule

| Credential Type | Environment | Rotation Frequency | Responsibility | Tool |
|-----------------|-------------|-------------------|----------------|------|
| JWT Secret Keys | Production | 90 days | DevOps Team | `rotate_credentials.sh` |
| JWT Secret Keys | Staging | 180 days | Development Team | `rotate_credentials.sh` |
| Database Credentials | Production | 90 days | DevOps Team | `rotate_credentials.sh` |
| Database Credentials | Staging | 180 days | Development Team | `rotate_credentials.sh` |
| Admin API Keys | Production | 60 days | DevOps Team | `rotate_credentials.sh` |
| API Keys (External Services) | All | 180 days | Development Team | `rotate_credentials.sh` |
| Developer Access Tokens | All | 30 days | Individual Developers | Manual |
| CI/CD Pipeline Tokens | All | 90 days | DevOps Team | Manual |
| Cloud Provider Tokens | All | 180 days | DevOps Team | Cloud Provider UI |

## Rotation Procedures

### Automated Rotation (Using Scripts)

For JWT secrets, database credentials, and API keys, use the provided rotation script:

```bash
# Rotate a specific credential in production
./scripts/rotate_credentials.sh --env-file .env.production --key JWT_SECRET_KEY

# Rotate all rotatable credentials in staging
./scripts/rotate_credentials.sh --env-file .env.staging --all

# Dry run to test rotation without making changes
./scripts/rotate_credentials.sh --env-file .env.production --all --dry-run
```

After rotating credentials:

1. Validate the updated environment:
   ```bash
   python scripts/validate_env.py --env-file .env.production --mode production
   ```

2. Sync the new credentials to cloud platforms:
   ```bash
   python scripts/sync_secrets.py --env-file .env.production
   ```

3. Deploy the updated environment to the appropriate services.

### Manual Rotation

For credentials that cannot be rotated automatically:

1. Generate a new secure credential using appropriate methods (e.g., `openssl rand -hex 32`).
2. Update the credential in all necessary systems.
3. Verify that all systems function correctly with the new credential.
4. Revoke the old credential after a suitable transition period.

## Emergency Rotation

In case of suspected credential compromise:

1. Initiate immediate rotation of affected credentials
2. Document the incident following the security incident response plan
3. Investigate the scope of potential exposure
4. Consider rotating additional credentials that might be affected
5. Review security logs for signs of unauthorized access

## Implementation Checklist

When rotating credentials:

- [ ] Schedule the rotation during low-traffic periods
- [ ] Ensure backup credentials are available for rollback if needed
- [ ] Test the new credentials in a staging environment first
- [ ] Notify appropriate team members before rotation
- [ ] Update credential documentation
- [ ] Verify system functionality after rotation
- [ ] Securely dispose of old credentials

## Auditing and Compliance

- Rotation activities should be logged and auditable
- Regular reviews of credential age and compliance with rotation schedules
- Quarterly audit of credential rotation compliance

## Tools and Resources

- `rotate_credentials.sh` - Rotates credentials in environment files
- `sync_secrets.py` - Syncs environment variables to cloud platforms
- `validate_env.py` - Validates environment variables for correctness

## Responsibility Matrix

| Role | Responsibilities |
|------|------------------|
| DevOps Team | Production credentials, Infrastructure secrets |
| Development Team | Staging/Dev credentials, API keys for development |
| Security Officer | Policy oversight, Audit compliance, Emergency response |
| Individual Developers | Personal access tokens, Local development credentials |

## Exceptions

Exceptions to this policy require:
1. Written approval from the Security Officer
2. Documentation of the business need for the exception
3. Implementation of compensating controls
4. Regular review of the exception status

## Policy Review

This policy will be reviewed every 12 months or when significant changes occur to the application architecture or security requirements.

Last updated: $(date +"%B %Y") 