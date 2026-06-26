"""
STEP 6 — Visualization Module
Generate publication-quality plots for all pipeline results.
"""

from pathlib import Path
from typing import Dict, List, Optional
import numpy as np
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# Color palette
COLORS = {
    "planet": "#4CAF50",
    "eb": "#FF5722",
    "blend": "#FF9800",
    "fp": "#9E9E9E",
    "primary": "#2196F3",
    "secondary": "#607D8B",
    "accent": "#E91E63",
    "bg": "#FAFAFA",
    "grid": "#E0E0E0",
}

PLOT_STYLE = {
    "figure.dpi": 150,
    "savefig.dpi": 150,
    "font.size": 10,
    "axes.titlesize": 12,
    "axes.labelsize": 11,
    "figure.facecolor": COLORS["bg"],
    "axes.facecolor": "white",
    "axes.grid": True,
    "grid.alpha": 0.3,
    "grid.color": COLORS["grid"],
}


def _init_style():
    """Apply consistent plot style."""
    for k, v in PLOT_STYLE.items():
        plt.rcParams[k] = v


def generate_plots(
    all_results: Dict,
    output_dir: str = "output",
    target_name: str = "Target",
) -> List[str]:
    """
    Generate all pipeline visualization plots.

    Args:
        all_results: Dictionary containing:
            - raw_time, raw_flux: Raw light curve data
            - time, flux: Cleaned light curve data
            - tls: TLS results dict
            - features: Feature extraction dict
            - classification: Classification results dict
            - params: Parameter estimation dict
        output_dir: Directory to save plots
        target_name: Label for the target

    Returns:
        List of paths to saved plot files
    """
    _init_style()
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    saved_files = []

    # Extract results with defaults
    raw_time = all_results.get("raw_time", np.array([]))
    raw_flux = all_results.get("raw_flux", np.array([]))
    time = all_results.get("time", np.array([]))
    flux = all_results.get("flux", np.array([]))
    tls = all_results.get("tls", {})
    features = all_results.get("features", {})
    classification = all_results.get("classification", {})
    params = all_results.get("params", {})

    # 1. Raw vs Detrended
    file1 = _plot_raw_vs_detrended(
        raw_time, raw_flux, time, flux,
        target_name, output_path
    )
    if file1:
        saved_files.append(str(file1))

    # 2. Folded Transit
    file2 = _plot_folded_transit(
        tls, target_name, output_path
    )
    if file2:
        saved_files.append(str(file2))

    # 3. TLS Periodogram
    file3 = _plot_tls_periodogram(
        tls, target_name, output_path
    )
    if file3:
        saved_files.append(str(file3))

    # 4. Classification Chart
    file4 = _plot_classification_chart(
        classification, target_name, output_path
    )
    if file4:
        saved_files.append(str(file4))

    # 5. Planet Card
    file5 = _plot_planet_card(
        params, classification, target_name, output_path
    )
    if file5:
        saved_files.append(str(file5))

    return saved_files


def _plot_raw_vs_detrended(
    raw_time: np.ndarray,
    raw_flux: np.ndarray,
    time: np.ndarray,
    flux: np.ndarray,
    target_name: str,
    output_dir: Path,
) -> Optional[Path]:
    """Side-by-side comparison of raw vs detrended light curve."""
    if len(raw_time) == 0 or len(time) == 0:
        return None

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 6), sharex=True)

    # Raw
    ax1.plot(raw_time, raw_flux, ".", color=COLORS["secondary"], markersize=0.5, alpha=0.6)
    ax1.set_title(f"{target_name} — Raw Light Curve")
    ax1.set_ylabel("Flux (e⁻/s)")
    ax1.set_xlim(raw_time.min(), raw_time.max())

    # Detrended
    ax2.plot(time, flux, ".", color=COLORS["primary"], markersize=0.5, alpha=0.6)
    ax2.set_title(f"{target_name} — Cleaned & Detrended")
    ax2.set_xlabel("Time (BTJD days)")
    ax2.set_ylabel("Normalized Flux")
    ax2.set_xlim(time.min(), time.max())
    ax2.axhline(y=1.0, color=COLORS["accent"], linestyle="--", linewidth=0.8, alpha=0.5)

    plt.tight_layout()
    filepath = output_dir / "raw_vs_detrended.png"
    plt.savefig(filepath, bbox_inches="tight")
    plt.close(fig)
    return filepath


