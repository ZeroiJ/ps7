"""
STEP 4 — Classification Module
Neural network classifier for transit signals (Planet, EB, Blend, False Positive).
"""

from typing import Dict, List
import numpy as np

# Known exoplanet hosts for mock high-confidence classification
KNOWN_PLANETS = {
    "HD 209458": "HD 209458 b (first transiting exoplanet)",
    "TRAPPIST-1": "TRAPPIST-1 system (7 Earth-sized planets)",
    "TOI-270": "TOI-270 (3 planets)",
    "TOI-178": "TOI-178 (6 planets in resonance)",
    "TOI-700": "TOI-700 (habitable zone planet)",
    "TOI-1231": "TOI-1231 b (sub-Neptune)",
    "TOI-2180": "TOI-2180 b (long-period giant)",
}

def mock_classify(features: Dict, target_name: str = "") -> Dict:
    """
    Mock classifier for demo purposes (no training data yet).

    Args:
        features: Output from step3_features.extract_features()
        target_name: Name of target (e.g., "TOI-270") for known planet detection

    Returns:
        Dictionary with:
        - class_probs: [p_planet, p_eb, p_blend, p_fp]
        - predicted_class: str
        - confidence: float (max probability)
    """
    physics = features["physics"]
    diagnostics = features["diagnostics"]
    folded_curve = features["folded_curve"]

    period = physics[0]
    depth = physics[1]
    duration = physics[2]
    snr = physics[3]
    sde = physics[4]

    odd_even_diff = diagnostics[0]
    secondary_depth = diagnostics[1]

    # Check if known planet host
    is_known = any(known in target_name for known in KNOWN_PLANETS)

    if is_known:
        # High confidence planet for known systems
        probs = np.array([0.94, 0.03, 0.02, 0.01])
    else:
        # Heuristic-based classification
        probs = _heuristic_classify(
            period, depth, duration, snr, sde, odd_even_diff, secondary_depth
        )

    class_names = ["PLANET", "ECLIPSING_BINARY", "BLEND", "FALSE_POSITIVE"]
    pred_idx = int(np.argmax(probs))

    return {
        "class_probs": probs.tolist(),
        "predicted_class": class_names[pred_idx],
        "confidence": float(probs[pred_idx]),
    }


def _heuristic_classify(
    period: float,
    depth: float,
    duration: float,
    snr: float,
    sde: float,
    odd_even_diff: float,
    secondary_depth: float,
) -> np.ndarray:
    """Heuristic classification based on physical constraints."""
    probs = np.zeros(4)

    # Start with baseline
    probs[3] = 0.4  # False positive baseline

    # Strong TLS detection
    if sde > 15:
        probs[0] += 0.3  # Planet
        probs[3] -= 0.2
    elif sde > 10:
        probs[0] += 0.15
        probs[3] -= 0.1
    elif sde > 8:
        probs[0] += 0.05
        probs[3] -= 0.05

    # Depth constraints (planets < 2%)
    if depth < 0.02:
        probs[0] += 0.15
        probs[1] -= 0.1
    elif depth > 0.05:
        probs[1] += 0.3  # Eclipsing binary
        probs[0] -= 0.2

    # Duration constraints
    duration_hours = duration * 24
    if 1.0 <= duration_hours <= 15:
        probs[0] += 0.1
    elif duration_hours > 15:
        probs[1] += 0.15

    # Period constraints
    if period > 0.5:
        probs[0] += 0.05

    # Secondary eclipse -> eclipsing binary
    if secondary_depth > 0.001:
        probs[1] += 0.3
        probs[0] -= 0.2

    # Odd-even difference -> planet (slight)
    if abs(odd_even_diff) < 0.0005:
        probs[0] += 0.05

    # Normalize and clip
    probs = np.clip(probs, 0.01, 0.97)
    probs = probs / probs.sum()

    return probs


def classify(features: Dict, target_name: str = "") -> Dict:
    """
    Main classification function.
    Currently uses mock classifier; replace with trained model when available.

    Args:
        features: Output from step3_features.extract_features()
        target_name: Optional target identifier for known planet lookup

    Returns:
        Dictionary with class_probs, predicted_class, confidence
    """
    return mock_classify(features, target_name)