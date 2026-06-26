# AI Agent Handoff Checklist

Give this checklist to your AI agent after it reads `WIRE_REAL_PIPELINE.md`.

## Order of Operations

### Step 1 — Setup (5 min)
- [x] Copy 6 pipeline `.py` files from source to `ps7/pipeline/`
- [x] Copy 5 NPZ files to `ps7/backend/sample_data/`
- [x] Delete `ps7/backend/mock_pipeline.py`
- [x] Update `ps7/backend/requirements.txt` (add transitleastsquares, lightkurve, etc.)

### Step 2 — Write bridge (30 min)
- [x] Create `ps7/backend/real_pipeline.py` with `load_file()` + `run_real_pipeline()` + `build_response()`
- [x] Follow the exact `build_response()` code — field names must match frontend types
- [x] Double-check depth is in ppm, frequency = 1/period

### Step 3 — Update main.py (15 min)
- [x] Replace import (`mock_pipeline` → `real_pipeline`)
- [x] Update `process_file()` to call `run_real_pipeline()`
- [x] Update `get_sample_data()` to serve real NPZ files
- [x] Add `@app.post("/api/sample-data")` for frontend compatibility

### Step 4 — Test locally (15 min)
- [x] Backend starts: `uvicorn main:app --reload --port 8000`
- [x] `curl POST /api/upload -F "file=@sample_data/TOI_270.npz"` returns valid JSON
- [x] `curl POST /api/process/{job_id}` returns `{status: "done", result: {...}}`
- [x] `curl GET /api/sample-data` returns a valid upload response
- [x] `curl GET /api/download/{job_id}` returns a zip

### Step 5 — Verify frontend integration (10 min)
- [ ] "Try sample" → shows preview → "Start Analysis" → 4 real charts render
- [ ] Periodogram shows actual TLS peak (not synthetic sine wave)
- [ ] Depth values are different for different targets
- [ ] Folded curve shows actual transit dip with red model overlay

### Step 6 — Deploy (10 min)
- [ ] Git add, commit, push
- [ ] Render auto-deploys backend (check build logs)
- [ ] Test live URL end-to-end

---

## Common Failure Points

| Symptom | Likely Cause |
|---------|-------------|
| Frontend shows "Processing failed" | Import error in real_pipeline.py — check the imports |
| Charts show no data | `tolist()` on empty array — check TLS returned results |
| Periodogram is blank | `frequency` key needs `1/periods` array, not `periods` |
| Depth shows 0 | Depth conversion: `depth_ppm = (1 - tls_depth) * 1e6` |
| "Try sample" returns error | Missing `@app.post("/api/sample-data")` decorator |
| Folded model line is missing | `folded_model` array needs to be sorted by phase same as flux |
| Build fails on Render | Missing system deps for transitleastsquares — add `gcc` to Render build |