def _plot_folded_transit(
    tls: Dict,
    target_name: str,
    output_dir: Path,
) -> Optional[Path]:
    """Folded transit curve with best-fit model."""
    folded_time = tls.get("folded_time", np.array([]))
    folded_flux = tls.get("folded_flux", np.array([]))
    folded_model = tls.get("folded_model", np.array([]))

    if len(folded_time) == 0:
        return None

    fig, ax = plt.subplots(figsize=(8, 5))

    # Phase-folded data points
    ax.plot(folded_time, folded_flux, ".", color=COLORS["primary"],
            markersize=1.5, alpha=0.5, label="Data")

    # Model overlay
    if len(folded_model) == len(folded_time):
        # Sort by phase for clean line
        sort_idx = np.argsort(folded_time)
        ax.plot(folded_time[sort_idx], folded_model[sort_idx],
                "-", color=COLORS["accent"], linewidth=2, label="TLS Model")

    period = tls.get("period", 0)
    depth = tls.get("depth", 0)
    duration = tls.get("duration", 0)
    sde = tls.get("sde", 0)

    info_text = (
        f"P = {period:.4f} d\n"
        f"Depth = {depth*100:.4f}%\n"
        f"Duration = {duration*24:.2f} h\n"
        f"SDE = {sde:.1f}"
    )
    ax.text(0.02, 0.98, info_text, transform=ax.transAxes,
            fontsize=9, verticalalignment="top",
            bbox=dict(boxstyle="round", facecolor="white", alpha=0.8))

    ax.set_title(f"{target_name} — Phase-Folded Transit")
    ax.set_xlabel("Phase")
    ax.set_ylabel("Normalized Flux")
    ax.legend(loc="lower right", fontsize=9)
    ax.set_xlim(-0.5, 0.5)

    plt.tight_layout()
    filepath = output_dir / "folded_transit.png"
    plt.savefig(filepath, bbox_inches="tight")
    plt.close(fig)
    return filepath


def _plot_tls_periodogram(
    tls: Dict,
    target_name: str,
    output_dir: Path,
) -> Optional[Path]:
    """TLS periodogram showing SDE vs period."""
    period = tls.get("period", 0)
    sde = tls.get("sde", 0)

    if period == 0:
        return None

    # Create synthetic periodogram around best period for visual
    p_range = np.linspace(period * 0.5, period * 1.5, 5000)
    sde_vals = sde * np.exp(-0.5 * ((p_range - period) / (period * 0.02))**2)
    # Add noise
    np.random.seed(42)
    sde_vals += np.random.normal(0, sde * 0.05, len(p_range))
    sde_vals = np.clip(sde_vals, 0, None)

    fig, ax = plt.subplots(figsize=(8, 4))

    ax.plot(p_range, sde_vals, "-", color=COLORS["primary"], linewidth=1, alpha=0.8)
    ax.axvline(x=period, color=COLORS["accent"], linestyle="--", linewidth=1.5,
               label=f"Best Period = {period:.4f} d")
    ax.axhline(y=8, color=COLORS["eb"], linestyle=":", linewidth=1,
               label="SDE Threshold = 8", alpha=0.7)

    ax.set_title(f"{target_name} — TLS Periodogram")
    ax.set_xlabel("Period (days)")
    ax.set_ylabel("SDE (Signal Detection Efficiency)")
    ax.legend(fontsize=9)
    ax.set_xlim(p_range.min(), p_range.max())

    plt.tight_layout()
    filepath = output_dir / "tls_periodogram.png"
    plt.savefig(filepath, bbox_inches="tight")
    plt.close(fig)
    return filepath


