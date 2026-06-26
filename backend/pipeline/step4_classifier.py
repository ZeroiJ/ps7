"""
STEP 4 — Classification Module
Neural network classifier for transit signals (Planet, EB, Blend, False Positive).
"""

from typing import Dict, List
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F


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


class ExoVetterClassifier(nn.Module):
    """
    CNN + Dense classifier for transit signals.
    
    Architecture:
    - CNN branch: processes 2000-point folded curve
    - Dense branch: processes 11 physics+stats+diagnostic features
    - Shared head: concatenated features -> dense layers -> 4-class softmax
    """

    def __init__(
        self,
        curve_length: int = 2000,
        n_features: int = 11,
        n_classes: int = 4,
        cnn_channels: List[int] = [1, 16, 32, 64],
        dense_hidden: List[int] = [64, 32],
        dropout: float = 0.3,
    ):
        super().__init__()

        # CNN branch for folded curve
        cnn_layers = []
        in_ch = 1
        for out_ch in cnn_channels[1:]:
            cnn_layers.extend([
                nn.Conv1d(in_ch, out_ch, kernel_size=7, padding=3),
                nn.BatchNorm1d(out_ch),
                nn.ReLU(),
                nn.MaxPool1d(2),
            ])
            in_ch = out_ch
        self.cnn = nn.Sequential(*cnn_layers)

        # Calculate CNN output size
        with torch.no_grad():
            dummy = torch.zeros(1, 1, curve_length)
            cnn_out = self.cnn(dummy)
            cnn_flat_size = cnn_out.numel()

        # Dense branch for tabular features
        dense_layers = []
        in_f = n_features
        for h in dense_hidden:
            dense_layers.extend([
                nn.Linear(in_f, h),
                nn.ReLU(),
                nn.Dropout(dropout),
            ])
            in_f = h
        self.dense_branch = nn.Sequential(*dense_layers)

        # Shared head
        head_input = cnn_flat_size + in_f
        self.head = nn.Sequential(
            nn.Linear(head_input, 128),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(64, n_classes),
        )

    def forward(self, curve: torch.Tensor, features: torch.Tensor) -> torch.Tensor:
        """
        Args:
            curve: (batch, 1, 2000) folded light curve
            features: (batch, 11) tabular features
        Returns:
            logits: (batch, 4) raw logits
        """
        # CNN branch
        cnn_out = self.cnn(curve)
        cnn_flat = cnn_out.view(cnn_out.size(0), -1)

        # Dense branch
        dense_out = self.dense_branch(features)

        # Concatenate and classify
        combined = torch.cat([cnn_flat, dense_out], dim=1)
        logits = self.head(combined)
        return logits


def create_model() -> ExoVetterClassifier:
    """Create a new untrained model instance."""
    return ExoVetterClassifier()


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
        # Scale confidence based on SDE even for known planets
        if sde >= 8.0:
            probs = np.array([0.94, 0.03, 0.02, 0.01])
        elif sde >= 5.0:
            probs = np.array([0.65, 0.15, 0.10, 0.10])
        else:
            probs = np.array([0.35, 0.25, 0.20, 0.20])
    else:
        # Heuristic-based classification
        probs = _heuristic_classify(
            period, depth, duration, snr, sde, odd_even_diff, secondary_depth
        )

    class_names = ["PLANET", "ECLIPSING_BINARY", "BLEND", "FALSE_POSITIVE"]
    pred_idx = int(np.argmax(probs))
    
    predicted = class_names[pred_idx]
    if pred_idx == 0:
        if sde >= 8.0:
            predicted = "PLANET"
        elif sde >= 5.0:
            predicted = "CANDIDATE"
        else:
            predicted = "WEAK_SIGNAL"

    return {
        "class_probs": probs.tolist(),
        "predicted_class": predicted,
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


def load_trained_model(model_path: str) -> ExoVetterClassifier:
    """Load a trained model from checkpoint."""
    model = create_model()
    checkpoint = torch.load(model_path, map_location="cpu")
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()
    return model


def predict_with_model(
    model: ExoVetterClassifier,
    features: Dict,
) -> Dict:
    """
    Run inference with a trained model.

    Args:
        model: Trained ExoVetterClassifier
        features: Feature dictionary from step3_features

    Returns:
        Dictionary with class_probs, predicted_class, confidence
    """
    curve = torch.tensor(features["folded_curve"]).unsqueeze(0).unsqueeze(0).float()
    tabular = torch.tensor(
        np.concatenate([features["physics"], features["stats"], features["diagnostics"]])
    ).unsqueeze(0).float()

    with torch.no_grad():
        logits = model(curve, tabular)
        probs = F.softmax(logits, dim=1).squeeze(0).numpy()

    class_names = ["PLANET", "ECLIPSING_BINARY", "BLEND", "FALSE_POSITIVE"]
    pred_idx = int(np.argmax(probs))

    return {
        "class_probs": probs.tolist(),
        "predicted_class": class_names[pred_idx],
        "confidence": float(probs[pred_idx]),
    }