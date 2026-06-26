# Technical Requirements Document — Data Upload & Analysis Web App

> **Stack**: Python (FastAPI backend) + JavaScript (Next.js frontend, style = Chroma)
> **Note for AI builder**: All docs reference Chroma's exact CSS variables. Use `--var-name` directly in your Tailwind config.

---

## 1. Architecture Overview

```
┌─────────────────────────────┐
│   Browser (Next.js SPA)     │
│   style: Chroma minimalist  │
│   charts: Plotly.js          │
└──────────┬──────────────────┘
           │ HTTP (JSON + files)
           ▼
┌─────────────────────────────┐
│   FastAPI Backend            │
│   /api/upload                │
│   /api/process               │
│   /api/sample-data           │
│   /api/download/<job_id>     │
│                              │
│   ┌─────────────────────┐   │
│   │ Pipeline Engine      │   │
│   │ (from pipeline/*.py) │   │
│   └─────────────────────┘   │
└─────────────────────────────┘
```

---

## 2. Frontend Architecture

### 2.1 Framework
- **Next.js 14+** (App Router, no SSR for this page — static export)
- **Tailwind CSS v4** with custom theme matching Chroma's CSS variables
- **Plotly.js** via `react-plotly.js` for interactive charts
- **react-dropzone** for drag-and-drop file upload
- **zustand** (or React context) for state — single upload->process->results flow

### 2.2 Chroma Color Theme (Tailwind Config)

```javascript
// tailwind.config.js
export default {
  theme: {
    extend: {
      colors: {
        'chroma-bg':       '#ffffff',
        'chroma-muted':    '#f6f6f6',
        'chroma-border':   '#e8e8e8',
        'chroma-fg':       '#070707',
        'chroma-muted-fg': '#7b7b7b',
        'chroma-black':    '#27201c',
        'chroma-primary':  '#141414',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['IBM Plex Mono', 'monospace'],
      },
      fontSize: {
        'hero': ['24px', { lineHeight: '36px', fontWeight: '400' }],
        'subtitle': ['16px', { lineHeight: '24px', fontWeight: '400' }],
        'body': ['16px', { lineHeight: '24px' }],
        'caption': ['14px', { lineHeight: '20px' }],
        'tiny': ['13px', { lineHeight: '16px' }],
      },
      borderRadius: {
        'chroma': '8px',
      },
      spacing: {
        'nav': '73px',
      },
    }
  }
}
```

### 2.3 Key Components

#### `Navbar`
- Fixed top, h-[73px], transparent bg, border-b border-chroma-border
- Left: logo SVG (wordmark, ~98×24px)
- Right: dark mode toggle button (inline SVG icon)
- No backdrop blur needed (transparent)

