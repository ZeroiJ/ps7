"""ExoVetter Data API — FastAPI backend for exoplanet transit vetting.

Endpoints
---------
POST /api/upload         Upload a light-curve file (.csv, .json, .npz)
POST /api/process/{id}   Run the (simulated) vetting pipeline
GET  /api/sample-data    Get a built-in sample dataset
GET  /api/status/{id}    Poll processing status
GET  /api/download/{id}  Download results as a ZIP archive
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pathlib import Path
import uuid
import json
import io
import zipfile
import tempfile
import textwrap

import pandas as pd
import numpy as np

from models import UploadResponse, ProcessResponse, ErrorResponse, PipelineResult
from mock_pipeline import run_mock_pipeline

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------
app = FastAPI(
    title="ExoVetter Data API",
    version="0.1.0",
    description="Backend for the ExoVetter exoplanet candidate vetting web app.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

TEMP_DIR = Path(tempfile.gettempdir()) / "exovetter_jobs"
TEMP_DIR.mkdir(exist_ok=True)

MAX_UPLOAD_BYTES = 200 * 1024 * 1024  # 200 MB
ALLOWED_EXTENSIONS = {".csv", ".json", ".npz"}

# In-memory job store  {job_id: {"status": ..., "result": ..., "filename": ...}}
job_store: dict = {}


# ---------------------------------------------------------------------------
# Error helpers
# ---------------------------------------------------------------------------

def _error(status: int, code: str, message: str,
           suggestion: str | None = None) -> JSONResponse:
    """Return a structured error response."""
    body = ErrorResponse(
        code=code,
        message=message,
        suggestion=suggestion,
    ).model_dump()
    return JSONResponse(status_code=status, content=body)


# ---------------------------------------------------------------------------
# 1. POST /api/upload
# ---------------------------------------------------------------------------

@app.post("/api/upload", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...)):
    """Accept a multipart file upload (.csv, .json, .npz)."""

    # --- Extension check ---
    filename = file.filename or "unknown"
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        return _error(
            400, "INVALID_FILE_TYPE",
            f"Unsupported file type '{ext}'.",
            f"Please upload one of: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )

    # --- Read contents & size check ---
    contents = await file.read()
    if len(contents) == 0:
        return _error(
            400, "EMPTY_FILE",
            "The uploaded file is empty.",
            "Make sure the file contains light-curve data before uploading.",
        )
    if len(contents) > MAX_UPLOAD_BYTES:
        return _error(
            413, "FILE_TOO_LARGE",
            f"File size ({len(contents) / 1e6:.1f} MB) exceeds the 200 MB limit.",
            "Try trimming the dataset or compressing it as .npz.",
        )

    # --- Save to disk ---
    job_id = uuid.uuid4().hex[:12]
    save_path = TEMP_DIR / f"{job_id}{ext}"
    save_path.write_bytes(contents)

    # --- Parse preview ---
    try:
        rows, columns, preview = _parse_preview(save_path, ext, contents)
    except Exception as exc:
        save_path.unlink(missing_ok=True)
        return _error(
            422, "PARSE_ERROR",
            f"Could not parse the uploaded file: {exc}",
            "Check that the file is a valid CSV/JSON/NPZ with numerical data.",
        )

    # --- Register job ---
    job_store[job_id] = {
        "status": "uploaded",
        "filename": filename,
        "file_path": str(save_path),
    }

    return UploadResponse(
        job_id=job_id,
        filename=filename,
        rows=rows,
        columns=columns,
        preview=preview,
        message=f"File '{filename}' uploaded successfully ({rows} rows).",
    )


def _parse_preview(path: Path, ext: str, raw_bytes: bytes):
    """Return (row_count, column_names, preview_rows) for supported formats."""

    if ext == ".csv":
        df = pd.read_csv(path)
        if df.empty:
            raise ValueError("CSV file contains no data rows")
        rows = len(df)
        columns = df.columns.tolist()
        preview = df.head(5).replace({np.nan: None}).to_dict(orient="records")

    elif ext == ".json":
        data = json.loads(raw_bytes)
        if isinstance(data, list):
            rows = len(data)
            columns = list(data[0].keys()) if rows > 0 else []
            preview = data[:5]
        elif isinstance(data, dict):
            # Treat top-level keys as columns, values as arrays
            columns = list(data.keys())
            first_len = len(next(iter(data.values()))) if data else 0
            rows = first_len
            preview = [
                {k: (v[i] if i < len(v) else None) for k, v in data.items()}
                for i in range(min(5, first_len))
            ]
        else:
            raise ValueError("JSON must be a list of objects or a dict of arrays")

    elif ext == ".npz":
        npz = np.load(path, allow_pickle=False)
        columns = list(npz.files)
        shapes = {k: list(npz[k].shape) for k in columns}
        rows = shapes[columns[0]][0] if columns else 0
        # Preview: show first 5 values per array
        preview = [
            {k: npz[k][:5].tolist() if npz[k].ndim >= 1 else [float(npz[k])]}
            for k in columns
        ]
        # Reshape preview to row-oriented for consistency
        preview = [{"array": k, "shape": shapes[k],
                     "first_5": npz[k].flat[:5].tolist()} for k in columns]

    else:
        raise ValueError(f"Unsupported extension: {ext}")

    return rows, columns, preview


# ---------------------------------------------------------------------------
# 2. POST /api/process/{job_id}
# ---------------------------------------------------------------------------

@app.post("/api/process/{job_id}", response_model=ProcessResponse)
async def process_file(job_id: str):
    """Run the vetting pipeline on a previously uploaded file."""

    if job_id not in job_store:
        return _error(404, "JOB_NOT_FOUND",
                      f"No job with id '{job_id}' exists.",
                      "Upload a file first via POST /api/upload.")

    job = job_store[job_id]
    file_path = job.get("file_path", "")
    filename = job.get("filename", "unknown")

    if not Path(file_path).exists():
        return _error(404, "FILE_MISSING",
                      "The uploaded file is no longer available on disk.",
                      "Please re-upload the file.")

    # Mark as processing
    job["status"] = "processing"

    try:
        result_dict = run_mock_pipeline(file_path, filename)
    except Exception as exc:
        job["status"] = "error"
        job["error"] = str(exc)
        return ProcessResponse(status="error", error=str(exc))

    job["status"] = "done"
    job["result"] = result_dict

    return ProcessResponse(
        status="done",
        result=PipelineResult(**result_dict),
    )


# ---------------------------------------------------------------------------
# 3. GET /api/sample-data
# ---------------------------------------------------------------------------

@app.get("/api/sample-data", response_model=UploadResponse)
async def sample_data():
    """Generate and return a built-in sample dataset (TOI-270 style)."""

    rng = np.random.default_rng(42)
    n = 1200
    time = np.sort(rng.uniform(0, 27.4, n))
    period = 5.66
    phase = ((time % period) / period + 0.5) % 1.0 - 0.5

    flux = np.ones(n)
    in_transit = np.abs(phase) < 0.02
    flux[in_transit] -= 0.0012
    flux += rng.normal(0, 0.0003, n)
    flux_err = np.full(n, 0.0003) + rng.uniform(0, 0.0001, n)

    df = pd.DataFrame({
        "time": np.round(time, 6),
        "flux": np.round(flux, 6),
        "flux_err": np.round(flux_err, 6),
    })

    job_id = uuid.uuid4().hex[:12]
    save_path = TEMP_DIR / f"{job_id}.csv"
    df.to_csv(save_path, index=False)

    filename = "toi_270_sample.csv"
    job_store[job_id] = {
        "status": "uploaded",
        "filename": filename,
        "file_path": str(save_path),
    }

    preview = df.head(5).to_dict(orient="records")

    return UploadResponse(
        job_id=job_id,
        filename=filename,
        rows=n,
        columns=["time", "flux", "flux_err"],
        preview=preview,
        message="Sample TOI-270 light curve loaded (1200 cadences, 27.4 days).",
    )


# ---------------------------------------------------------------------------
# 4. GET /api/status/{job_id}
# ---------------------------------------------------------------------------

@app.get("/api/status/{job_id}")
async def get_status(job_id: str):
    """Check the current processing status of a job."""

    if job_id not in job_store:
        return _error(404, "JOB_NOT_FOUND",
                      f"No job with id '{job_id}' exists.",
                      "Upload a file first via POST /api/upload.")

    job = job_store[job_id]
    status = job.get("status", "unknown")

    payload: dict = {"status": status, "job_id": job_id}

    if status == "done" and "result" in job:
        payload["result_available"] = True
    if status == "error":
        payload["error"] = job.get("error", "Unknown error")

    return payload


# ---------------------------------------------------------------------------
# 5. GET /api/download/{job_id}
# ---------------------------------------------------------------------------

@app.get("/api/download/{job_id}")
async def download_results(job_id: str):
    """Download pipeline results as a ZIP archive."""

    if job_id not in job_store:
        return _error(404, "JOB_NOT_FOUND",
                      f"No job with id '{job_id}' exists.",
                      "Upload and process a file first.")

    job = job_store[job_id]

    if job.get("status") != "done" or "result" not in job:
        return _error(409, "NOT_PROCESSED",
                      "Pipeline has not finished for this job.",
                      "Call POST /api/process/{job_id} first and wait for status 'done'.")

    result = job["result"]
    target = result.get("target_name", job_id)

    # --- Build ZIP in memory ---
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:

        # metrics.json — everything except bulky plot arrays
        metrics = {k: v for k, v in result.items() if k != "plots"}
        zf.writestr("metrics.json", json.dumps(metrics, indent=2))

        # summary.txt — human-readable report
        cls = result.get("classification", {})
        tls = result.get("tls_result", {})
        params = result.get("parameters", {})
        pre = result.get("preprocessed", {})

        summary = textwrap.dedent(f"""\
            ExoVetter Analysis Report
            =========================
            Target: {target}
            Job ID: {job_id}

            Preprocessing
            -------------
            Data points (raw → clean): {pre.get('n_points_raw', '?')} → {pre.get('n_points', '?')}
            Time span: {pre.get('time_span', '?')} days
            Flux median: {pre.get('flux_median', '?')}
            Outliers removed: {pre.get('outliers_removed', '?')}

            Transit Search (TLS)
            --------------------
            Period: {tls.get('period', '?')} days
            SDE:    {tls.get('sde', '?')}
            Depth:  {tls.get('depth', '?')} ppm
            Duration: {tls.get('duration', '?')} hrs
            SNR:    {tls.get('snr', '?')}

            Classification
            --------------
            Predicted class: {cls.get('predicted_class', '?')}
            Confidence:      {cls.get('confidence', '?')}
            Probabilities:   {cls.get('class_probs', {})}

            Derived Parameters
            ------------------
            Planet radius:      {params.get('planet_radius_rearth', '?')} R⊕
            Semi-major axis:    {params.get('semi_major_axis_au', '?')} AU
            Equilibrium temp:   {params.get('equilibrium_temp_k', '?')} K
            Transit depth:      {params.get('transit_depth_ppm', '?')} ppm
        """)
        zf.writestr("summary.txt", summary)

    buf.seek(0)
    zip_filename = f"exovetter_{target.replace(' ', '_')}_{job_id}.zip"

    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{zip_filename}"'},
    )


# ---------------------------------------------------------------------------
# Global exception handler
# ---------------------------------------------------------------------------

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return _error(
        500, "INTERNAL_ERROR",
        f"An unexpected error occurred: {exc}",
        "Please try again or contact support.",
    )
