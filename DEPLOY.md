# Deployment Guide

## Architecture

- **Frontend**: Vercel (Next.js)
- **Backend**: Railway (FastAPI + Docker)
- **Database**: Railway MySQL/MariaDB
- **Cache**: Railway Redis

---

## Railway (Backend)

### 1. Create Project

- Go to railway.app and create new project
- Connect GitHub repository

### 2. Add Services

**Backend Service:**
- Click "New Service" > "GitHub Repo"
- Select this repository
- Set root directory to `backend`

**MySQL Database:**
- Click "New Service" > "Database" > "MySQL"
- Automatically creates DATABASE_URL variable

**Redis:**
- Click "New Service" > "Database" > "Redis"
- Automatically creates REDIS_URL variable

### 3. Environment Variables (Backend)

Required variables for backend service:

```
DEBUG=false
DATABASE_URL=${{MySQL.DATABASE_URL}}
REDIS_URL=${{Redis.REDIS_URL}}
GOOGLE_API_KEY=your-google-api-key
SECRET_KEY=your-secure-secret-key
```

Optional variables:
```
OPENAI_API_KEY=your-openai-key
LUMA_API_KEY=your-luma-key
```

### 4. Database Migration

After deployment, run migrations via Railway CLI:
```bash
railway run alembic upgrade head
```

---

## Vercel (Frontend)

### 1. Import Project

- Go to vercel.com
- Import from GitHub
- Set root directory to `frontend`

### 2. Environment Variables

Required:
```
NEXT_PUBLIC_API_URL=https://your-backend.railway.app
```

### 3. Build Settings

- Framework: Next.js (auto-detected)
- Build Command: `npm run build`
- Output Directory: `.next`

---

## Post-Deployment Checklist

1. Verify backend health: `https://backend.railway.app/health`
2. Run database migrations
3. Test frontend-backend connection
4. Create initial admin user
5. Configure CORS if needed

---

## Local Development

```bash
# Backend
cd backend
docker-compose up -d  # Database, Redis
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```
