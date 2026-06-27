# ExoVetter — Exoplanet Data Analysis

ExoVetter is an ultra-minimalist web application for processing TESS light curves. It takes raw flux data (CSV, JSON, NPZ) and sequentially preprocesses it, runs a Transit Least Squares (TLS) search, extracts features, and finally classifies it as a Planet Candidate, Eclipsing Binary, or False Positive.

## 🏗 Architecture Overview

This project uses a decoupled, serverless-friendly architecture:

- **Frontend**: Next.js 14+ (React), deployed as a static site on **Cloudflare Pages**.
  - We use **Recharts** for lightweight, performant data visualization (replacing Plotly for faster load times).
  - The UI utilizes a beautiful, typography-forward "Chroma" bento-grid layout.
- **Backend**: Python 3.11 + FastAPI, deployed as a Docker container on **Hugging Face Spaces**.
  - Powered by heavy astronomical libraries (`lightkurve`, `transitleastsquares`, `numpy`, `scipy`).
  - To bypass memory (OOM) and timeout limits on free tiers, the backend utilizes a **Sequential 6-Step Pipeline**.

## ⚙️ How the Backend Works

Since processing 50,000+ points of astronomical data can crash free-tier servers if done all at once, we broke the pipeline into 6 granular API endpoints. 

1. **Upload & Preprocess** (`/api/step/upload`): Receives the file, runs Sigma Clipping (removes outliers), and applies a Savitzky-Golay filter to flatten the light curve.
2. **Transit Search** (`/api/step/tls`): Runs the Transit Least Squares algorithm to find the period, depth, and duration.
3. **Feature Extraction** (`/api/step/features`): Derives physical parameters (like star radius ratios).
4. **Physical Parameters** (`/api/step/parameters`): (Placeholder for deeper astrophysical calculations).
5. **Classification** (`/api/step/classify`): Uses heuristics (like Signal Detection Efficiency, SDE) to classify the signal.
6. **Output** (`/api/step/output`): Aggregates all results for the frontend to download as JSON.

### 💾 Session Storage (State Management)
Because HTTP requests are stateless and we split the task into 6 steps, the backend saves intermediate arrays (like the cleaned light curve and TLS results) into local JSON files in a temporary directory (`/tmp/exovetter_sessions/<session_id>.json`). 

The frontend simply passes the `session_id` to the next step, allowing the backend to pick up exactly where it left off. This completely avoids sending massive NumPy arrays back and forth over the network. 

### 🛡️ Safety & Resiliency
NumPy operations frequently produce `NaN` (Not a Number) or `Infinity` values which inherently crash standard JSON parsers. We implemented a custom `SafeJSONResponse` and `NanSafeEncoder` that intercepts all backend API responses and safely converts NaNs to `null` before sending them to the frontend.

## 🚀 Getting Started Locally

### 1. Start the Backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```
*(Backend runs at `http://localhost:8000`)*

### 2. Start the Frontend
```bash
cd frontend
npm install
npm run dev
```
*(Frontend runs at `http://localhost:3000`. It will automatically connect to your HF Spaces API unless you override the `NEXT_PUBLIC_API_URL` environment variable.)*

## 📦 Deployment
- **Frontend**: Push to the `main` branch on GitHub to automatically deploy via Cloudflare Pages.
- **Backend**: Deploy to Hugging Face Spaces using the Hugging Face CLI:
  ```bash
  cd backend
  hf upload <your-username>/exovetter-api . . --repo-type space --exclude ".venv/**" --exclude "**/__pycache__/**"
  ```
