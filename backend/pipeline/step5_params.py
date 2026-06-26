"""
STEP 5 — Parameter Estimation
Calculate planet radius, orbital distance, and equilibrium temperature.
"""

from typing import Dict, Optional
import numpy as np

# Physical constants
G = 6.67430e-11  # m^3 kg^-1 s^-2
MSUN = 1.98847e30  # kg
RSUN = 6.957e8  # m
AU = 1.495978707e11  # m
REARTH = 6.371e6  # m


def estimate_parameters(
    tls_results: Dict,
    star_radius: float = 1.0,  # Solar radii
    star_mass: float = 1.0,    # Solar masses
    star_temp: float = 5778.0, # Kelvin
) -> Dict:
    """
    Estimate planetary parameters from TLS results and stellar properties.

    Args:
        tls_results: Output from step2_tls.find_period()
        star_radius: Stellar radius in solar radii (R_sun)
        star_mass: Stellar mass in solar masses (M_sun)
        star_temp: Stellar effective temperature in Kelvin

    Returns:
        Dictionary with:
        - planet_radius: Planet radius in Earth radii (R_earth)
        - planet_radius_rearth: Alias for planet_radius
        - orbital_distance: Semi-major axis in AU
        - equilibrium_temperature: Planet equilibrium temperature in K
        - orbital_period_days: Orbital period in days
        - transit_depth_pct: Transit depth as percentage
        - transit_duration_hours: Transit duration in hours
    """
    if not tls_results:
        return _empty_params()

    period_days = tls_results["period"]
    depth_raw = tls_results["depth"]
    duration_days = tls_results["duration"]

    depth_frac = 1.0 - depth_raw

    # --- Planet Radius ---
    # depth_frac = (Rp / Rstar)^2
    # Rp = Rstar * sqrt(depth_frac)
    planet_radius_rsun = star_radius * np.sqrt(depth_frac)
    planet_radius_rearth = planet_radius_rsun * RSUN / REARTH

    # --- Orbital Distance (Kepler's Third Law) ---
    # P^2 = (4π^2 / GM) * a^3
    # a = (GM * P^2 / 4π^2)^(1/3)
    period_seconds = period_days * 86400.0
    star_mass_kg = star_mass * MSUN

    a_meters = (G * star_mass_kg * period_seconds**2 / (4 * np.pi**2))**(1/3)
    orbital_distance_au = a_meters / AU

    # --- Equilibrium Temperature ---
    # Teq = Tstar * sqrt(Rstar / 2a) * (1 - A)^(1/4)
    # Assume Bond albedo A = 0.3 (Earth-like)
    albedo = 0.3
    star_radius_m = star_radius * RSUN
    equilibrium_temperature = star_temp * np.sqrt(
        star_radius_m / (2 * a_meters)
    ) * (1 - albedo)**0.25

    return {
        "planet_radius": float(planet_radius_rearth),
        "planet_radius_rearth": float(planet_radius_rearth),
        "orbital_distance": float(orbital_distance_au),
        "equilibrium_temperature": float(equilibrium_temperature),
        "orbital_period_days": float(period_days),
        "transit_depth_pct": float(depth_frac * 100),
        "transit_duration_hours": float(duration_days * 24),
    }


def _empty_params() -> Dict:
    """Return empty parameter structure for failed detections."""
    return {
        "planet_radius": 0.0,
        "planet_radius_rearth": 0.0,
        "orbital_distance": 0.0,
        "equilibrium_temperature": 0.0,
        "orbital_period_days": 0.0,
        "transit_depth_pct": 0.0,
        "transit_duration_hours": 0.0,
    }


def format_planet_summary(params: Dict, target_name: str = "Candidate") -> str:
    """Generate a formatted planet summary card."""
    lines = [
        f"{target_name}",
        "─" * 32,
        f"Period:        {params['orbital_period_days']:.2f} days",
        f"Radius:        {params['planet_radius_rearth']:.2f} R⊕",
        f"Orbital Dist:  {params['orbital_distance']:.3f} AU",
        f"Temperature:   {params['equilibrium_temperature']:.0f} K "
        f"({params['equilibrium_temperature'] - 273.15:.0f}°C)",
        f"Depth:         {params['transit_depth_pct']:.3f}%",
        f"Duration:      {params['transit_duration_hours']:.1f} hours",
    ]
    return "\n".join(lines)


def classify_planet_type(planet_radius_rearth: float) -> str:
    """Classify planet by radius."""
    if planet_radius_rearth < 1.25:
        return "Earth-sized"
    elif planet_radius_rearth < 2.0:
        return "Super-Earth"
    elif planet_radius_rearth < 4.0:
        return "Sub-Neptune"
    elif planet_radius_rearth < 8.0:
        return "Neptune-sized"
    elif planet_radius_rearth < 12.0:
        return "Sub-Jupiter"
    else:
        return "Jupiter-sized"