#### `UploadZone`
- Min-h-[300px], dashed border (2px dashed #e8e8e8), rounded-[8px]
- Centered flex column: icon + "Drop your file here" heading + "CSV, JSON, NPZ up to 200 MB" caption
- States: empty / dragging (border turns black) / uploading (pulsing indicator) / loaded (shows file name + size + remove button)

#### `ProgressStepper`
- 5 steps in a horizontal row, connected by thin gray lines
- Each step: circle (24px) + label text
- States: pending (gray circle) / active (black circle, pulsing) / done (black circle with checkmark)
- Elapsed timer below

#### `ResultsDashboard`
- Verdict badge: pill shape, 3 variants (green#4ade80/black/yellow#eab308)
- Key metrics row: 4 cards, each = value (bold, 2xl) + label (caption, muted)
- Chart grid: CSS grid 2×2, gap-[24px], each chart in a white card with subtle shadow
- Download button: black bg, white text, rounded-chroma, hover:opacity-90

#### `Footer`
- Border-t border-chroma-border, py-[48px]
- Logo + text centered
- Small copyright

---

## 3. Backend Architecture

### 3.1 Endpoints

| Endpoint | Method | Input | Output | Description |
|----------|--------|-------|--------|-------------|
| `/api/upload` | POST | multipart/form-data (file) | `{ job_id, filename, rows, columns_preview, message }` | Accepts file, validates, stores in temp dir, returns preview |
| `/api/process/{job_id}` | POST | — | `{ status, result }` or `{ status: "processing" }` | Runs pipeline synchronously (or returns job ID for polling) |
| `/api/sample-data` | GET | `?target=TOI-270` | binary (redirect to static .npz file) | Returns a pre-packaged sample light curve |
| `/api/download/{job_id}` | GET | `?format=zip` | binary .zip | Downloads all result plots + metrics JSON |
| `/api/status/{job_id}` | GET | — | `{ status: "queued"|"processing"|"done"|"error", progress, result }` | Polling endpoint for async processing |

### 3.2 Processing Model

```python
# Simplified request flow
@app.post("/api/upload")
async def upload_file(file: UploadFile):
    ext = Path(file.filename).suffix.lower()
    if ext not in {".csv", ".json", ".npz"}:
        raise HTTPException(400, "Unsupported format")
    
    job_id = str(uuid4())
    save_path = TEMP_DIR / f"{job_id}{ext}"
    contents = await file.read()
    
    if len(contents) > 200 * 1024 * 1024:
        raise HTTPException(400, "File exceeds 200 MB limit")
    
    save_path.write_bytes(contents)
    
    # Parse and return preview
    if ext == ".csv":
        df = pd.read_csv(save_path)
        preview = df.head(5).to_dict(orient="records")
        columns = list(df.columns)
    elif ext == ".npz":
        npz = np.load(save_path)
        preview = {key: arr.shape for key, arr in npz.items()}
        columns = list(npz.keys())
    
    return {
        "job_id": job_id,
        "filename": file.filename,
        "rows": len(df) if ext == ".csv" else 0,
        "columns": columns,
        "preview": preview,
        "message": "File uploaded successfully"
    }


@app.post("/api/process/{job_id}")
async def process_file(job_id: str):
    # Find file in TEMP_DIR
    # Call the pipeline
    from pipeline import run_pipeline
    
    try:
        result = run_pipeline(file_path)
        return {"status": "done", "result": result}
    except Exception as e:
        return {"status": "error", "error": str(e)}
```

### 3.3 Result Schema

```python
@dataclass
class PipelineResult:
    target_name: str
    preprocessed: dict        # n_points, time_span, flux_range
    tls_result: dict          # period, sde, depth, duration, snr
    features: dict            # physics, stats, diagnostics arrays
    classification: dict      # predicted_class, confidence, class_probs
    parameters: dict          # planet_radius_rearth, etc.
    plots: List[str]          # paths to generated PNG files
```

---

## 4. Data Flow

```
1. User drags .npz file onto UploadZone
2. Frontend calls POST /api/upload with file
3. Backend validates, saves to /tmp/{job_id}/, parses columns
4. Frontend shows preview table + column mapping
5. Frontend calls POST /api/process/{job_id}
6. Backend runs pipeline modules sequentially
7. Backend returns result JSON + plot file references  
8. Frontend renders ResultsDashboard with charts
9. User clicks "Download All" → GET /api/download/{job_id}?format=zip
10. Backend zips all plot PNGs + metrics.json → user downloads
```

---

## 5. File Structure

```
interactive_demo/
├── frontend/                    # Next.js app
│   ├── app/
│   │   ├── layout.tsx           # Root layout (Inter font, body styles)
│   │   ├── page.tsx             # Single page (upload → process → results)
│   │   └── globals.css          # Tailwind + Chroma theme variables
│   ├── components/
│   │   ├── Navbar.tsx
│   │   ├── Hero.tsx
│   │   ├── UploadZone.tsx
│   │   ├── PreviewTable.tsx
│   │   ├── ProgressStepper.tsx
│   │   ├── ResultsDashboard.tsx
│   │   ├── MetricCard.tsx
│   │   ├── ChartCard.tsx        # Wrapper for Plotly charts
│   │   ├── VerdictBadge.tsx
│   │   └── Footer.tsx
│   ├── lib/
│   │   ├── api.ts               # fetch wrappers for all endpoints
│   │   └── types.ts             # TypeScript types for API responses
│   └── public/
│       ├── chroma-logo.svg
│       └── favicon.ico
│
├── backend/                     # FastAPI service
│   ├── main.py                  # FastAPI app with 5 endpoints
│   ├── models.py                # Pydantic models
│   ├── handlers.py              # Upload, processing, download logic
│   └── requirements.txt         # fastapi, uvicorn, pandas, numpy, etc.
│
└── pipeline/                    # Reused from existing pipeline modules
    ├── __init__.py
    ├── step1_preprocess.py
    ├── step2_period.py
    ├── step3_features.py
    ├── step4_classifier.py
    ├── step5_params.py
    ├── step6_viz.py
    └── pipeline.py              # run_pipeline() orchestrator
```

---

## 6. Performance Requirements

| Metric | Target |
|--------|--------|
| Upload time (100 MB) | < 2 seconds (local network) |
| Processing time (10K pts) | < 30 seconds |
| Chart render time | < 500ms per chart |
| Initial page load (cold) | < 3 seconds |
| Total bundle size (JS) | < 500 KB gzipped |

---

## 7. Error Handling

- Backend returns structured errors: `{ "error": true, "code": "INVALID_FORMAT", "message": "...", "suggestion": "..." }`
- Frontend shows inline toasts (position: top-right, auto-dismiss 5s)
- All API calls wrapped in try/catch with user-friendly fallback messages
- Pipeline errors don't crash the server — each step catches and reports

---

## 8. Dependencies

### Backend
```
fastapi>=0.110
uvicorn[standard]>=0.27
python-multipart>=0.0.9
pandas>=2.0
numpy>=1.26
torch>=2.0
lightkurve>=2.0
astropy>=5.0
```

### Frontend
```json
{
  "next": "^14.2",
  "react": "^18.3",
  "react-dom": "^18.3",
  "react-plotly.js": "^2.6",
  "plotly.js-dist-min": "^2.30",
  "react-dropzone": "^14.2",
  "zustand": "^4.5",
  "tailwindcss": "^4.0",
  "next-themes": "^0.3"
}
```
