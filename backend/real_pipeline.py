import json
from pathlib import Path
import numpy as np
import pandas as pd
from pipeline import (
    load_raw_and_clean,
    find_period,
    extract_features,
    classify,
    estimate_parameters,
)
from scipy.signal import savgol_filter

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


def run_real_pipeline(file_path: str, filename: str) -> dict:
    """
    Run the real 6-step pipeline on an uploaded file.
    
    Returns dict matching PipelineResult schema.
    """
    # STEP 0: Load raw data from uploaded file
    raw_time, raw_flux = load_file(file_path, filename)
    target_name = Path(filename).stem
    
    # Point limit for Render free tier memory issues
    MAX_POINTS = 50_000
    if len(raw_time) > MAX_POINTS:
        indices = np.linspace(0, len(raw_time)-1, MAX_POINTS).astype(int)
        raw_time = raw_time[indices]
        raw_flux = raw_flux[indices]

    # Clean and detrend
    # Remove NaN
    valid = np.isfinite(raw_time) & np.isfinite(raw_flux)
    t, f = raw_time[valid], raw_flux[valid]
    
    # Sigma clip
    med, std = np.median(f), np.std(f)
    mask = np.abs(f - med) <= 3 * std
    t, f = t[mask], f[mask]
    
    # Savitzky-Golay detrend
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
