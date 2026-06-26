"""
ExoVetter Pipeline — 6-Step Transit Analysis Pipeline

Processes TESS light curves through preprocessing, period detection,
feature extraction, classification, parameter estimation, and visualization.

Usage:
    from pipeline import run_pipeline
    results = run_pipeline("TOI-270")
"""

from .step1_preprocess import load_and_clean, load_raw_and_clean
from .step2_tls import find_period, run_tls_search
from .step3_features import extract_features, concatenate_features
from .step4_classifier import classify, create_model
from .step5_params import estimate_parameters, format_planet_summary
from .step6_visualize import generate_plots


def run_pipeline(
    target: str,
    star_radius: float = 1.0,
    star_mass: float = 1.0,
    star_temp: float = 5778.0,
    output_dir: str = "output",
) -> dict:
    """
    Run the full 6-step ExoVetter pipeline on a TESS target.

    Args:
        target: TIC ID or TOI name (e.g., "TOI-270", "TIC 259377017")
                or path to a local .npz/.fits file
        star_radius: Stellar radius in solar radii
        star_mass: Stellar mass in solar masses
        star_temp: Stellar temperature in Kelvin
        output_dir: Directory for saving visualization outputs

    Returns:
        Dictionary with all pipeline results:
        - time, flux: Cleaned light curve
        - raw_time, raw_flux: Original (before cleaning)
        - tls: TLS period detection results
        - features: Extracted features
        - classification: Classification results
        - params: Estimated planetary parameters
        - plots: List of saved plot paths
    """
    results = {"target": target}

    # STEP 1: Preprocess
    time, raw_flux, cleaned_flux = load_raw_and_clean(target)
    results["time"] = time
    results["flux"] = cleaned_flux
    results["raw_time"] = time  # Same time axis
    results["raw_flux"] = raw_flux

    # STEP 2: TLS Period Detection
    tls_result = find_period(time, cleaned_flux)
    results["tls"] = tls_result

    # STEP 3: Feature Extraction
    features = extract_features(time, cleaned_flux, tls_result)
    results["features"] = features

    # STEP 4: Classification
    classification = classify(features, target_name=target)
    results["classification"] = classification

    # STEP 5: Parameter Estimation
    params = estimate_parameters(tls_result, star_radius, star_mass, star_temp)
    results["params"] = params

    # STEP 6: Visualization
    all_results = {
        "raw_time": time,
        "raw_flux": raw_flux,
        "time": time,
        "flux": cleaned_flux,
        "tls": tls_result,
        "features": features,
        "classification": classification,
        "params": params,
    }
    plots = generate_plots(all_results, output_dir, target_name=target)
    results["plots"] = plots

    return results


__all__ = [
    "load_and_clean",
    "load_raw_and_clean",
    "find_period",
    "run_tls_search",
    "extract_features",
    "concatenate_features",
    "classify",
    "create_model",
    "estimate_parameters",
    "format_planet_summary",
    "generate_plots",
    "run_pipeline",
]
