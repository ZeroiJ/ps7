# Implementation Plan — AI Builder Handoff

> **Audience**: Another AI agent that will build this from scratch
> **Priority**: Follow this exact order. Each phase must compile before starting the next.

---

## Phase 0 — Project Scaffolding (5 min)

```bash
# Frontend
npx create-next-app@latest frontend --typescript --tailwind --eslint
cd frontend
npm install react-plotly.js plotly.js-dist-min react-dropzone zustand next-themes

# Backend
mkdir backend && cd backend
python -m venv venv && source venv/bin/activate
pip install fastapi uvicorn python-multipart pandas numpy torch lightkurve astropy
```

**File check**: Ensure `frontend/` has `app/layout.tsx`, `app/page.tsx`, `tailwind.config.ts`, and `backend/` has `requirements.txt`.

---

## Phase 1 — Tailwind Config + Global CSS (10 min)

### tailwind.config.ts
Copy the full theme from [TRD.md §2.2](./TRD.md). Must include:
- `chroma-*` color tokens
- `fontFamily` with Inter + IBM Plex Mono
- `fontSize` scale matching Chroma
- `borderRadius.chroma`

### globals.css
```css
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&display=swap');

@tailwind base;
@tailwind components;
@tailwind utilities;

:root {
  --chroma-bg: #ffffff;
  --chroma-muted: #f6f6f6;
  --chroma-border: #e8e8e8;
  --chroma-fg: #070707;
  --chroma-muted-fg: #7b7b7b;
  --chroma-primary: #141414;
}
```

### layout.tsx
- Import Inter from `next/font/google`
- Apply Inter font to body
- HTML: `suppressHydrationWarning` (for next-themes)

---

## Phase 2 — Types + API Client (10 min)

### lib/types.ts
```typescript
export interface UploadResponse {
  job_id: string;
  filename: string;
  rows: number;
  columns: string[];
  preview: Record<string, unknown>[];
  message: string;
}

export interface PipelineResult {
  target_name: string;
  preprocessed: { n_points: number; time_span: number; flux_range: [number, number] };
  tls_result: { period: number; sde: number; depth: number; duration: number; snr: number };
  features: { physics: number[]; stats: number[]; diagnostics: number[] };
  classification: { predicted_class: string; confidence: number; class_probs: number[] };
  parameters: { planet_radius_rearth?: number; [key: string]: unknown };
  plots: string[];
}
```

### lib/api.ts
```typescript
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function uploadFile(file: File): Promise<UploadResponse> { ... }
export async function processFile(jobId: string): Promise<{status:string, result?:PipelineResult, error?:string}> { ... }
export async function getSampleData(target: string): Promise<File> { ... }
export async function downloadResults(jobId: string): Promise<Blob> { ... }
```

**Validation points**: TypeScript compiles. Each function makes a `fetch()` call with correct headers.

---

## Phase 3 — Components (Bottom-Up, 40 min)

Build in this order (each must render before the next):

### Phase 3a — Atomic Components
1. **`VerdictBadge.tsx`** — Pill-shaped badge: green "PLANET CONFIRMED" / yellow "CANDIDATE" / red "FALSE POSITIVE"
   - Props: `verdict: 'planet' | 'eb' | 'blend' | 'fp'`
   - Styled as: `inline-flex items-center px-3 py-1 rounded-full text-sm font-medium`

2. **`MetricCard.tsx`** — Single metric display
   - Props: `label: string, value: string | number, icon?: ReactNode`
   - Layout: flex row, icon (24px) on left, value+label stacked on right

3. **`ChartCard.tsx`** — Wrapper for Plotly chart
   - Props: `title: string, figure: Partial<PlotlyLayout>`
   - Basic: border, padding, title heading

4. **`ProgressStepper.tsx`** — 5-step progress indicator
   - Props: `currentStep: number, steps: string[]`
   - Horizontal layout, circles connected by lines
   - States: pending (gray), active (black + pulse), complete (black + check)