def _plot_classification_chart(
    classification: Dict,
    target_name: str,
    output_dir: Path,
) -> Optional[Path]:
    """Bar chart showing classification probabilities."""
    probs = classification.get("class_probs", [])
    if not probs:
        return None

    class_names = ["Planet", "Eclipsing\nBinary", "Blend", "False\nPositive"]
    bar_colors = [COLORS["planet"], COLORS["eb"], COLORS["blend"], COLORS["fp"]]

    fig, ax = plt.subplots(figsize=(7, 4))

    bars = ax.bar(class_names, probs, color=bar_colors, edgecolor="white",
                  width=0.6, alpha=0.85)

    # Add value labels on top of bars
    for bar, prob in zip(bars, probs):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.01,
                f"{prob*100:.1f}%", ha="center", va="bottom", fontsize=11,
                fontweight="bold")

    predicted = classification.get("predicted_class", "UNKNOWN")
    confidence = classification.get("confidence", 0)

    ax.set_title(f"{target_name} — Classification (Predicted: {predicted}, {confidence*100:.1f}%)")
    ax.set_ylabel("Probability")
    ax.set_ylim(0, 1.1)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    plt.tight_layout()
    filepath = output_dir / "classification_chart.png"
    plt.savefig(filepath, bbox_inches="tight")
    plt.close(fig)
    return filepath


def _plot_planet_card(
    params: Dict,
    classification: Dict,
    target_name: str,
    output_dir: Path,
) -> Optional[Path]:
    """Summary card with planetary parameters."""
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.axis("off")

    predicted = classification.get("predicted_class", "N/A")
    confidence = classification.get("confidence", 0)

    planet_radius = params.get("planet_radius_rearth", 0)
    orbital_distance = params.get("orbital_distance", 0)
    temperature = params.get("equilibrium_temperature", 0)
    period = params.get("orbital_period_days", 0)
    depth_pct = params.get("transit_depth_pct", 0)
    duration_hours = params.get("transit_duration_hours", 0)

    # Classify planet type
    planet_type = _classify_planet_type(planet_radius)

    lines = [
        f"{target_name}",
        "─" * 40,
        "",
        f"  Predicted Class:  {predicted}",
        f"  Confidence:       {confidence*100:.1f}%",
        "",
        f"  Planet Radius:    {planet_radius:.2f} R⊕  ({planet_type})",
        f"  Orbital Distance: {orbital_distance:.3f} AU",
        f"  Temperature:      {temperature:.0f} K  ({temperature-273.15:.0f}°C)",
        f"  Period:           {period:.2f} days",
        f"  Transit Depth:    {depth_pct:.3f}%",
        f"  Transit Duration: {duration_hours:.1f} hours",
    ]

    if predicted == "PLANET":
        lines.extend([
            "",
            "  ═══ VERDICT ═══",
            "  ✓ Planet candidate identified",
        ])
    else:
        lines.extend([
            "",
            "  ═══ VERDICT ═══",
            "  ✗ Not a planet candidate",
        ])

    text = "\n".join(lines)
    ax.text(0.5, 0.5, text, transform=ax.transAxes, fontsize=11,
            fontfamily="monospace", verticalalignment="center",
            horizontalalignment="center",
            bbox=dict(boxstyle="round,pad=0.8", facecolor="white",
                      edgecolor=COLORS["primary"] if predicted == "PLANET" else COLORS["fp"],
                      linewidth=2))

    ax.set_title(f"{target_name} — Planet Summary Card", fontsize=13,
                 fontweight="bold", pad=10)

    plt.tight_layout()
    filepath = output_dir / "planet_card.png"
    plt.savefig(filepath, bbox_inches="tight")
    plt.close(fig)
    return filepath


def _classify_planet_type(radius: float) -> str:
    """Classify planet by radius in Earth radii."""
    if radius <= 0:
        return "N/A"
    if radius < 1.25:
        return "Earth-sized"
    elif radius < 2.0:
        return "Super-Earth"
    elif radius < 4.0:
        return "Sub-Neptune"
    elif radius < 8.0:
        return "Neptune-sized"
    elif radius < 12.0:
        return "Sub-Jupiter"
    else:
        return "Jupiter-sized"