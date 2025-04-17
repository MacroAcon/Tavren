# Tavren Deployment Guide

This guide provides detailed instructions for deploying both the Tavren frontend and backend. It supports local, Docker-based, and free-tier cloud-hosted environments using **Render** (backend) and **Vercel** (frontend).

---

## 📁 Project Structure

```
/tavren-frontend/   # React + Vite frontend
/tavren-backend/    # FastAPI backend with SQLite or PostgreSQL
/docs/              # Documentation and integration plans
```

---

## ⚙️ Environment Setup

### Required Tools
- Node.js (v16+)
- Python 3.8+
- pip or poetry
- Git
- Optional: Docker + Docker Compose (for local dev)

---

## 🖥️ Local Development (No Docker)

### Frontend (Vite + React)
```bash
cd tavren-frontend
cp .env.example .env   # Update VITE_API_BASE_URL as needed
npm install
npm run dev
```

### Backend (FastAPI)
```bash
cd tavren-backend
python -m venv venv
source venv/bin/activate    # On Windows: .\venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

- API will be available at: `http://localhost:8000`
- Swagger UI: `http://localhost:8000/docs`

---

## ☁️ Free Cloud Deployment

### 🔹 Vercel (Frontend)
1. Push `tavren-frontend` to GitHub
2. Import the repo into your Vercel dashboard
3. In project settings, add:
   - `VITE_API_BASE_URL=https://<your-backend-service>.onrender.com`
4. Build Command: `npm run build`
5. Output Directory: `dist/`
6. Deploy

### 🔹 Render (Backend)
1. Push `tavren-backend` to GitHub
2. Go to [render.com](https://render.com) → New Web Service
3. Connect GitHub and select the backend repo
4. Set:
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host=0.0.0.0 --port=10000`
5. Add environment variables:
   - `DATABASE_URL` (use Render's PostgreSQL free tier if needed)
   - `API_SECRET` (used for JWT or secure routes)
6. Deploy and copy the public URL (used in Vercel frontend)

---

## 🔐 Environment Configuration

### Backend (.env files)

| Variable | Required | Description |
|----------|----------|-------------|
| `JWT_SECRET` | ✅ | A unique, random 32+ character hex string (`openssl rand -hex 32`) |
| `ENCRYPTION_KEY` | ✅ | A unique, random 16+ character hex string (`openssl rand -hex 16`) |
| `ADMIN_API_KEY` | ✅ | A unique, random 24+ character hex string (`openssl rand -hex 24`) |
| `DATABASE_URL` | ✅ | PostgreSQL connection string with proper credentials |
| `ENVIRONMENT` | ✅ | Set to `production` for production deployments |
| `LOG_LEVEL` | ✅ | Set to `WARNING` or `ERROR` for production |
| `REDIS_PASSWORD` | If used | A strong password for Redis |
| `NGINX_API_KEY` | If needed | A valid API key with required permissions |

### Frontend (.env)

| Variable | Required | Description |
|----------|----------|-------------|
| `VITE_API_BASE_URL` | ✅ | URL of the backend API |

---

## 📦 Build Commands (Frontend)
```bash
cd tavren-frontend
npm run build        # Production build
npm run preview      # Local preview of built app
```

---

## 🔒 Deployment Security Checklist

### Docker Configuration

| Requirement | Description |
|-------------|-------------|
| No default credentials | Docker Compose shouldn't contain default credentials |
| Database port not exposed | Database should not be accessible from outside the Docker network |
| Secure volume configuration | Data volumes properly secured with appropriate permissions |
| Latest base images | Using the latest secure base images for services |
| Container security | Non-root users, minimal permissions, resource limits |

### Infrastructure Security

| Requirement | Description |
|-------------|-------------|
| HTTPS enabled | All traffic encrypted with valid SSL certificates |
| HTTP to HTTPS redirect | Redirect all HTTP traffic to HTTPS |
| Firewall configured | Limit inbound connections to necessary ports only |
| Rate limiting | API endpoints protected from brute force attacks |
| CORS configured | Proper CORS settings to restrict API access |
| Security headers | Content-Security-Policy, X-XSS-Protection, etc. |

### Security Practices

| Practice | Description |
|----------|-------------|
| Security scripts | Run `scan_for_credentials.sh` to verify no sensitive data |
| Environment validation | Run `validate_env.py` to check all required variables |
| Secret rotation | Plan for regular rotation of secrets and credentials |
| Data backup | Regular database backups with secure storage |
| Error handling | No sensitive information in error messages/logs |
| Database security | Strong passwords, least privilege access, secure connection |

### Deployment Validation Commands

```bash
# For staging
./scripts/bootstrap_env.sh staging
python scripts/validate_env.py --env-file .env.staging --mode staging

# For production
./scripts/bootstrap_env.sh production
python scripts/validate_env.py --env-file .env.production --mode production

# Check for credentials before deployment
./scripts/scan_for_credentials.sh
```

---

## 🧪 Post-Deployment Checklist

| Task | Description |
|------|-------------|
| API reachable | API server is running and responding at deployed URL |
| Swagger docs | Swagger docs load at `/docs` endpoint |
| Frontend load | Frontend loads and communicates with backend |
| Environment vars | Environment variables injected correctly |
| Authentication | User login and token-based authentication works |
| Core features | Offer feed, wallet, and preferences function as expected |
| Error handling | Verify graceful handling of API errors |
| Performance | Check application performance and response times |
| Logs | Verify proper logging without sensitive information |
| No mock data | QAHelper confirms no mock data in production |

### Emergency Response

| Preparation | Description |
|-------------|-------------|
| Rollback plan | Document steps to rollback to previous version |
| Contact list | Emergency contacts for infrastructure issues |
| Credential replacement | Process for replacing compromised credentials |
| Incident response | Plan for responding to security incidents |

---

## 📄 Related Docs
- [`API_Integration_Plan.md`](../docs/API_Integration_Plan.md)
- [`LICENSE`](../LICENSE)
- [`tavren-frontend/ROADMAP.md`](../tavren-frontend/ROADMAP.md)

---

For any deployment questions, contact Asa or reference the Swagger docs at `/docs` once deployed.