### Phase 3b — Composite Components
5. **`Navbar.tsx`** — Fixed top bar
   - Left: inline SVG logo (wordmark)
   - Right: dark mode toggle (sun/moon icon)
   - Height: 73px, border-bottom: 1px solid var(--chroma-border)
   - Transparent background

6. **`Hero.tsx`** — First section below navbar
   - H1: "Upload. Analyze. Discover."
   - P: "Drop a light curve and get instant transit analysis — no sign-up required."
   - Two buttons: "Upload your data" (primary) + "Try sample" (secondary)
   - Below buttons: stat strip (3 metrics)

7. **`UploadZone.tsx`** — Drag-and-drop file upload
   - States: empty → dragging → uploaded → preview
   - Empty: dashed border, icon, text
   - Dragging: border turns black, bg turns lighter
   - Uploaded: file name, size, type badge, row count
   - Preview: renders `PreviewTable` (first 5 rows)

8. **`PreviewTable.tsx`** — Scrollable table of uploaded data preview
   - Props: `columns: string[], rows: Record<string, unknown>[]`

9. **`ResultsDashboard.tsx`** — Main results view (the biggest component)
   - Verdict badge at top
   - 4 MetricCards in a row
   - 2×2 grid of ChartCards
   - Download button at bottom

### Phase 3c — Page Assembly
10. **`page.tsx`** — Single page assembling all components
    - State machine: `idle` → `uploading` → `previewing` → `processing` → `results` → `error`
    - zustand store for global state (file, jobId, results, step)

**Validation**: `npm run build` succeeds. Page renders without errors on `npm run dev`.

---

## Phase 4 — Backend API (30 min)

### main.py
```python
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import uuid, json

app = FastAPI(title="ExoVetter Data API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

TEMP_DIR = Path("/tmp/exovetter_jobs")
TEMP_DIR.mkdir(exist_ok=True)

# 5 endpoints: POST /api/upload, POST /api/process/{job_id}, 
# GET /api/sample-data, GET /api/status/{job_id}, GET /api/download/{job_id}
```

### handlers.py
- `handle_upload()` — file validation, save, parse, return preview
- `handle_process()` — run pipeline, catch errors, return result
- `handle_download()` — zip plots + metrics, return streaming response
- `handle_sample()` — return pre-packaged NPZ file

### models.py
- `UploadResponse`, `ProcessResponse`, `StatusResponse`, `ErrorResponse` (Pydantic)

**Validation**: `uvicorn main:app --reload` starts. `curl POST /api/upload -F "file=@test.npz"` returns JSON.

---

## Phase 5 — Integration (20 min)

1. Frontend calls backend on file drop
2. Show preview → user confirms → call process
3. Poll `/api/status/{job_id}` until done (or use single synchronous call)
4. Render results + charts
5. "Download All" button calls `/api/download/{job_id}`

**Checklist**:
- [ ] End-to-end: file upload → processing → charts rendered
- [ ] "Try sample" loads TOI-270 data
- [ ] Error state: upload a .txt file → see error toast
- [ ] Download produces a .zip with valid files

---

## Phase 6 — Polish (15 min)

1. **Dark mode**: Use `next-themes` ThemeProvider. Map colors to CSS variables in `globals.css`.
2. **Responsive**: Test on mobile (375px) — sections should stack vertically
3. **Loading states**: Add skeleton loaders while processing
4. **Edge cases**:
   - Empty CSV (no rows) → clear error
   - NPZ without time/flux keys → show column picker
   - File upload canceled mid-way → clean up temp file
5. **Performance**: Add `loading="lazy"` to images. Plotly charts use `responsive: true`.

---

## What NOT To Do

- ❌ No authentication / login system
- ❌ No database — everything is ephemeral (temp files)
- ❌ No SSR / ISR — static export (output: 'export' in next.config)
- ❌ Don't install any component library (shadcn, MUI, etc.) — Chroma style is raw Tailwind
- ❌ No loading spinners — use simple progress bar
- ❌ Don't animate on-scroll — everything is static on load
- ❌ Don't use emoji — Chroma doesn't use them
