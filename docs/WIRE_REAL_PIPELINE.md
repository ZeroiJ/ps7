# Wire Real Pipeline — AI Agent Handoff

## Mission
Replace the mock pipeline in the backend with the real exoplanet transit pipeline. The uploaded file (CSV/JSON/NPZ) must be actually processed through TLS (Transit Least Squares), feature extraction, classification, and parameter estimation — not simulated.

## Success Criteria
- [ ] Upload a real TESS `.npz` file → frontend shows **actual** TLS periodogram with a real peak
- [ ] Upload a CSV with time+flux columns → same real processing
- [ ] "Try sample" downloads a real NPZ from backend and processes it
- [ ] All 4 charts show real data (not sine waves)
- [ ] Numbers change when you upload different targets
- [ ] Depth displays in ppm in frontend (frontend displays `tls_result.depth` with `unit="ppm"`)
- [ ] Processing time < 30s for 20K points on Render

---

## File Inventory

### To COPY from source repo to target repo

| Source File | Destination | Purpose |
|-------------|------------|---------|
| `pipeline/step1_preprocess.py` | `ps7/pipeline/step1_preprocess.py` | Load NPZ/CSV, clean, detrend |
| `pipeline/step2_tls.py` | `ps7/pipeline/step2_tls.py` | Transit Least Squares period detection |
| `pipeline/step3_features.py` | `ps7/pipeline/step3_features.py` | Extract 11 features |
| `pipeline/step4_classifier.py` | `ps7/pipeline/step4_classifier.py` | Heuristic + known-planet classifier |
| `pipeline/step5_params.py` | `ps7/pipeline/step5_params.py` | Kepler's law → planet radius, temp |
| `pipeline/step6_visualize.py` | `ps7/pipeline/step6_visualize.py` | Matplotlib plots (PNG) |
| `pipeline/__init__.py` | `ps7/pipeline/__init__.py` | Exports `run_pipeline()` |
| `data/sample_light_curves/*.npz` | `ps7/backend/sample_data/` | Real TOI light curves for sample |

### To CREATE in target repo

| File | Purpose |
|------|---------|
| `backend/real_pipeline.py` | Bridge: loads file → runs pipeline → reshapes to frontend schema |
| `backend/sample_data/` | Directory with real NPZ files for "Try sample" |

### To DELETE in target repo

| File | Reason |
|------|--------|
| `backend/mock_pipeline.py` | Replaced by `real_pipeline.py` |

### To MODIFY in target repo

| File | Change |
|------|--------|
| `backend/main.py` | Replace `from mock_pipeline import run_mock_pipeline` with `from real_pipeline import run_real_pipeline`. Update `process_file()` endpoint. Update `get_sample_data()` endpoint. |
| `backend/requirements.txt` | Add: `transitleastsquares`, `lightkurve`, `astropy`, `scipy`, `matplotlib`, `torch` |

---

## Bridge Layer: `backend/real_pipeline.py`

This is the critical file. It must:
1. Accept a file path and filename
2. Load the data (handling CSV, JSON, NPZ)
3. Call the real pipeline steps
4. Transform the output into the exact `PipelineResult` schema the frontend expects
5. Return chart data as JSON-serializable arrays (not PNG paths)

### Input → Output Contract

```
Input:  file_path (str), filename (str)
Output: dict matching PipelineResult (see schema below)
```

### Loading Logic (handle all 3 formats)

```python
import pandas as pd
import numpy as np
from pathlib import Path

def load_file(file_path: str, filename: str) -> tuple[np.ndarray, np.ndarray]:
    """Load time and flux arrays from any supported format."""
    ext = Path(filename).suffix.lower()
    
    if ext == ".csv":
        df = pd.read_csv(file_path)
        # Find time and flux columns (look for common names)
        time_col = next((c for c in df.columns if c.lower() in ("time", "t", "btjd", "jd")), df.columns[0])
        flux_col = next((c for c in df.columns if c.lower() in ("flux", "f", "flux_raw", "pdcsap_flux")), df.columns[1])
        time = df[time_col].values.astype(np.float64)
        flux = df[flux_col].values.astype(np.float64)
        
    elif ext == ".json":
        with open(file_path) as f:
            data = json.load(f)
        # Handle both list-of-dicts and dict-of-arrays
        if isinstance(data, dict):
            time = np.array(data.get("time", data.get("t", []))).astype(np.float64)
            flux = np.array(data.get("flux", data.get("f", []))).astype(np.float64)
        else:
            time = np.array([d.get("time", d.get("t")) for d in data]).astype(np.float64)
            flux = np.array([d.get("flux", d.get("f")) for d in data]).astype(np.float64)
            
    elif ext == ".npz":
        npz = np.load(file_path, allow_pickle=False)
        # Prioritize common key names
        time = npz.get("time", npz.get("t", npz[list(npz.files)[0]])).astype(np.float64)
        flux = npz.get("flux", npz.get("f", npz[list(npz.files)[1]])).astype(np.float64)
        
    else:
        raise ValueError(f"Unsupported format: {ext}")
    
    # Flatten to 1D
    time = np.asarray(time).ravel()
    flux = np.asarray(flux).ravel()
    
    return time, flux
```

