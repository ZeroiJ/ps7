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
import shutil
import logging

import pandas as pd
import numpy as np

from models import UploadResponse, ProcessResponse, ErrorResponse, PipelineResult


# ---------------------------------------------------------------------------
# NaN-safe JSON encoder
# ---------------------------------------------------------------------------

class NanSafeEncoder(json.JSONEncoder):
    """Safe JSON encoder that handles NaN/Inf by converting them to null."""
    """Convert NaN / Inf to null so JSON serialisation never crashes."""
    def default(self, obj):
        if isinstance(obj, float) and (np.isnan(obj) or np.isinf(obj)):
            return None
        return super().default(obj)

    def encode(self, o):
        return super().encode(self._clean(o))

    def _clean(self, o):
        if isinstance(o, dict):
            return {k: self._clean(v) for k, v in o.items()}
        if isinstance(o, list):
            return [self._clean(v) for v in o]
        if isinstance(o, float):
            if np.isnan(o) or np.isinf(o):
                return None
            return o
        if hasattr(o, 'item'):
            return self._clean(o.item())
        return o


def json_dumps_safe(obj) -> str:
    """json.dumps with NaN→null protection."""
    return json.dumps(obj, cls=NanSafeEncoder)


def save_session(session_id, data):
    path = SESSIONS_DIR / f"{session_id}.json"
    path.write_text(json_dumps_safe(data))


# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------
# Override default JSON response to handle NaN/Inf safely
from fastapi.responses import JSONResponse as FastAPIJSONResponse

class SafeJSONResponse(FastAPIJSONResponse):
    def render(self, content):
        return json_dumps_safe(content).encode("utf-8")

