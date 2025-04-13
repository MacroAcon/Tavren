# Tavren Deployment Checklist

This checklist helps ensure that your Tavren deployment is secure and properly configured.

## Environment Configuration

### Backend (.env files)

| ✅ | Requirement | Description |
|---|-------------|-------------|
| □ | Secure JWT secret | A unique, random 32+ character hex string (`openssl rand -hex 32`) |
| □ | Secure encryption key | A unique, random 16+ character hex string (`openssl rand -hex 16`) |
| □ | Secure admin API key | A unique, random 24+ character hex string (`openssl rand -hex 24`) |
| □ | Correct database URL | PostgreSQL connection string with proper credentials |
| □ | Correct environment | Set to `production` for production deployments |
| □ | Appropriate log level | Set to `WARNING` or `ERROR` for production |
| □ | Redis password (if used) | A strong password for Redis |
| □ | Nginx API key (if needed) | A valid API key with required permissions |

### Frontend (.env)

| ✅ | Requirement | Description |
|---|-------------|-------------|
| □ | Backend API URL | Correct URL to the deployed backend service |
| □ | No sensitive values | Frontend env should not contain any sensitive keys |

## Docker Configuration

| ✅ | Requirement | Description |
|---|-------------|-------------|
| □ | No default credentials | Docker Compose shouldn't contain default credentials |
| □ | Database port not exposed | Database should not be accessible from outside the Docker network |
| □ | Secure volume configuration | Data volumes properly secured with appropriate permissions |
| □ | Latest base images | Using the latest secure base images for services |
| □ | Container security | Non-root users, minimal permissions, resource limits |

## Infrastructure Security

| ✅ | Requirement | Description |
|---|-------------|-------------|
| □ | HTTPS enabled | All traffic encrypted with valid SSL certificates |
| □ | HTTP to HTTPS redirect | Redirect all HTTP traffic to HTTPS |
| □ | Firewall configured | Limit inbound connections to necessary ports only |
| □ | Rate limiting | API endpoints protected from brute force attacks |
| □ | CORS configured | Proper CORS settings to restrict API access |
| □ | Security headers | Content-Security-Policy, X-XSS-Protection, etc. |

## Security Practices

| ✅ | Requirement | Description |
|---|-------------|-------------|
| □ | Security scripts | Run `scan_for_credentials.sh` to verify no sensitive data |
| □ | Environment validation | Run `validate_env.py` to check all required variables |
| □ | Secret rotation | Plan for regular rotation of secrets and credentials |
| □ | Data backup | Regular database backups with secure storage |
| □ | Error handling | No sensitive information in error messages/logs |
| □ | Database security | Strong passwords, least privilege access, secure connection |

## Render.com Deployment (Backend)

| ✅ | Requirement | Description |
|---|-------------|-------------|
| □ | Environment Variables | All required env vars set in Render dashboard |
| □ | Database provisioned | PostgreSQL instance created and configured |
| □ | Build command | Set to `pip install -r requirements.txt` |
| □ | Start command | Set to `uvicorn app.main:app --host=0.0.0.0 --port=10000` |
| □ | Health check | Configure health check endpoint if available |
| □ | Auto-deploy | Configure auto-deploy from main/production branch |

## Vercel Deployment (Frontend) 

| ✅ | Requirement | Description |
|---|-------------|-------------|
| □ | Environment Variables | Set `VITE_API_BASE_URL` to backend URL |
| □ | Build Command | Set to `npm run build` |
| □ | Output Directory | Set to `dist` |
| □ | Node.js Version | Use appropriate Node.js version (16+) |
| □ | Preview Deployments | Configure preview deployments for PRs if needed |

## Post-Deployment Verification

| ✅ | Task | Description |
|---|------|-------------|
| □ | API Health | Verify API server is running and responding |
| □ | Frontend Load | Verify frontend loads and communicates with backend |
| □ | Authentication | Test user login and token-based authentication |
| □ | Core Features | Test main application features and flows |
| □ | Error Handling | Verify graceful handling of API errors |
| □ | Performance | Check application performance and response times |
| □ | Logs | Verify proper logging without sensitive information |

## Emergency Response

| ✅ | Preparation | Description |
|---|-------------|-------------|
| □ | Rollback plan | Document steps to rollback to previous version |
| □ | Contact list | Emergency contacts for infrastructure issues |
| □ | Credential replacement | Process for replacing compromised credentials |
| □ | Incident response | Plan for responding to security incidents |

---

## Deployment Commands

Bootstrap your environment with:
```bash
# For staging
./scripts/bootstrap_env.sh staging

# For production
./scripts/bootstrap_env.sh production
```

Validate your environment with:
```bash
# For staging
python scripts/validate_env.py --env-file .env.staging --mode staging

# For production 
python scripts/validate_env.py --env-file .env.production --mode production
```

Check for credentials before deployment:
```bash
./scripts/scan_for_credentials.sh
``` 