### Pipeline Execution

```python
from pipeline import (
    load_raw_and_clean,   # ONLY use for cleaning, NOT for loading from file
    find_period,
    extract_features,
    classify,
    estimate_parameters,
)

def run_real_pipeline(file_path: str, filename: str) -> dict:
    """
    Run the real 6-step pipeline on an uploaded file.
    
    Returns dict matching PipelineResult schema.
    """
    import numpy as np
    
    # STEP 0: Load raw data from uploaded file
    raw_time, raw_flux = load_file(file_path, filename)
    target_name = Path(filename).stem
    
    # Clean and detrend (reuse step1 cleaning logic)
    # Remove NaN
    valid = np.isfinite(raw_time) & np.isfinite(raw_flux)
    t, f = raw_time[valid], raw_flux[valid]
    
    # Sigma clip
    med, std = np.median(f), np.std(f)
    mask = np.abs(f - med) <= 3 * std
    t, f = t[mask], f[mask]
    
    # Savitzky-Golay detrend
    from scipy.signal import savgol_filter
    window = min(101, len(f) - 1)
    if window % 2 == 0: window -= 1
    if window >= 5:
        trend = savgol_filter(f, window, polyorder=3)
        f_detrended = f / trend
    else:
        f_detrended = f / med
    flux_clean = f_detrended / np.median(f_detrended)
    
    # STEP 1: TLS
    from pipeline.step2_tls import find_period
    tls_result = find_period(t, flux_clean)
    
    # STEP 2: Features
    from pipeline.step3_features import extract_features
    features = extract_features(t, flux_clean, tls_result)
    
    # STEP 3: Classify
    from pipeline.step4_classifier import classify
    classification = classify(features, target_name=target_name)
    
    # STEP 4: Parameters
    from pipeline.step5_params import estimate_parameters
    params = estimate_parameters(tls_result)
    
    # STEP 5: Build response
    return build_response(target_name, raw_time, raw_flux, t, flux_clean,
                          tls_result, features, classification, params)
```

### Response Builder (CRITICAL — must match frontend schema exactly)

