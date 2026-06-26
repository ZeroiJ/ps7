# ExoVetter — Exoplanet Data Analysis

ExoVetter is an ultra-minimalist, single-page web application designed for the ISRO BAH Challenge 7. It allows users to upload light-curve data (CSV, JSON, NPZ) and instantly receive processed results, including transit detection, feature extraction, and classification probabilities.

The UI is inspired by the **Chroma design system** — typography-forward, black, white, and grays, with no unnecessary decorative elements.

## Architecture

This project uses a split architecture:
- **Frontend**: Next.js 14+ (Static HTML Export), Tailwind CSS v4, Plotly.js, Zustand
- **Backend**: Python FastAPI, Pandas, NumPy (Simulated ML Pipeline)

## Getting Started Locally

To run the application locally, you will need two terminal windows.

### 1. Start the Backend
The backend runs on FastAPI and uses a mock pipeline to generate realistic TESS-like transit data.

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```
The backend API will be available at `http://localhost:8000`.

### 2. Start the Frontend
The frontend is a Next.js application.

```bash
cd frontend
npm install
npm run dev
```
The frontend will be available at `http://localhost:3000`. 
By default, it will automatically connect to your local backend.

## Deployment

The application is configured to be easily deployed to **Cloudflare Pages** (Frontend) and **Render** (Backend).

Please see the [DEPLOYMENT_GUIDE.md](docs/DEPLOYMENT_GUIDE.md) for step-by-step instructions.

## Documentation Reference
All design and technical specifications are located in the `docs/` directory:
- [Product Requirements (PRD.md)](docs/PRD.md)
- [Technical Requirements (TRD.md)](docs/TRD.md)
- [Chroma Style Guide (STYLE_GUIDE.md)](docs/STYLE_GUIDE.md)
