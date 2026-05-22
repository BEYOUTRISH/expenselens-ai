# ExpenseLens AI - Deployment Guide

This guide describes how to deploy the ExpenseLens project to the cloud.

We support two main cloud deployment methods:
1. **Render (Backend & Postgres) + Vercel (Frontend)** - **(Recommended, Fully Free)**
2. **Railway (Backend) + Vercel (Frontend)** - (Alternative)

---

## Prerequisites

1. **GitHub or GitLab Account** - To host your repository and trigger auto-deployments.
2. **Render Account** (free, no credit card required) - https://render.com
3. **Vercel Account** (free) - https://vercel.com
4. **Groq API Key** (optional, for AI features) - https://console.groq.com

---

## Method 1: Render + Vercel (Recommended & Fully Free)

This method uses the `render.yaml` Blueprint file at the root of the project to automatically configure and deploy the FastAPI backend, a PostgreSQL database, and a persistent storage disk.

### Part 1: Deploy Backend & Database to Render

1. **Push your code to GitHub/GitLab:**
   Ensure the new [render.yaml](file:///c:/Users/KIIT0001/Desktop/Demo/expenselens/render.yaml) file is committed and pushed to your repository.

2. **Deploy via Render Blueprints:**
   - Go to your [Render Dashboard](https://dashboard.render.com).
   - Click **New** (top right) → **Blueprint**.
   - Connect your GitHub or GitLab account and select your `expenselens` repository.
   - Render will parse `render.yaml` and show the resources it will create:
     - **Service:** `expenselens-backend` (FastAPI Web Service)
     - **Database:** `expenselens-db` (PostgreSQL Database)
     - **Disk:** `upload-disk` (1 GB Persistent Disk)
   - You will be prompted to enter values for:
     - `CORS_ORIGINS`: Set this to `*` for initial setup, then update it to your Vercel URL after deploying the frontend.
     - `GROQ_API_KEY`: Input your Groq API key (optional, for AI features).
   - Click **Apply**. Render will automatically provision the database and build/deploy the backend.

3. **Get your Backend URL:**
   Once the backend service deployment is complete, copy the backend URL from the top of the service page in Render (looks like `https://expenselens-backend-xxxx.onrender.com`).

---

### Part 2: Deploy Frontend to Vercel

1. Go to your [Vercel Dashboard](https://vercel.com).
2. Click **Add New** → **Project**.
3. Import your `expenselens` repository.
4. Configure the project settings:
   - **Framework Preset:** Next.js
   - **Root Directory:** `frontend`
   - **Build Command:** `npm run build`
   - **Environment Variables:**
     - Add `NEXT_PUBLIC_API_URL` = `https://your-render-backend-app-name.onrender.com/api` (replace with your actual Render backend URL).
5. Click **Deploy**.

---

### Part 3: Secure CORS (Optional but Recommended)

Once Vercel gives you your frontend production URL (e.g. `https://expenselens-xxx.vercel.app`):
1. Go to your Render Dashboard.
2. Select your `expenselens-backend` web service.
3. Go to **Environment**.
4. Update `CORS_ORIGINS` from `*` to your exact Vercel frontend URL.
5. Save changes. Render will automatically redeploy the backend with the new CORS restrictions.

---

## Method 2: Railway + Vercel (Alternative)

### Part 1: Deploy Backend to Railway

#### Option A: Deploy via Railway CLI
1. **Install Railway CLI:**
   ```bash
   npm install -g @railway/cli
   ```
2. **Login to Railway:**
   ```bash
   railway login
   ```
3. **Initialize and Deploy:**
   ```bash
   cd backend
   railway init
   # Select "Empty Project" or create a new one
   railway up
   ```
4. **Add Persistent Volume:**
   - Go to Railway Dashboard → Select your project → Volumes.
   - Add Volume: Mount Path = `/app/uploads`, Size = `1 GB`.
5. **Set Environment Variables:**
   Go to Railway Dashboard → Variables:
   ```env
   SECRET_KEY=<generate-secure-key>
   ENVIRONMENT=production
   GROQ_API_KEY=<your-groq-api-key>
   CORS_ORIGINS=https://your-vercel-app.vercel.app
   ```

#### Option B: Deploy via Docker
1. **Build and push Docker image:**
   ```bash
   cd backend
   docker build -t your-username/expenselens-backend .
   docker push your-username/expenselens-backend
   ```
2. **Deploy on Railway using the Docker image.**

### Part 2: Deploy Frontend to Vercel
(Same as Part 2 under Method 1)

---

## Environment Variables Reference

### Backend (Render/Railway)

| Variable | Required? | Description |
|----------|-----------|-------------|
| `SECRET_KEY` | Yes | Secure random string for sessions (auto-generated in Render Blueprint) |
| `ENVIRONMENT` | No | `development` or `production` |
| `DATABASE_URL` | No | PostgreSQL connection string (auto-injected in Render Blueprint) |
| `GROQ_API_KEY` | No | For AI features |
| `GROQ_MODEL` | No | Default: `llama-3.1-8b-instant` |
| `CORS_ORIGINS` | Yes | Your Vercel frontend URL |
| `UPLOAD_DIR` | No | Default: `/app/uploads` |

### Frontend (Vercel)

| Variable | Required? | Description |
|----------|-----------|-------------|
| `NEXT_PUBLIC_API_URL` | Yes | Backend `/api` URL (e.g. `https://your-backend.onrender.com/api`) |

---

## Testing the Deployment

1. **Health Check:**
   Run this in your terminal or browser:
   ```bash
   curl https://your-backend-app-name.onrender.com/api/health
   ```
   Expected response:
   ```json
   {
     "status": "ok",
     "app": "ExpenseLens AI",
     "version": "1.0.0",
     "environment": "production",
     "database": "postgresql"
   }
   ```

2. **Frontend:**
   Visit your Vercel URL and verify:
   - Upload page loads.
   - Can upload a sample file (found in `backend/sample_data/dirty_expenses.xlsx`).
   - Dashboard loads with charts and analytical insights.

---

## Troubleshooting

### Issue: Build fails with "TypeScript not found" or "Next.js Build Error"
**Fix:** Ensure your Vercel project has the **Root Directory** set to `frontend` so it doesn't try to build the backend requirements as Node dependencies.

### Issue: Data resets after deploy
**Fix:** Render blueprint automatically mounts a persistent disk volume to store uploads. Make sure you don't delete the `disk` block in `render.yaml`.

### Issue: CORS errors
**Fix:** Verify `CORS_ORIGINS` matches your Vercel URL exactly (including `https://` and without a trailing slash `/`).
