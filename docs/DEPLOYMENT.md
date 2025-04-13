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

## 🔐 Environment Variables
| Variable | Location | Description |
|----------|----------|-------------|
| `VITE_API_BASE_URL` | Frontend | URL of the backend API |
| `DATABASE_URL` | Backend | PostgreSQL DB string |
| `API_SECRET` | Backend | JWT or auth secret |

---

## 📦 Build Commands (Frontend)
```bash
cd tavren-frontend
npm run build        # Production build
npm run preview      # Local preview of built app
```

---

## 🧪 Post-Deployment Checklist
- [ ] API reachable at deployed Render URL
- [ ] Swagger docs load at `/docs`
- [ ] Frontend loads and communicates with backend
- [ ] Environment vars injected correctly
- [ ] Auth/login works end-to-end
- [ ] Offer feed, wallet, and preferences function as expected
- [ ] QAHelper confirms no mock data in production

---

## 📄 Related Docs
- [`API_Integration_Plan.md`](../docs/API_Integration_Plan.md)
- [`LICENSE`](../LICENSE)
- [`tavren-frontend/ROADMAP.md`](../tavren-frontend/ROADMAP.md)

---

For any deployment questions, contact Asa or reference the Swagger docs at `/docs` once deployed.

