"""
STEP 3 — Feature Extraction
Extract physics, statistical, and diagnostic features from light curves.
"""

from typing import Dict
import numpy as np
from scipy.stats import skew, kurtosis


def extract_features(
    time: np.ndarray,
    flux: np.ndarray,
    tls_results: Dict,
) -> Dict:
    """
    Extract features for classification.

    Args:
        time: Cleaned time array
        flux: Cleaned, normalized flux array
        tls_results: Output from step2_tls.find_period()

    Returns:
        Dictionary with keys:
        - physics: [period, depth, duration, snr, sde]
        - stats: [skewness, kurtosis, std, mad]
        - diagnostics: [odd_even_diff, secondary_eclipse_depth]
        - folded_curve: 2000-point interpolated folded curve
    """
    if not tls_results:
        return _empty_features()

    period = tls_results["period"]
    depth_frac = 1.0 - tls_results["depth"]
    duration = tls_results["duration"]
    snr = tls_results["snr"]
    sde = tls_results["sde"]

    # --- Physics Features (5) ---
    physics = np.array([
        period,
        depth_frac,
        duration,
        snr,
        sde,
    ], dtype=np.float32)

    # --- Statistical Features (4) ---
    # Flux values during transit vs out of transit
    # For stats, use the whole cleaned light curve
    flux_std = np.std(flux)
    flux_mad = np.median(np.abs(flux - np.median(flux)))
    flux_skew = skew(flux)
    flux_kurt = kurtosis(flux)

    stats = np.array([
        float(flux_skew),
        float(flux_kurt),
        float(flux_std),
        float(flux_mad),
    ], dtype=np.float32)

    # --- Diagnostic Features (2) ---
    folded_time = tls_results["folded_time"]
    folded_flux = tls_results["folded_flux"]

    # Odd-Even test: compare odd vs even transits
    # In phase-folded data, transit is at phase ~0
    # Split transits by orbit number
    transit_mask = folded_time > -duration / period / 2
    transit_mask &= folded_time < duration / period / 2

    # For odd-even, we need the original (unfolded) transits
    # Approximate: check if there are multiple transit events
    odd_even_diff = _compute_odd_even_diff(time, flux, period, tls_results["t0"])

    # Secondary eclipse check at phase 0.5
    secondary_mask = np.abs(folded_time - 0.5) < duration / period / 2
    if np.any(secondary_mask):
        secondary_depth = 1.0 - np.median(folded_flux[secondary_mask])
        secondary_depth = max(0.0, float(secondary_depth))
    else:
        secondary_depth = 0.0

    diagnostics = np.array([
        float(odd_even_diff),
        float(secondary_depth),
    ], dtype=np.float32)

    # --- Folded Curve (2000 points for CNN) ---
    folded_curve = _interpolate_folded_curve(
        folded_time, folded_flux, n_points=2000
    )

    return {
        "physics": physics,
        "stats": stats,
        "diagnostics": diagnostics,
        "folded_curve": folded_curve,
    }


def _compute_odd_even_diff(
    time: np.ndarray,
    flux: np.ndarray,
    period: float,
    t0: float,
) -> float:
    """Compute difference between odd and even transit depths."""
    # Assign each point to a transit number
    transit_numbers = np.floor((time - t0) / period + 0.5).astype(int)

    # Find unique transit numbers that have enough points
    unique_transits = np.unique(transit_numbers)
    if len(unique_transits) < 2:
        return 0.0

    odd_depths = []
    even_depths = []

    for tn in unique_transits:
        mask = transit_numbers == tn
        transit_flux = flux[mask]
        if len(transit_flux) < 3:
            continue
        depth = 1.0 - np.min(transit_flux)
        if tn % 2 == 0:
            even_depths.append(depth)
        else:
            odd_depths.append(depth)

    if not odd_depths or not even_depths:
        return 0.0

    return float(np.mean(odd_depths) - np.mean(even_depths))


def _interpolate_folded_curve(
    folded_time: np.ndarray,
    folded_flux: np.ndarray,
    n_points: int = 2000,
) -> np.ndarray:
    """Interpolate folded curve to fixed number of points."""
    from scipy.interpolate import interp1d

    # Phase range -0.5 to 0.5
    phase_grid = np.linspace(-0.5, 0.5, n_points)

    # Interpolate
    # Only interpolate where we have data
    valid = np.isfinite(folded_flux)
    if np.sum(valid) < 4:
        return np.ones(n_points, dtype=np.float32)

    try:
        interp = interp1d(
            folded_time[valid],
            folded_flux[valid],
            kind="linear",
            bounds_error=False,
            fill_value=1.0,
        )
        curve = interp(phase_grid)
    except Exception:
        curve = np.ones(n_points, dtype=np.float32)

    return curve.astype(np.float32)


def _empty_features() -> Dict:
    """Return empty feature structure for failed detections."""
    return {
        "physics": np.zeros(5, dtype=np.float32),
        "stats": np.zeros(4, dtype=np.float32),
        "diagnostics": np.zeros(2, dtype=np.float32),
        "folded_curve": np.ones(2000, dtype=np.float32),
    }


def concatenate_features(features: Dict) -> np.ndarray:
    """
    Concatenate all features into a single vector for the classifier.

    Returns:
        1D array of shape (11 + 2000,) = (2011,)
    """
    return np.concatenate([
        features["physics"],      # 5
        features["stats"],        # 4
        features["diagnostics"],  # 2
        features["folded_curve"], # 2000
    ]).astype(np.float32)