# ☀️ Localized UV Risk & Hotspot Monitoring System (SIH26219)

An AI-based environmental safety system combining satellite-derived atmospheric telemetry 
(Sentinel-5P/TROPOMI Ozone, Copernicus CAMS) with localized geographic factors (elevation lapse, 
cloud attenuation, and diurnal solar zenith models) to predict micro-scale UV indices and 
mitigate occupational sun-burn hazards in data-sparse monitoring zones.

## Features
- **Satellite Data Ingestion:** Real-time Total Column Ozone (DU) and solar telemetry.
- **Micro-Scale Downscaling:** Physical elevation lapse (+11%/1000m) and empirical cloud attenuation modeling.
- **Interactive 24-Hour Diurnal Arc:** Time-of-day slider to track solar radiation progression.
- **Occupational Health Engine:** Standardized WHO exposure tiers and Minimal Erythemal Dose (MED) burn-time calculations across skin phototypes.
- **Statutory Audit Export:** Downloadable CSV compliance reports for labor safety officers.

## Quickstart
```bash
pip install -r requirements.txt
streamlit run app.py