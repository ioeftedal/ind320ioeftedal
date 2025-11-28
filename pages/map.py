import numpy as np
import pandas as pd
import geopandas as gpd
import folium
from streamlit_folium import st_folium
from branca.colormap import linear
import streamlit as st
import streamlit as st
import requests
import pandas as pd
import geopandas as gpd

from Snow_drift import (
    compute_yearly_results,
    compute_average_sector,
    plot_rose,
)

# PAGE CONFIG
st.set_page_config(page_title="Norwegian Power Price Dashboard", layout="wide")

st.title("Norwegian Power Price Areas (NO1–NO5)")
st.markdown(
    "Interactive dashboard for NVE price areas. "
    "Click on the map to select a coordinate and inspect the corresponding price area."
)

# DATA LOADING
@st.cache_data
def load_price_areas():
    gdf = gpd.read_file("data/file.geojson")  # NVE Elspot Område
    gdf = gdf.to_crs(4326)
    gdf["area_id"] = gdf.index.astype(str)
    return gdf

@st.cache_data
def load_municipalities():
    gdf = gpd.read_file("data/file.geojson")
    return gdf.to_crs(4326)

@st.cache_data
def load_geojson():
    gdf = gpd.read_file("data/file.geojson")
    gdf = gdf.to_crs(4326)
    return gdf


price_areas = load_price_areas()
municipalities = load_municipalities()
geojson_data = load_geojson()

# ============================================================
# USER DATE INPUTS (shared by energy, meteo, snow drift)
# ============================================================

st.subheader("Analysis Date Range")

start_date = st.date_input(
    "Start date",
    value=pd.to_datetime("2022-07-01"),
    min_value=pd.to_datetime("1950-01-01"),
    max_value=pd.to_datetime("today"),
    key="energy_start_date"
)

end_date = st.date_input(
    "End date",
    value=pd.to_datetime("2025-06-30"),
    min_value=start_date,
    max_value=pd.to_datetime("today"),
    key="energy_end_date"
)


if start_date > end_date:
    st.error("Start date must be before end date.")
    st.stop()



# PLACEHOLDER DATA synced with user-selected date range
energy_groups = ["Production", "Consumption"]
time_index = pd.date_range(start=start_date, end=end_date, freq="D")
days_available = len(time_index)

np.random.seed(1)
time_series_data = {
    group: pd.DataFrame(
        {area: np.random.uniform(10, 100, size=days_available)
         for area in price_areas["ElSpotOmr"]},
        index=time_index
    )
    for group in energy_groups
}

# USER INPUTS (full width at top)
st.subheader("Options")
selected_group = st.selectbox("Choose energy group", energy_groups)
selected_days = st.slider(
    "Select interval (days)", min_value=1, max_value=days_available, value=7
)

# Compute mean values for the choropleth
mean_values = time_series_data[selected_group].tail(selected_days).mean()
price_areas["value"] = price_areas["ElSpotOmr"].map(mean_values)

# TWO-COLUMN LAYOUT (map + info)
col_map, col_info = st.columns([2, 1])

with col_map:
    st.subheader("Interactive Price Area Map")
    colormap = linear.YlOrRd_09.scale(price_areas["value"].min(), price_areas["value"].max())
    colormap.caption = f"Mean {selected_group} over last {selected_days} days"

    m = folium.Map(location=[64.5, 11], zoom_start=5, tiles="cartodbpositron")

    folium.GeoJson(
        price_areas,
        style_function=lambda f: {
            "fillColor": colormap(f["properties"]["value"]),
            "color": "#333333",
            "weight": 1,
            "fillOpacity": 0.5,
        },
        tooltip=folium.GeoJsonTooltip(
            fields=["ElSpotOmr", "value"],
            aliases=["Price Area", f"Mean {selected_group}"],
        ),
        name="Price Areas",
    ).add_to(m)

    colormap.add_to(m)

    folium.GeoJson(
        municipalities,
        style_function=lambda f: {
            "fillColor": "transparent",
            "color": "#666666",
            "weight": 0.5,
        },
        tooltip=folium.GeoJsonTooltip(fields=["ElSpotOmr"], aliases=["Municipality"])
    ).add_to(m)

    m.add_child(folium.LatLngPopup())
    map_data = st_folium(m, height=600, width="100%")

