# Deployment Guide

This guide covers how to deploy the ExoVetter application using a split architecture: **Cloudflare Pages** for the ultra-fast frontend and **Render.com** (or similar) for the Python FastAPI backend.

## 1. Deploying the Backend (Python FastAPI)

Since the backend uses Python (and eventually data science libraries like `astropy` and `torch`), it needs to be hosted on a standard containerized service. Render.com is perfect for this (and has a free tier).

### Option A: Render.com (Recommended for Hackathons)
1. Create a free account at [Render.com](https://render.com).
2. Click **New +** and select **Web Service**.
3. Connect your GitHub repository (`ZeroiJ/ps7`).
4. Configure the service:
   - **Name**: `exovetter-api` (or similar)
   - **Root Directory**: `backend`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port 10000`
5. Click **Create Web Service**. 
6. Wait for the deployment to finish. Once done, copy the URL provided by Render (e.g., `https://exovetter-api.onrender.com`).

*(Note: Render's free tier spins down after 15 minutes of inactivity, so the first request after a break might take ~30 seconds to wake up).*

---

## 2. Deploying the Frontend (Cloudflare Pages)

We have already configured Next.js to do a static HTML export (`output: 'export'`), making it fully compatible with Cloudflare Pages.

### Step 1: Connect to Cloudflare
1. Log in to your [Cloudflare Dashboard](https://dash.cloudflare.com/).
2. Go to **Workers & Pages** from the left sidebar, then click **Create Application**.
3. Select the **Pages** tab and click **Connect to Git**.
4. Authorize your GitHub account and select the `ZeroiJ/ps7` repository.

### Step 2: Configure the Build
Set the following build settings:
- **Framework preset**: `Next.js (Static HTML Export)`
- **Root directory**: `frontend`
- **Build command**: `npm run build`
- **Build output directory**: `out`

### Step 3: Add the Backend API Variable
Scroll down to **Environment variables (advanced)** and click **Add variable**:
- **Variable name**: `NEXT_PUBLIC_API_URL`
- **Value**: The URL you got from Render in Step 1 (e.g., `https://exovetter-api.onrender.com`)

### Step 4: Deploy
Click **Save and Deploy**. Cloudflare will build your Next.js application and deploy it globally to their edge network.

---

## 3. Local Development

To run the application locally on your machine for further development:

**Backend:**
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows use: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

**Frontend:**
Open a new terminal window:
```bash
cd frontend
npm install
npm run dev
```
The frontend will be available at `http://localhost:3000`. By default, it will automatically connect to your local backend at `http://localhost:8000`.
