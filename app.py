import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
from uv_engine import fetch_atmospheric_telemetry, calculate_localized_uv, get_risk_category, get_burn_time_minutes

st.set_page_config(page_title="Localized UV Risk & Hotspot Monitor", layout="wide")

st.title("☀️ Localized UV Hotspot & Occupational Risk Monitor")
st.caption("Satellite-derived (Sentinel-5P/CAMS) micro-scale solar UV index predictor for data-sparse zones")

REGIONS = {
    "Bardoli / Surat Belt (Gujarat)": {"lat": 21.12, "lon": 73.11, "elevation": 22},
    "Jodhpur Agricultural Belt (Rajasthan)": {"lat": 26.23, "lon": 73.02, "elevation": 231},
    "Ladakh High-Altitude Plains": {"lat": 34.15, "lon": 77.57, "elevation": 3500},
    "Custom GPS Coordinates": {"lat": 21.12, "lon": 73.11, "elevation": 50}
}

col_ctrl, col_map = st.columns([1, 2])

with col_ctrl:
    st.subheader("📍 Target Region")
    selected_region = st.selectbox("Select Bounding Zone", list(REGIONS.keys()))
    
    if selected_region == "Custom GPS Coordinates":
        lat = st.number_input("Latitude", value=21.1255, format="%.4f")
        lon = st.number_input("Longitude", value=73.1122, format="%.4f")
        elev = st.number_input("Elevation (m)", value=30, min_value=0, max_value=8000)
    else:
        lat = REGIONS[selected_region]["lat"]
        lon = REGIONS[selected_region]["lon"]
        elev = REGIONS[selected_region]["elevation"]
        st.write(f"**Elevation:** `{elev} m` | **Coords:** `{lat}°N, {lon}°E`")

    st.subheader("⏰ Diurnal Timing & Environment")
    
    # 24-Hour Slider (Allows user to inspect 12 PM peak, 8 AM morning, or night)
    selected_hour = st.slider("Select Time of Day (Hour)", min_value=0, max_value=23, value=12, format="%02d:00 hrs")
    simulated_cloud = st.slider("Simulated Cloud Cover (%)", min_value=0, max_value=100, value=15)
    skin_profile = st.selectbox("Worker Phototype Profile", [
        "Type III (Medium / South Asian)",
        "Type I/II (Fair / High Sensitivity)",
        "Type V/VI (Dark / Low Sensitivity)"
    ])

# Fetch satellite telemetry if region changes or not yet cached
if "telemetry" not in st.session_state or st.session_state.get("last_coords") != (lat, lon):
    with st.spinner("Connecting to Copernicus / Sentinel-5P telemetry feed..."):
        st.session_state["telemetry"] = fetch_atmospheric_telemetry(lat, lon)
        st.session_state["last_coords"] = (lat, lon)

telemetry = st.session_state["telemetry"]
base_hourly_uv = telemetry["hourly_uv"]

# Compute localized UV for selected hour
current_base_uv = base_hourly_uv[selected_hour]
local_uvi = calculate_localized_uv(current_base_uv, elev, simulated_cloud)
tier, color, advisory = get_risk_category(local_uvi)
burn_time = get_burn_time_minutes(local_uvi, skin_profile)

with col_ctrl:
    st.markdown("---")
    st.metric(
        label=f"Localized UVI @ {selected_hour:02d}:00",
        value=f"{local_uvi:.2f}",
        delta=f"{tier} EXPOSURE",
        delta_color="inverse"
    )
    
    st.metric(label="Estimated Time to Burn", value=burn_time)
    st.caption(f"Sentinel-5P Ozone: **{telemetry['ozone']:.1f} DU** | Midday Peak UVI: **{telemetry['peak_uv']}**")
    
    st.markdown(
        f"""
        <div style="background-color:{color}; padding:12px; border-radius:8px; color:white; font-weight:bold;">
            OCCUPATIONAL ADVISORY: {tier}<br>
            <span style="font-size:13px; font-weight:normal;">{advisory}</span>
        </div>
        """, unsafe_allow_html=True
    )

with col_map:
    st.subheader("🗺️ Micro-Scale Heatmap & Risk Buffer")
    m = folium.Map(location=[lat, lon], zoom_start=11, tiles="CartoDB positron")
    
    folium.Circle(
        location=[lat, lon],
        radius=5000,
        color=color,
        fill=True,
        fill_color=color,
        fill_opacity=0.35,
        popup=f"Zone UVI @ {selected_hour:02d}:00: {local_uvi} ({tier})"
    ).add_to(m)

    folium.Marker(
        [lat, lon],
        popup=f"Target: {local_uvi} UVI",
        icon=folium.Icon(color="red" if local_uvi >= 8.0 else ("orange" if local_uvi >= 6.0 else "blue"), icon="sun", prefix="fa")
    ).add_to(m)

    st_folium(m, width="100%", height=400)
    
    st.subheader("📈 24-Hour Diurnal UV Profile (Localized)")
    
    # Calculate localized curve for all 24 hours
    localized_curve = [calculate_localized_uv(u, elev, simulated_cloud) for u in base_hourly_uv]
    chart_df = pd.DataFrame({
        "Hour": [f"{h:02d}:00" for h in range(24)],
        "Localized UV Index": localized_curve,
        "Base Satellite UV": base_hourly_uv
    }).set_index("Hour")
    
    st.area_chart(chart_df)

# Compliance Audit Export
st.markdown("---")
st.subheader("📋 Statutory Occupational Sun-Exposure Export")

audit_df = pd.DataFrame([{
    "Region": selected_region,
    "Latitude": lat,
    "Longitude": lon,
    "Elevation_m": elev,
    "Simulated_Time": f"{selected_hour:02d}:00 hrs",
    "Sentinel5P_Ozone_DU": telemetry["ozone"],
    "Cloud_Cover_Pct": simulated_cloud,
    "Localized_UVI": local_uvi,
    "Risk_Tier": tier,
    "Skin_Phototype": skin_profile,
    "Safe_Burn_Time": burn_time
}])

csv = audit_df.to_csv(index=False).encode("utf-8")
st.download_button(
    label="📥 Download Regional UV Advisory Audit Log (CSV)",
    data=csv,
    file_name=f"uv_risk_log_{selected_region.split()[0].lower()}.csv",
    mime="text/csv"
)