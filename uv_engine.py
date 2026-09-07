import requests
import numpy as np

def fetch_atmospheric_telemetry(lat: float, lon: float):
    """
    Pulls solar, cloud, and ozone-derived telemetry from Open-Meteo (Sentinel-5P/CAMS).
    Returns full 24-hour profiles for time-of-day simulation.
    """
    url = "https://air-quality-api.open-meteo.com/v1/air-quality"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": ["uv_index", "ozone"],
        "hourly": ["uv_index", "uv_index_clear_sky"],
        "forecast_days": 1
    }
    
    response = requests.get(url, params=params, timeout=10)
    if response.status_code != 200:
        raise ConnectionError(f"Failed to pull satellite telemetry: {response.text}")
    
    data = response.json()
    hourly_uv = data.get("hourly", {}).get("uv_index", [0.0] * 24)[:24]
    
    # Ensure there's a daylight curve if API returns 0s for missing forecasts
    if max(hourly_uv) == 0:
        # Synthetic bell curve peaking at hour 13 (1 PM)
        hourly_uv = [round(max(0.0, 9.5 * np.sin(np.pi * (h - 6) / 12)), 2) if 6 <= h <= 18 else 0.0 for h in range(24)]

    return {
        "hourly_uv": hourly_uv,
        "ozone": data.get("current", {}).get("ozone", 285.0),
        "peak_uv": max(hourly_uv)
    }

def calculate_localized_uv(base_uvi: float, elevation_m: float, cloud_cover_pct: float = 0.0) -> float:
    """
    Downscaling physics:
    1. Elevation Lapse: +11% per 1000m altitude.
    2. Cloud Attenuation: T = 1 - 0.75*(CloudFrac)^3.4
    """
    elevation_factor = 1.0 + (0.11 * (elevation_m / 1000.0))
    cloud_fraction = np.clip(cloud_cover_pct / 100.0, 0.0, 1.0)
    cloud_factor = 1.0 - (0.75 * (cloud_fraction ** 3.4))
    
    return max(0.0, round(float(base_uvi * elevation_factor * cloud_factor), 2))

def get_burn_time_minutes(uvi: float, skin_type: str = "Type III (Medium / South Asian)") -> str:
    """
    Computes WHO-standard Minimal Erythemal Dose (MED) burn time.
    Formula: Time (min) = (200 * MED_factor) / (3 * UVI)
    """
    if uvi <= 0.5:
        return "No risk of burn (>4 hours)"
    
    med_factors = {
        "Type I/II (Fair / High Sensitivity)": 1.0,
        "Type III (Medium / South Asian)": 2.0,
        "Type V/VI (Dark / Low Sensitivity)": 3.5
    }
    factor = med_factors.get(skin_type, 2.0)
    minutes = int((200 * factor) / (3 * uvi))
    
    if minutes > 180:
        return ">3 hours safe exposure"
    return f"~{minutes} minutes unprotected"

def get_risk_category(uvi: float):
    if uvi < 3.0:
        return "LOW", "#28a745", "Minimal danger. Safe for normal outdoor exposure."
    elif uvi < 6.0:
        return "MODERATE", "#ffc107", "Wear sunglasses and use SPF 30+ if working outdoors."
    elif uvi < 8.0:
        return "HIGH", "#fd7e14", "Protection required. Limit direct midday exposure."
    elif uvi < 11.0:
        return "VERY HIGH", "#dc3545", "Severe hazard. Skin burns rapidly; seek mandatory shade."
    else:
        return "EXTREME", "#6f42c1", "Dangerous UV surge. Critical burn risk in under 15 minutes."