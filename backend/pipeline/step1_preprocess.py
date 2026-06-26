"""
STEP 1 — Preprocessing Module
Load, clean, detrend, and normalize TESS light curves.
"""

from pathlib import Path
from typing import Tuple, Union
import numpy as np
from scipy.signal import savgol_filter
from lightkurve import search_lightcurve


_SAMPLE_DIR = Path(__file__).resolve().parent.parent / "data" / "sample_light_curves"


def _resolve_local_path(tic_id_or_path: Union[str, Path]) -> Union[Path, None]:
    """Resolve a TIC/TOI name to a local .npz file path, if one exists.

    Checks: (1) exact given path, (2) ``data/sample_light_curves/`` with
    the name as-is, and (3) ``data/sample_light_curves/`` with underscores
    substituted for dashes (e.g. *TOI-270* → *TOI_270.npz*).
    """
    p = Path(tic_id_or_path)

    # (1) Exact path
    if p.exists():
        return p

    # (2) Search in sample directory
    candidates = [
        _SAMPLE_DIR / p.name,
        _SAMPLE_DIR / (p.name + ".npz"),
        _SAMPLE_DIR / (str(p.name).replace("-", "_")),
        _SAMPLE_DIR / (str(p.name).replace("-", "_") + ".npz"),
    ]
    for c in candidates:
        if c.exists():
            return c

    return None


def load_and_clean(tic_id_or_path: Union[str, Path]) -> Tuple[np.ndarray, np.ndarray]:
    """
    Load a TESS light curve for a given TIC ID or local path,
    clean it, detrend it, and normalize it.

    Args:
        tic_id_or_path: TIC ID string (e.g., "TIC 123456789", "TOI-270")
                       or Path to a local .fits or .npz file

    Returns:
        Tuple of (time, flux) arrays - cleaned, detrended, normalized
    """
    local = _resolve_local_path(tic_id_or_path)

    if local is not None:
        if local.suffix == ".npz":
            data = np.load(local)
            time = data["time"]
            flux = data["flux"]
        elif local.suffix in (".fits", ".fit"):
            from lightkurve import read
            lc = read(local)
            time = lc.time.value
            flux = lc.flux.value
        else:
            raise ValueError(f"Unsupported file format: {local.suffix}")
    else:
        # Search by TIC ID or TOI name (online fallback)
        tic_str = str(tic_id_or_path)
        search_result = search_lightcurve(tic_str, mission="TESS")

        if len(search_result) == 0:
            search_result = search_lightcurve(tic_str, mission="TESS", author="QLP")

        if len(search_result) == 0:
            raise ValueError(f"No light curves found for {tic_str}")

        # Download the first available sector
        lc = search_result[0].download()
        time = lc.time.value
        flux = lc.flux.value

    # Remove NaN values
    valid_mask = np.isfinite(time) & np.isfinite(flux)
    time = time[valid_mask]
    flux = flux[valid_mask]

    # Remove bad quality cadences if quality array exists
    # (This is handled by lightkurve download if quality flag is available)

    # Sigma-clip outliers (>3 sigma)
    flux_median = np.median(flux)
    flux_std = np.std(flux)
    outlier_mask = np.abs(flux - flux_median) <= 3 * flux_std
    time = time[outlier_mask]
    flux = flux[outlier_mask]

    # Detrend using Savitzky-Golay filter
    # window_length must be odd and <= len(flux)
    window_length = min(101, len(flux) - 1)
    if window_length % 2 == 0:
        window_length -= 1
    if window_length >= 5:  # Need at least 5 points for polyorder=3
        trend = savgol_filter(flux, window_length=window_length, polyorder=3)
        flux_detrended = flux / trend
    else:
        flux_detrended = flux / flux_median

    # Normalize by median (baseline = 1.0)
    flux_normalized = flux_detrended / np.median(flux_detrended)

    return time, flux_normalized


def load_raw_and_clean(tic_id_or_path: Union[str, Path]) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Load a light curve and return both raw and cleaned versions.

    Returns:
        Tuple of (time, raw_flux, cleaned_flux)
    """
    local = _resolve_local_path(tic_id_or_path)

    if local is not None:
        if local.suffix == ".npz":
            data = np.load(local)
            time = data["time"]
            raw_flux = data["flux"]
        elif local.suffix in (".fits", ".fit"):
            from lightkurve import read
            lc = read(local)
            time = lc.time.value
            raw_flux = lc.flux.value
        else:
            raise ValueError(f"Unsupported file format: {local.suffix}")
    else:
        tic_str = str(tic_id_or_path)
        search_result = search_lightcurve(tic_str, mission="TESS")
        if len(search_result) == 0:
            search_result = search_lightcurve(tic_str, mission="TESS", author="QLP")
        if len(search_result) == 0:
            raise ValueError(f"No light curves found for {tic_str}")
        lc = search_result[0].download()
        time = lc.time.value
        raw_flux = lc.flux.value

    # Remove NaN
    valid_mask = np.isfinite(time) & np.isfinite(raw_flux)
    time = time[valid_mask]
    raw_flux = raw_flux[valid_mask]

    # Sigma-clip
    flux_median = np.median(raw_flux)
    flux_std = np.std(raw_flux)
    outlier_mask = np.abs(raw_flux - flux_median) <= 3 * flux_std
    time = time[outlier_mask]
    raw_flux = raw_flux[outlier_mask]

    # Detrend
    window_length = min(101, len(raw_flux) - 1)
    if window_length % 2 == 0:
        window_length -= 1
    if window_length >= 5:
        trend = savgol_filter(raw_flux, window_length=window_length, polyorder=3)
        flux_detrended = raw_flux / trend
    else:
        flux_detrended = raw_flux / flux_median

    # Normalize
    cleaned_flux = flux_detrended / np.median(flux_detrended)

    return time, raw_flux, cleaned_flux