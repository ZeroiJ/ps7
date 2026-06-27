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
        
        def get_npz_data(npz_obj, primary_key, secondary_key, default_index):
            if primary_key in npz_obj:
                return npz_obj[primary_key]
            elif secondary_key in npz_obj:
                return npz_obj[secondary_key]
            return npz_obj[list(npz_obj.files)[default_index]]
        
        time = get_npz_data(npz, "time", "t", 0).astype(np.float64)
        flux = get_npz_data(npz, "flux", "f", 1).astype(np.float64)
        
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


def step1_preprocess(file_path: str, filename: str) -> dict:
    raw_time, raw_flux = load_file(file_path, filename)
    target_name = Path(filename).stem
    
    MAX_POINTS = 50_000
    if len(raw_time) > MAX_POINTS:
        indices = np.linspace(0, len(raw_time)-1, MAX_POINTS).astype(int)
        raw_time = raw_time[indices]
        raw_flux = raw_flux[indices]

    valid = np.isfinite(raw_time) & np.isfinite(raw_flux)
    t, f = raw_time[valid], raw_flux[valid]
    
    med, std = np.median(f), np.std(f)
    mask = np.abs(f - med) <= 3 * std
    t, f = t[mask], f[mask]
    
    window = min(101, len(f) - 1)
    if window % 2 == 0: window -= 1
    if window >= 5:
        trend = savgol_filter(f, window, polyorder=3)
        f_detrended = f / trend
    else:
        f_detrended = f / med
    flux_clean = f_detrended / np.median(f_detrended)

    return {
        "target_name": target_name,
        "raw_time": raw_time.tolist(),
        "raw_flux": raw_flux.tolist(),
        "cleaned_time": t.tolist(),
        "cleaned_flux": flux_clean.tolist(),
        "preprocessed": {
            "n_points": len(t),
            "n_points_raw": len(raw_time),
            "time_span": round(float(t[-1] - t[0]), 2),
            "flux_median": round(float(np.median(flux_clean)), 6),
            "outliers_removed": len(raw_time) - len(t),
        }
    }

def step2_tls(t: list, flux_clean: list) -> dict:
    from pipeline.step2_tls import find_period
    t_np = np.array(t)
    f_np = np.array(flux_clean)
    tls_result = find_period(t_np, f_np)
    
    # Clean non-serializable objects from tls_result if needed, but we will selectively pick fields
    period = float(tls_result.get("period", 0))
    depth_frac = 1.0 - float(tls_result.get("depth", 1.0))
    depth_ppm = round(depth_frac * 1_000_000, 1)
    duration_hrs = round(float(tls_result.get("duration", 0)) * 24, 3)
    
    # For JSON serialization
    def to_list(k):
        v = tls_result.get(k, np.array([]))
        return v.tolist() if isinstance(v, np.ndarray) else list(v)

    serializable_tls = {
        "period": period,
        "sde": round(float(tls_result.get("sde", 0)), 1),
        "depth": depth_ppm,
        "duration": duration_hrs,
        "snr": round(float(tls_result.get("snr", 0)), 2),
        "t0": round(float(tls_result.get("t0", 0)), 4),
        "periods": to_list("periods"),
        "power": to_list("power"),
        "folded_time": to_list("folded_time"),
        "folded_flux": to_list("folded_flux"),
        "folded_model": to_list("folded_model"),
    }
    
    return {"tls_result": serializable_tls}

def step3_classify(t: list, flux_clean: list, tls_dict: dict, target_name: str) -> dict:
    from pipeline.step3_features import extract_features
    from pipeline.step4_classifier import classify
    from pipeline.step5_params import estimate_parameters
    
    t_np = np.array(t)
    f_np = np.array(flux_clean)
    
    # Reconstruct expected TLS result format for downstream functions
    tls_result = {k: (np.array(v) if isinstance(v, list) else v) for k, v in tls_dict.items()}
    
    features = extract_features(t_np, f_np, tls_result)
    classification = classify(features, target_name=target_name)
    params = estimate_parameters(tls_result)
    
    # Mock raw data to empty arrays since build_response doesn't strictly need them for step3 UI
    return build_response(target_name, np.array([]), np.array([]), t_np, f_np,
                          tls_result, features, classification, params)