app = FastAPI(
    title="ExoVetter Data API",
    version="0.1.0",
    description="Backend for the ExoVetter exoplanet candidate vetting web app.",
    default_response_class=SafeJSONResponse,
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

SESSIONS_DIR = Path(tempfile.gettempdir()) / "exovetter_sessions"
SESSIONS_DIR.mkdir(exist_ok=True)

def get_session(session_id):
    path = SESSIONS_DIR / f"{session_id}.json"
    if path.exists():
        return json.loads(path.read_text())
    return {"step": "upload", "files": {}, "results": {}}

# ---------------------------------------------------------------------------
# Error helpers
# ---------------------------------------------------------------------------

def _error(status: int, code: str, message: str,
           suggestion: str | None = None) -> JSONResponse:
    body = ErrorResponse(
        code=code,
        message=message,
        suggestion=suggestion,
    ).model_dump()
    return JSONResponse(status_code=status, content=body)

# ---------------------------------------------------------------------------
# 1. POST /api/step/upload — Upload & Preprocess
# ---------------------------------------------------------------------------

from real_pipeline import step1_preprocess, step2_tls, step3_classify, step4_features, step5_params, step6_output

@app.post("/api/step/upload")
async def step_upload(file: UploadFile = File(...)):
    filename = file.filename or "unknown"
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        return _error(400, "INVALID_FILE_TYPE", f"Unsupported file type '{ext}'.")

    contents = await file.read()
    if len(contents) == 0:
        return _error(400, "EMPTY_FILE", "The uploaded file is empty.")
    if len(contents) > MAX_UPLOAD_BYTES:
        return _error(413, "FILE_TOO_LARGE", "File size exceeds limit.")

    session_id = uuid.uuid4().hex[:12]
    save_path = TEMP_DIR / f"{session_id}{ext}"
    save_path.write_bytes(contents)

    try:
        res = step1_preprocess(str(save_path), filename)
    except Exception as exc:
        return _error(422, "PROCESS_ERROR", str(exc))

    # Save to session
    session_data = {
        "step": 1,
        "filename": filename,
        "file_path": str(save_path),
        "target_name": res["target_name"],
        "cleaned_time": res["cleaned_time"],
        "cleaned_flux": res["cleaned_flux"],
    }
    save_session(session_id, session_data)

    return {
        "session_id": session_id,
        "step": 1,
        "cleaned_flux_chart_data": {
            "raw_time": res["raw_time"],
            "raw_flux": res["raw_flux"],
            "cleaned_time": res["cleaned_time"],
            "cleaned_flux": res["cleaned_flux"],
        },
        "stats": res["preprocessed"]
    }

# ---------------------------------------------------------------------------
# 2. POST /api/step/tls — Run Transit Search
# ---------------------------------------------------------------------------

@app.post("/api/step/tls")
async def step_run_tls(request: Request):
    data = await request.json()
    session_id = data.get("session_id")
    session = get_session(session_id)
    
    if "cleaned_time" not in session:
        return _error(400, "SESSION_ERROR", "Invalid session or missing preprocessed data.")

    try:
        res = step2_tls(session["cleaned_time"], session["cleaned_flux"])
    except Exception as exc:
        return _error(500, "PROCESS_ERROR", str(exc))

    tls_res = res["tls_result"]
    session["tls_dict"] = tls_res
    session["step"] = 2
    save_session(session_id, session)

    return {
        "session_id": session_id,
        "step": 2,
        "period": tls_res["period"],
        "depth": tls_res["depth"],
        "snr": tls_res["snr"],
        "sde": tls_res["sde"],
        "duration": tls_res["duration"],
        "periodogram_chart_data": {
            "frequency": tls_res["periods"],
            "power": tls_res["power"],
        },
        "phase_fold_chart_data": {
            "phase": tls_res["folded_time"],
            "flux": tls_res["folded_flux"],
            "model": tls_res["folded_model"],
        }
    }

# ---------------------------------------------------------------------------
# 3. POST /api/step/features — Extract Features (Step 3)
# ---------------------------------------------------------------------------

@app.post("/api/step/features")
async def step_run_features(request: Request):
    data = await request.json()
    session_id = data.get("session_id")
    session = get_session(session_id)

    if "tls_dict" not in session:
        return _error(400, "SESSION_ERROR", "Missing TLS data. Run Transit Search first.")

    try:
        features = step4_features(
            session["cleaned_time"],
            session["cleaned_flux"],
            session["tls_dict"],
        )
    except Exception as exc:
        return _error(500, "PROCESS_ERROR", str(exc))

    session["features"] = features
    session["step"] = 3
    save_session(session_id, session)

    return {
        "session_id": session_id,
        "step": 3,
        "features": features,
    }

# ---------------------------------------------------------------------------
# 4. POST /api/step/classify — Classify (Step 4)
# ---------------------------------------------------------------------------

@app.post("/api/step/classify")
async def step_run_classify(request: Request):
    data = await request.json()
    session_id = data.get("session_id")
    session = get_session(session_id)

    if "features" not in session:
        if "tls_dict" not in session:
            return _error(400, "SESSION_ERROR", "Missing features data. Run Feature Extraction first.")
        features = step4_features(
            session["cleaned_time"],
            session["cleaned_flux"],
            session["tls_dict"],
        )
        session["features"] = features
    else:
        features = session["features"]

    from pipeline.step4_classifier import classify as classify_fn
    feat_dict = {
        "physics": features["physics"],
        "stats": features["stats"],
        "diagnostics": features["diagnostics"],
        "folded_curve": features.get("folded_curve", [1.0] * 2000),
    }
    classification = classify_fn(feat_dict, target_name=session["target_name"])

    session["classification"] = classification
    session["step"] = 4
    save_session(session_id, session)

    return {
        "session_id": session_id,
        "step": 4,
        "verdict": classification["predicted_class"],
        "confidence": classification["confidence"],
        "class_probs": classification["class_probs"],
    }

# ---------------------------------------------------------------------------
# 5. POST /api/step/parameters — Estimate Planet Parameters (Step 5)
# ---------------------------------------------------------------------------

@app.post("/api/step/parameters")
async def step_run_parameters(request: Request):
    data = await request.json()
    session_id = data.get("session_id")
    session = get_session(session_id)

    if "tls_dict" not in session:
        return _error(400, "SESSION_ERROR", "Missing TLS data. Run Transit Search first.")

    try:
        params = step5_params(session["tls_dict"])
    except Exception as exc:
        return _error(500, "PROCESS_ERROR", str(exc))

    session["parameters"] = params
    session["step"] = 5
    save_session(session_id, session)

    return {
        "session_id": session_id,
        "step": 5,
        "planet_radius_rearth": params["planet_radius_rearth"],
        "orbital_distance": params["orbital_distance"],
        "equilibrium_temperature": params["equilibrium_temperature"],
        "orbital_period_days": params["orbital_period_days"],
        "transit_depth_pct": params["transit_depth_pct"],
        "transit_duration_hours": params["transit_duration_hours"],
    }

# ---------------------------------------------------------------------------
# 6. POST /api/step/output — Final Assembly (Step 6)
# ---------------------------------------------------------------------------

@app.post("/api/step/output")
async def step_run_output(request: Request):
    data = await request.json()
    session_id = data.get("session_id")
    session = get_session(session_id)

    missing = [k for k in ("features", "classification", "parameters") if k not in session]
    if missing:
        return _error(400, "SESSION_ERROR", f"Missing data: {', '.join(missing)}. Complete earlier steps first.")

    try:
        result = step6_output(
            session["target_name"],
            session["cleaned_time"],
            session["cleaned_flux"],
            session["tls_dict"],
            session["features"],
            session["classification"],
            session["parameters"],
        )
    except Exception as exc:
        return _error(500, "PROCESS_ERROR", str(exc))

    session["final_result"] = result
    session["step"] = 6
    save_session(session_id, session)

    return {
        "session_id": session_id,
        "step": 6,
        "target_name": result["target_name"],
        "preprocessed": result["preprocessed"],
        "tls_result": result["tls_result"],
        "features": result["features"],
        "classification": result["classification"],
        "parameters": result["parameters"],
        "plots": result["plots"],
    }

# ---------------------------------------------------------------------------
# Sample Data Endpoint (Simulates step 1)
# ---------------------------------------------------------------------------
@app.get("/api/sample-data")
@app.post("/api/sample-data")
async def get_sample_data(target: str = "TOI-270"):
    sample_dir = Path(__file__).resolve().parent / "sample_data"
    sample_files = {
        "TOI-270": "TOI_270.npz",
        "TOI-700": "TOI_700.npz",
        "TOI-178": "TOI_178.npz",
        "TOI-1231": "TOI_1231.npz",
        "TOI-2180": "TOI_2180.npz",
    }
    filename = sample_files.get(target, "TOI_270.npz")
    filepath = sample_dir / filename
    
    if not filepath.exists():
        raise HTTPException(404, f"Sample data not found for {target}")
    
    session_id = uuid.uuid4().hex[:12]
    save_path = TEMP_DIR / f"{session_id}.npz"
    shutil.copy(filepath, save_path)
    
    try:
        res = step1_preprocess(str(save_path), filename)
    except Exception as exc:
        return _error(500, "PROCESS_ERROR", str(exc))

    session_data = {
        "step": 1,
        "filename": filename,
        "file_path": str(save_path),
        "target_name": res["target_name"],
        "cleaned_time": res["cleaned_time"],
        "cleaned_flux": res["cleaned_flux"],
    }
    save_session(session_id, session_data)

    return {
        "session_id": session_id,
        "step": 1,
        "cleaned_flux_chart_data": {
            "raw_time": res["raw_time"],
            "raw_flux": res["raw_flux"],
            "cleaned_time": res["cleaned_time"],
            "cleaned_flux": res["cleaned_flux"],
        },
        "stats": res["preprocessed"]
    }


# ---------------------------------------------------------------------------
# 5. GET /api/download/{job_id}
# ---------------------------------------------------------------------------

@app.get("/api/download/{job_id}")
async def download_results(job_id: str):
    """Download pipeline results as a ZIP archive."""
    session = get_session(job_id)
    if "final_result" not in session:
        return _error(409, "NOT_PROCESSED", "Pipeline has not finished for this job.")

    result = session["final_result"]
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
