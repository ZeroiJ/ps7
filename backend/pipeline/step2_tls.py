"""
STEP 2 — Transit Least Squares (TLS) Period Detection
Find the best transit period and model parameters.

TLS results object provides these attributes:
    SDE, period, period_uncertainty, T0, duration, depth,
    depth_mean, depth_mean_even, depth_mean_odd, rp_rs,
    snr, snr_per_transit, odd_even_mismatch,
    folded_phase, folded_y, folded_dy, model_folded_phase, model_folded_model,
    model_lightcurve_time, model_lightcurve_model,
    periods, power, power_raw, FAP, SR, chi2, chi2red
"""

from typing import Dict
import numpy as np
from transitleastsquares import transitleastsquares


def find_period(
    time: np.ndarray,
    flux: np.ndarray,
    period_min: float = 0.5,
    period_max: float = 13.5,
) -> Dict:
    """
    Use TLS to find the best transit period and model parameters.

    Args:
        time: Time array (days)
        flux: Normalized flux array (baseline ~1.0)
        period_min: Minimum period to search (days)
        period_max: Maximum period to search (days)

    Returns:
        Dictionary with keys:
        - period: Best period (days)
        - sde: Signal Detection Efficiency score
        - depth: Transit depth (fractional flux drop)
        - duration: Transit duration (days)
        - snr: Signal-to-Noise Ratio
        - t0: Transit center time (BTJD)
        - rp_rs: Planet-to-star radius ratio
        - folded_time: Phase-folded time (centered at 0)
        - folded_flux: Phase-folded flux values
        - folded_model: TLS folded transit model
        - power: Full periodogram power array
        - periods: Trial periods array
    """
    model = transitleastsquares(time, flux)

    results = model.power(
        period_min=period_min,
        period_max=period_max,
        R_star=1.0,       # Solar radius — tells TLS expected transit duration
        M_star=1.0,       # Solar mass — helps TLS narrow duration search
    )

    folded_phase = np.asarray(results.folded_phase, dtype=np.float64)
    folded_phase = np.where(folded_phase > 0.5, folded_phase - 1, folded_phase)
    sort_idx = np.argsort(folded_phase)
    folded_time = folded_phase[sort_idx]
    folded_flux = np.asarray(results.folded_y, dtype=np.float64)[sort_idx]

    model_folded = getattr(results, "model_folded_model", None)
    if model_folded is not None:
        folded_model = np.asarray(model_folded, dtype=np.float64)[sort_idx]
    else:
        folded_model = np.ones_like(folded_flux)

    return {
        "period": float(results.period),
        "period_uncertainty": float(getattr(results, "period_uncertainty", 0.0)),
        "sde": float(results.SDE),
        "depth": float(results.depth),
        "duration": float(results.duration),
        "snr": float(results.snr),
        "snr_per_transit": np.asarray(getattr(results, "snr_per_transit", [])),
        "t0": float(results.T0),
        "rp_rs": float(getattr(results, "rp_rs", 0.0)),
        "odd_even_mismatch": float(getattr(results, "odd_even_mismatch", 0.0)),
        "power": np.asarray(results.power, dtype=np.float64),
        "periods": np.asarray(results.periods, dtype=np.float64),
        "folded_time": folded_time,
        "folded_flux": folded_flux,
        "folded_model": folded_model,
    }


def run_tls_search(
    time: np.ndarray,
    flux: np.ndarray,
) -> Dict:
    """
    Convenience wrapper that runs TLS with default parameters
    and returns a standardized result dictionary.

    Returns empty dict if SDE < 8 (no significant detection).
    """
    result = find_period(time, flux)

    if result["sde"] < 8:
        return {}

    return result