```python
def build_response(target_name, raw_time, raw_flux, time, flux,
                   tls_result, features, classification, params):
    """Build the PipelineResult dict matching frontend types.ts exactly."""
    
    n_points = len(time)
    
    # --- Preprocessed ---
    preprocessed = {
        "n_points": n_points,
        "n_points_raw": len(raw_time),
        "time_span": round(float(time[-1] - time[0]), 2),
        "flux_median": round(float(np.median(flux)), 6),
        "flux_std": round(float(np.std(flux)), 6),
        "flux_range": [round(float(np.min(flux)), 6), round(float(np.max(flux)), 6)],
        "outliers_removed": len(raw_time) - n_points,
    }
    
    # --- TLS Result ---
    # IMPORTANT: depth must be in ppm (1 = 1,000,000 ppm) for frontend display
    period = float(tls_result.get("period", 0))
    depth_frac = 1.0 - float(tls_result.get("depth", 1.0))  # fractional depth
    depth_ppm = round(depth_frac * 1_000_000, 1)  # convert to ppm
    duration_hrs = round(float(tls_result.get("duration", 0)) * 24, 3)
    snr_val = round(float(tls_result.get("snr", 0)), 2)
    sde_val = round(float(tls_result.get("sde", 0)), 1)
    
    tls_out = {
        "period": round(period, 6),
        "sde": sde_val,
        "depth": depth_ppm,         # <-- frontend shows this with unit="ppm"
        "duration": duration_hrs,    # <-- frontend shows this (hours)
        "snr": snr_val,
        "t0": round(float(tls_result.get("t0", 0)), 4),
    }
    
    # --- Features ---
    phys = features.get("physics", np.zeros(5))
    stats = features.get("stats", np.zeros(4))
    diag = features.get("diagnostics", np.zeros(2))
    
    features_out = {
        "physics": [round(float(x), 4) for x in phys],
        "stats": [round(float(x), 4) for x in stats],
        "diagnostics": [round(float(x), 4) for x in diag],
    }
    
    # --- Classification ---
    class_probs = classification.get("class_probs", [0.25]*4)
    if isinstance(class_probs, np.ndarray):
        class_probs = class_probs.tolist()
    class_names = ["planet", "eclipsing_binary", "blend", "false_positive"]
    
    classification_out = {
        "predicted_class": classification.get("predicted_class", "false_positive"),
        "confidence": round(float(classification.get("confidence", 0)), 4),
        "class_probs": dict(zip(class_names, class_probs)),
    }
    
    # --- Parameters ---
    params_out = {
        "planet_radius_rearth": round(float(params.get("planet_radius_rearth", 0)), 2),
        "semi_major_axis_au": round(float(params.get("orbital_distance", 0)), 4),
        "equilibrium_temp_k": int(round(float(params.get("equilibrium_temperature", 0)))),
        "orbital_period_days": round(period, 4),
        "transit_depth_ppm": depth_ppm,
        "duration_hrs": duration_hrs,
    }
    
    # --- PLOTS (JSON chart data) ---
    # raw flux (use raw data before cleaning)
    plots = {
        "raw_flux": {
            "time": raw_time.tolist(),
            "flux": raw_flux.tolist(),
        },
        "cleaned_flux": {
            "time": time.tolist(),
            "flux": flux.tolist(),
        },
    }
    
    # Periodogram: frontend expects {frequency, power}
    # frequency = 1/period (TLS returns periods array)
    periods_arr = tls_result.get("periods", np.array([]))
    power_arr = tls_result.get("power", np.array([]))
    if len(periods_arr) > 0 and len(power_arr) > 0:
        frequency = (1.0 / periods_arr).tolist()
        power = power_arr.tolist()
    else:
        frequency = []
        power = []
    plots["periodogram"] = {"frequency": frequency, "power": power}
    
    # Folded curve: {phase, flux, model}
    folded_phase = tls_result.get("folded_time", np.array([]))
    folded_flux = tls_result.get("folded_flux", np.array([]))
    folded_model = tls_result.get("folded_model", np.array([]))
    
    if len(folded_phase) > 0:
        # Sort by phase for clean rendering
        sort_idx = np.argsort(folded_phase)
        plots["folded_curve"] = {
            "phase": folded_phase[sort_idx].tolist(),
            "flux": folded_flux[sort_idx].tolist(),
            "model": folded_model[sort_idx].tolist() if len(folded_model) == len(folded_phase) else [],
        }
    else:
        plots["folded_curve"] = {"phase": [], "flux": [], "model": []}
    
    # Classification bars: {classes, probabilities}
    plots["classification_bars"] = {
        "classes": class_names,
        "probabilities": class_probs if isinstance(class_probs, list) else class_probs.tolist(),
    }
    
    # --- Assemble ---
    return {
        "target_name": target_name,
        "preprocessed": preprocessed,
        "tls_result": tls_out,
        "features": features_out,
        "classification": classification_out,
        "parameters": params_out,
        "plots": plots,
    }
```

---

## Changes to `backend/main.py`

### 1. Replace imports at top of file
```python
# DELETE this:
from mock_pipeline import run_mock_pipeline

# ADD this:
from real_pipeline import run_real_pipeline
```

### 2. Update `process_file()` endpoint
The current endpoint calls `run_mock_pipeline(file_path, filename)`. Replace the call:

```python
# Delete the old call:
# result_dict = run_mock_pipeline(file_path, filename)

# Add:
result_dict = run_real_pipeline(file_path, filename)
```

Keep the rest of the endpoint unchanged (job_store update, response serialization).

### 3. Update `get_sample_data()` endpoint
Currently the sample endpoint returns mock data. Change it to return a real NPZ file:

```python
@app.get("/api/sample-data")
async def get_sample_data(target: str = "TOI-270"):
    """Return a pre-packaged real TESS light curve as an upload."""
    sample_dir = Path(__file__).resolve().parent / "sample_data"
    
    # Map target names to filenames
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
    
    # Simulate an upload by creating a temp copy and registering a job
    import shutil
    job_id = str(uuid.uuid4())
    ext = ".npz"
    save_path = TEMP_DIR / f"{job_id}{ext}"
    save_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(filepath, save_path)
    
    # Parse and return preview (same logic as upload endpoint)
    npz = np.load(save_path, allow_pickle=False)
    columns = list(npz.files)
    shapes = {k: list(npz[k].shape) for k in columns}
    rows = shapes[columns[0]][0] if columns else 0
    preview = [{"array": k, "shape": shapes[k],
                "first_5": npz[k].flat[:5].tolist()} for k in columns]
    
    job_store[job_id] = {
        "status": "uploaded",
        "file_path": str(save_path),
        "filename": filename,
    }
    
    return {
        "job_id": job_id,
        "filename": filename,
        "rows": rows,
        "columns": columns,
        "preview": preview,
        "message": "Sample data loaded",
    }
```