with col_info:
    st.subheader("Selected Information")
    clicked_point = map_data.get("last_clicked")
    selected_area = None

    if clicked_point:
        lat, lon = clicked_point["lat"], clicked_point["lng"]
        st.info(f"Selected coordinate: **({lat:.5f}, {lon:.5f})**")

        point_gdf = gpd.GeoDataFrame(
            geometry=gpd.points_from_xy([lon], [lat]), crs=4326
        )
        joined = gpd.sjoin(point_gdf, price_areas, how="left", predicate="within")

        if not pd.isna(joined.iloc[0]["area_id"]):
            selected_area = joined.iloc[0]
            st.success(f"Location is inside **{selected_area['ElSpotOmr']}**")

            # Dynamic chart
            area_name = selected_area["ElSpotOmr"]
            st.subheader(f"{selected_group} Evolution (Last {selected_days} Days)")
            st.line_chart(time_series_data[selected_group][area_name].tail(selected_days))
        else:
            st.warning("Coordinate is outside any price area.")
    else:
        st.info("Click on the map to see area information and charts.")

# HIGHLIGHT SELECTED AREA MAP
if selected_area is not None:
    st.subheader("Selected Price Area Highlight")
    highlight_map = folium.Map(location=[lat, lon], zoom_start=6, tiles="cartodbpositron")

    folium.GeoJson(
        price_areas,
        style_function=lambda f: {
            "fillColor": colormap(f["properties"]["value"]),
            "color": "#777777",
            "weight": 1,
            "fillOpacity": 0.5,
        },
    ).add_to(highlight_map)

    # Highlight selected area with different outline
    poly = price_areas.loc[price_areas["area_id"] == selected_area["area_id"], "geometry"].iloc[0]
    folium.GeoJson(
        poly,
        style_function=lambda f: {
            "fillColor": "#3e82f7",
            "color": "#1a5fc4",
            "weight": 3,
            "fillOpacity": 0.3,
        },
        tooltip=selected_area["ElSpotOmr"],
    ).add_to(highlight_map)

    folium.Marker([lat, lon], popup="Selected Point").add_to(highlight_map)
    st_folium(highlight_map, height=500, width="100%")


clicked_point = map_data.get("last_clicked")
if clicked_point:
    lat = clicked_point["lat"]
    lon = clicked_point["lng"]
else:
    # default if nothing is clicked
    lat = 60.57
    lon = 7.60


# Extract polygon for the selected point
point = gpd.GeoDataFrame(geometry=gpd.points_from_xy([lon], [lat]), crs=4326)
selected_poly = gpd.sjoin(point, geojson_data, how="left", predicate="within")

if selected_poly.empty:
    st.warning("Point is outside polygon dataset, using default coordinates.")
    lat, lon = 60.57, 7.60



def fetch_meteo(lat, lon, start_date, end_date):
    url = "https://archive-api.open-meteo.com/v1/era5"
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": [
            "temperature_2m",
            "precipitation",
            "wind_speed_10m",
            "wind_direction_10m"
        ],
        "start_date": start_date,
        "end_date": end_date,
    }

    r = requests.get(url, params=params).json()

    # Safety check for API error
    if "hourly" not in r:
        raise ValueError(f"Open-Meteo error: {r}")

    df = pd.DataFrame(r["hourly"])

    # Convert time column
    df["time"] = pd.to_datetime(df["time"])

    # --- IMPORTANT: Rename into Snow Drift module naming ---
    rename_map = {
        "temperature_2m": "temperature_2m (°C)",
        "precipitation": "precipitation (mm)",
        "wind_speed_10m": "wind_speed_10m (m/s)",
        "wind_direction_10m": "wind_direction_10m (°)"
    }

    # Only rename if columns exist (prevents KeyError)
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})

    return df


# --- Snow Drift date inputs ---
st.subheader("Snow Drift Date Range")


sd_start_date = st.date_input(
    "Start date",
    value=pd.to_datetime("2022-07-01"),
    min_value=pd.to_datetime("1950-01-01"),
    max_value=pd.to_datetime("today"),
    key="snowdrift_start_date"
)

