"""Simulated exoplanet transit analysis pipeline.

Generates realistic-looking results without requiring real ML models,
lightkurve, or astropy.  Designed for hackathon demo / frontend testing.
"""

import time
import random
import math
from typing import Dict, Any

import numpy as np


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _transit_model(phases: np.ndarray, depth: float = 0.001,
                   duration_phase: float = 0.04) -> np.ndarray:
    """Simple box-shaped transit centred on phase 0."""
    model = np.ones_like(phases)
    in_transit = np.abs(phases) < duration_phase / 2
    model[in_transit] -= depth
    return model


def _generate_light_curve(n_points: int = 1000, period: float = 5.66,
                          depth: float = 0.001, noise: float = 0.0003,
                          time_span: float = 27.4) -> dict:
    """Create a synthetic TESS-like light curve with injected transits."""
    rng = np.random.default_rng(random.randint(0, 2**31))

    time = np.sort(rng.uniform(0, time_span, n_points))
    phase = ((time % period) / period + 0.5) % 1.0 - 0.5  # centred on 0

    flux_clean = _transit_model(phase, depth=depth)
    flux_raw = flux_clean + rng.normal(0, noise, n_points)

    # Add slow stellar variability (low-freq sinusoid)
    variability = 0.0005 * np.sin(2 * np.pi * time / 13.7 + rng.uniform(0, 2 * np.pi))
    flux_raw += variability

    return {
        "time": time,
        "flux_raw": flux_raw,
        "flux_clean": flux_clean + rng.normal(0, noise * 0.6, n_points),
        "phase": phase,
        "period": period,
        "depth": depth,
    }