### 4. Add CORS for sample-data
The frontend calls `getSampleData()` as a `POST` to `/api/sample-data` (see `frontend/lib/api.ts`). Update the route decorator to also accept POST:

```python
@app.get("/api/sample-data")
@app.post("/api/sample-data")   # <-- ADD this line for frontend compatibility
async def get_sample_data(target: str = "TOI-270"):
```

---

## Updates to `backend/requirements.txt`

Add these dependencies (keep existing ones):
```
transitleastsquares>=1.32
lightkurve>=2.4
astropy>=5.0
scipy>=1.11
matplotlib>=3.7
torch>=2.0
```

---

## Sample Data Setup

Copy the 5 real NPZ files from the source repo:

```bash
cp /path/to/source/data/sample_light_curves/TOI_*.npz backend/sample_data/
```

Each file contains:
- `time`: float64 array (TESS BTJD time in days)
- `flux`: float64 array (flux in e-/s)
- `flux_err`: float64 array
- `quality`: int32 array (quality flags)
- `sector`: int32 (TESS sector number)
- `target_name`: string

---

## Edge Cases & Important Notes

### When TLS Returns SDE < 8 (no detection)
- `find_period()` still returns a result with real period, SDE etc.
- `run_tls_search()` (the wrapper) returns `{}` if SDE < 8 — DO NOT USE IT
- Always use `find_period()` directly so you get periodogram data
- The classifier will return low confidence if SDE is weak
- The frontend still renders charts; they'll just show low signal

### NPZ Key Names
In the sample NPZ files keys are: `time`, `flux`, `flux_err`, `quality`, `sector`, `target_name`, `description`. When users upload their own NPZ files, they might have different key names. The load function handles this by trying common variants (`time`, `t`, `btjd`, etc.).

### Depth Conversion
- Pipeline stores depth as `1.0 - tls_result["depth"]` (fractional depth)
- `tls_result["depth"]` from TLS is the minimum of the transit (0.999 = no transit, 0.99 = 1% dip)
- So `1.0 - depth = 0.001` = 0.1% = 1000 ppm
- Frontend shows `tls_result.depth` with `unit="ppm"` — so pass depth in ppm

### Memory Limits on Render
- Free tier has 512 MB RAM
- A 100 MB NPZ file decompresses to ~400 MB of float64 arrays — this might OOM
- TLS on 100K+ points takes significant memory
- **Suggestion**: Add a file point limit in `real_pipeline.py`:
  ```python
  MAX_POINTS = 100_000
  if len(time) > MAX_POINTS:
      # Subsample or reject
      indices = np.linspace(0, len(time)-1, MAX_POINTS).astype(int)
      time = time[indices]
      flux = flux[indices]
  ```

### Processing Time
- TLS on 13K points takes ~10s on Render free tier
- The frontend polls every 2s for up to 60 attempts (120s timeout)
- This is sufficient for data up to ~50K points

### "Try Sample" Button Flow
1. Frontend calls `POST /api/sample-data`
2. Backend copies a real NPZ file to temp, registers a job, returns it
3. Frontend shows preview table with array keys
4. User clicks "Start Analysis" → calls `POST /api/process/{job_id}`
5. Backend runs `run_real_pipeline()` on the NPZ copy
6. Results display with real TLS data

---

## Files NOT to Modify

| File | Reason |
|------|--------|
| `frontend/app/components/*` | Already wired to accept PipelineResult |
| `frontend/app/lib/api.ts` | Already calls correct endpoints |
| `frontend/app/lib/types.ts` | Defines the schema — keep as-is |
| `frontend/app/lib/store.ts` | State management — keep as-is |
| `frontend/next.config.ts` | Cloudflare static export config |
| `frontend/tailwind.config.ts` | Style config — keep as-is |
| `vercel.json` (root) | Deployment config — keep as-is |

---

## Verification Checklist

After implementation, test each scenario:

- [ ] **Try Sample (TOI-270)**: Shows "PLANET" with >90% confidence (known planet), periodogram has a peak
- [ ] **Try Sample (TOI-700)**: Similar, different period value
- [ ] **Upload NPZ file**: Loads, shows preview with array keys, processes correctly
- [ ] **Upload CSV file**: time+flux columns detected, processed correctly
- [ ] **Upload nonsense file**: Shows error toast with clear message
- [ ] **Depth in ppm**: Frontend shows values like "84.2 ppm" not "0.0000842"
- [ ] **Charts render**: All 4 Plotly charts show actual data points
- [ ] **Download All**: Produces a zip with content
- [ ] **Processing time**: <30s for standard files