sd_end_date = st.date_input(
    "End date",
    value=pd.to_datetime("2025-06-30"),
    min_value=sd_start_date,
    max_value=pd.to_datetime("today"),
    key="snowdrift_end_date"
)


if start_date > end_date:
    st.error("Start date must be before end date.")
    st.stop()

# Fetch ERA5 data with user dates
df = fetch_meteo(lat, lon, str(start_date), str(end_date))
# Assign season (your function requires this)
df["season"] = df["time"].apply(lambda dt: dt.year if dt.month >= 7 else dt.year - 1)

T = 3000
F = 30000
theta = 0.5

yearly = compute_yearly_results(df, T, F, theta)
overall = yearly["Qt (kg/m)"].mean()

avg_sectors = compute_average_sector(df)

st.subheader("Snow Drift Results")
st.write(yearly)

fig = plot_rose(avg_sectors, overall)
st.pyplot(fig)


# ============================================================
# 🔵 SLIDING WINDOW CORRELATION (Fixed for your dataset)
# ============================================================

st.header("Meteorology ↔ Energy Correlation Explorer")

# ---------- SELECTORS ----------
meteo_columns = [c for c in df.columns if c not in ["time", "season"]]
energy_columns = list(time_series_data[selected_group].columns)

col1, col2 = st.columns(2)
with col1:
    selected_meteo = st.selectbox("Meteorological variable", meteo_columns)

with col2:
    selected_energy = st.selectbox("Energy area", energy_columns)

lag = st.slider("Lag (hours)", -72, 72, 0)
window = st.slider("Window length (hours)", 6, 240, 48)


# ---------- PREP METEO ----------
met = (
    df[["time", selected_meteo]]
    .rename(columns={selected_meteo: "meteo"})
    .set_index("time")
)

# Ensure strictly hourly
met = met.resample("H").interpolate()


# ---------- PREP ENERGY ----------
energy_raw = time_series_data[selected_group][selected_energy]

# Convert daily → hourly without destroying shape
energy = (
    energy_raw
    .resample("H")
    .ffill()      # Forward fill instead of interpolation
)

energy.name = "energy"


# ---------- MERGE ----------
merged = pd.concat([met, energy], axis=1).dropna()

# Apply LAG
if lag != 0:
    merged["energy"] = merged["energy"].shift(lag)

merged = merged.dropna()

# Debug output if needed
if merged.empty:
    st.error("Merged meteorology & energy dataset is empty — timestamps don’t overlap.")
    st.write("Meteo index example:", met.head())
    st.write("Energy index example:", energy.head())
    st.stop()


# ---------- SLIDING CORRELATION ----------
corr = merged["meteo"].rolling(window).corr(merged["energy"])

if corr.dropna().empty:
    st.error("Correlation series is empty — window too large or lag misaligned.")
    st.write("Merged shape:", merged.shape)
    st.write("Correlation head:", corr.head())
    st.stop()


# ---------- PLOT ----------
import plotly.graph_objects as go

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=corr.index,
    y=corr.values,
    mode="lines",
    line=dict(color="royalblue", width=3),
))

fig.update_layout(
    title=f"Sliding Window Correlation: {selected_meteo} ↔ {selected_energy}",
    xaxis_title="Time",
    yaxis_title="Correlation",
    yaxis=dict(range=[-1, 1]),
    template="plotly_white",
    height=450
)

st.plotly_chart(fig, use_container_width=True)

# ============================================================
# STORE SHARED DATA FOR OTHER PAGES
# ============================================================

st.session_state["time_series_data"] = time_series_data
st.session_state["df"] = df                 # meteo dataframe
st.session_state["energy_groups"] = energy_groups
st.session_state["price_areas"] = price_areas

st.session_state["selected_group"] = selected_group
st.session_state["selected_area"] = selected_area["ElSpotOmr"] if selected_area is not None else None
st.session_state["lat"] = lat
st.session_state["lon"] = lon
st.session_state["start_date"] = start_date
st.session_state["end_date"] = end_date
st.session_state["sd_start_date"] = sd_start_date
st.session_state["sd_end_date"] = sd_end_date