def _generate_periodogram(true_period: float, n_periods: int = 500) -> dict:
    """Create a synthetic BLS/TLS periodogram with a clear peak."""
    rng = np.random.default_rng(random.randint(0, 2**31))

    periods = np.linspace(0.5, 30.0, n_periods)
    # Background noise
    power = rng.exponential(0.3, n_periods)
    # Inject a sharp peak at the true period
    sigma = 0.15
    peak = 12.0 * np.exp(-0.5 * ((periods - true_period) / sigma) ** 2)
    power += peak
    # Add a smaller alias at half-period
    alias = 3.5 * np.exp(-0.5 * ((periods - true_period / 2) / sigma) ** 2)
    power += alias

    return {"period": periods, "power": power}


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def run_mock_pipeline(file_path: str, filename: str) -> Dict[str, Any]:
    """Run a *simulated* exoplanet vetting pipeline.

    Parameters
    ----------
    file_path : str
        Path to the uploaded data file (read but not actually processed).
    filename : str
        Original upload filename — used to derive a target name.

    Returns
    -------
    dict
        A dictionary compatible with the ``PipelineResult`` Pydantic model.
    """
    # Simulate processing time (staggered so the UI can show progress)
    time.sleep(1.0)  # "preprocessing"
    time.sleep(0.8)  # "TLS search"
    time.sleep(0.7)  # "feature extraction + classification"

    # ------------------------------------------------------------------
    # Random but plausible parameters
    # ------------------------------------------------------------------
    rng = np.random.default_rng(random.randint(0, 2**31))

    period = round(float(rng.uniform(1.5, 15.0)), 4)
    depth = round(float(rng.uniform(0.0005, 0.003)), 6)
    sde = round(float(rng.uniform(8.0, 25.0)), 2)
    snr = round(float(rng.uniform(7.0, 40.0)), 2)
    duration_hrs = round(float(rng.uniform(1.0, 4.5)), 2)
    planet_radius = round(float(rng.uniform(1.0, 6.0)), 2)
    n_points = int(rng.integers(800, 1500))

    # ------------------------------------------------------------------
    # Generate synthetic data
    # ------------------------------------------------------------------
    lc = _generate_light_curve(n_points=n_points, period=period, depth=depth)
    pg = _generate_periodogram(period)

    # Target name from filename or fallback
    stem = filename.rsplit(".", 1)[0].replace("_", " ").replace("-", " ").title()
    target_name = stem if len(stem) < 30 else "TOI-270"

    # ------------------------------------------------------------------
    # Classification (weighted toward 'planet' for a nice demo)
    # ------------------------------------------------------------------
    classes = ["planet", "eclipsing_binary", "blend", "false_positive"]
    weights = np.array([0.55, 0.15, 0.15, 0.15])
    predicted_idx = int(rng.choice(len(classes), p=weights))
    predicted_class = classes[predicted_idx]

    # Generate probabilities that sum to 1 and favour the predicted class
    raw = rng.dirichlet(np.array([0.6 if i == predicted_idx else 0.2
                                   for i in range(4)]))
    # Make sure the predicted class is highest
    raw[predicted_idx] = max(raw) + 0.05
    probs = (raw / raw.sum()).tolist()
    probs = [round(p, 4) for p in probs]
    confidence = round(max(probs), 4)

    # ------------------------------------------------------------------
    # Assemble result
    # ------------------------------------------------------------------
    result: Dict[str, Any] = {
        "target_name": target_name,

        "preprocessed": {
            "n_points": n_points,
            "n_points_raw": n_points + int(rng.integers(50, 200)),
            "time_span": round(float(lc["time"][-1] - lc["time"][0]), 2),
            "flux_median": round(float(np.median(lc["flux_raw"])), 6),
            "flux_std": round(float(np.std(lc["flux_raw"])), 6),
            "flux_range": [
                round(float(np.min(lc["flux_raw"])), 6),
                round(float(np.max(lc["flux_raw"])), 6),
            ],
            "outliers_removed": int(rng.integers(5, 50)),
        },

        "tls_result": {
            "period": period,
            "sde": sde,
            "depth": round(depth * 1e6, 1),
            "duration": duration_hrs,
            "snr": snr,
            "t0": round(float(rng.uniform(0, period)), 4),
        },

        "features": {
            "physics": [
                round(float(x), 4)
                for x in rng.normal(0, 1, 8).tolist()
            ],
            "stats": [
                round(float(x), 4)
                for x in rng.normal(0, 1, 6).tolist()
            ],
            "diagnostics": [
                round(float(x), 4)
                for x in rng.normal(0, 1, 5).tolist()
            ],
        },

        "classification": {
            "predicted_class": predicted_class,
            "confidence": confidence,
            "class_probs": dict(zip(classes, probs)),
        },

        "parameters": {
            "planet_radius_rearth": planet_radius,
            "semi_major_axis_au": round(float(rng.uniform(0.02, 0.15)), 4),
            "equilibrium_temp_k": int(rng.integers(400, 1800)),
            "insolation_searth": round(float(rng.uniform(1, 300)), 1),
            "impact_parameter": round(float(rng.uniform(0.0, 0.9)), 3),
            "transit_depth_ppm": round(depth * 1e6, 1),
            "duration_hrs": duration_hrs,
            "ingress_duration_hrs": round(duration_hrs * float(rng.uniform(0.1, 0.25)), 3),
        },

        "plots": {
            "raw_flux": {
                "time": lc["time"].tolist(),
                "flux": lc["flux_raw"].tolist(),
            },
            "cleaned_flux": {
                "time": lc["time"].tolist(),
                "flux": lc["flux_clean"].tolist(),
            },
            "periodogram": {
                "frequency": (1.0 / pg["period"]).tolist(),
                "power": pg["power"].tolist(),
            },
            "folded_curve": {
                "phase": np.sort(lc["phase"]).tolist(),
                "flux": lc["flux_clean"][np.argsort(lc["phase"])].tolist(),
                "model": _transit_model(np.sort(lc["phase"]), depth=depth).tolist(),
            },
            "classification_bars": {
                "classes": classes,
                "probabilities": probs,
            },
        },
    }

    return result
