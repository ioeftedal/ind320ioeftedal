import streamlit as st
import io
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import plotly.io as pio
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import requests
from statsmodels.tsa.statespace.sarimax import SARIMAX


# 1. VALIDATE REQUIRED DATA
required_keys = [
    "time_series_data", "df", "energy_groups", "price_areas",
    "selected_group", "selected_area", "lat", "lon",
    "start_date", "end_date"
]

for key in required_keys:
    if key not in st.session_state:
        st.error(f"Missing `{key}` in session_state. Please run the Map page first.")
        st.stop()

# 2. FETCH VARIABLES FROM SESSION_STATE
time_series_data = st.session_state["time_series_data"]
df_meteo = st.session_state["df"]
energy_groups = st.session_state["energy_groups"]
price_areas = st.session_state["price_areas"]

selected_group = st.session_state["selected_group"]
selected_area = st.session_state["selected_area"]
lat = st.session_state["lat"]
lon = st.session_state["lon"]
start_date = st.session_state["start_date"]
end_date = st.session_state["end_date"]

# --- HELPER FUNCTION TO FETCH WEATHER DATA ---
def fetch_weather(lat, lon, start_date, end_date, variables=None):
    """
    Fetch hourly weather data from Open-Meteo API.
    Returns a dataframe with columns for the requested variables.
    """
    if variables is None:
        variables = ["temperature_2m", "precipitation", "wind_speed_10m", "wind_direction_10m"]

    url = "https://archive-api.open-meteo.com/v1/era5"
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": variables,
        "start_date": str(start_date),
        "end_date": str(end_date),
    }

    r = requests.get(url, params=params).json()
    if "hourly" not in r:
        raise ValueError(f"Open-Meteo error: {r}")

    df = pd.DataFrame(r["hourly"])
    df["time"] = pd.to_datetime(df["time"])

    # Rename to match existing format
    rename_map = {
        "temperature_2m": "temperature_2m (°C)",
        "precipitation": "precipitation (mm)",
        "wind_speed_10m": "wind_speed_10m (m/s)",
        "wind_direction_10m": "wind_direction_10m (°)"
    }
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})

    return df

st.title("🔮 SARIMAX Forecasting – Energy Production & Consumption")

# 1. VALIDATE REQUIRED DATA (from main app)
required_keys = ["time_series_data", "df", "energy_groups", "price_areas"]

for key in required_keys:
    if key not in st.session_state:
        st.error(f"Missing `{key}` in session_state. Load map and snowdrift page first.")
        st.stop()

time_series_data = st.session_state["time_series_data"]
df_meteo = st.session_state["df"]
energy_groups = st.session_state["energy_groups"]
price_areas = st.session_state["price_areas"]


# 2. USER INPUTS
st.subheader("Configuration")

col1, col2, col3 = st.columns(3)
with col1:
    selected_group = st.selectbox("Energy group", energy_groups, index=energy_groups.index(selected_group))

with col2:
    selected_area = st.selectbox(
        "Price area",
        list(time_series_data[selected_group].columns),
        index=list(time_series_data[selected_group].columns).index(selected_area) if selected_area in time_series_data[selected_group].columns else 0
    )

with col3:
    forecast_horizon = st.number_input("Forecast horizon (days)", min_value=1, max_value=365, value=30)


# Training window
st.subheader("Training Data Window")

colA, colB = st.columns(2)
with colA:
    train_start = st.date_input("Training start date", value=pd.to_datetime(str(start_date)))
with colB:
    train_end = st.date_input("Training end date", value=pd.to_datetime(str(end_date)))

if train_start >= train_end:
    st.error("Training start must be before end date.")
    st.stop()


# 3. SELECT EXOGENOUS VARIABLES
st.subheader("Exogenous Variables (Optional)")

# Use default coordinates (replace with selected_area coords if available)
# Use coordinates from map page
lat = st.session_state["lat"]
lon = st.session_state["lon"]


# Fetch weather data if missing or outside training range
if "df" not in st.session_state \
        or st.session_state["df"].empty \
        or st.session_state["df"]["time"].min() > pd.to_datetime(train_start) \
        or st.session_state["df"]["time"].max() < pd.to_datetime(train_end):

    st.info("Fetching weather data for the selected period...")
    df_meteo = fetch_weather(lat, lon, train_start, train_end)
    st.session_state["df"] = df_meteo
else:
    df_meteo = st.session_state["df"]

# Prepare list of weather variables for selection
meteo_columns = [c for c in df_meteo.columns if c not in ["time", "season"]]

selected_exog = st.multiselect(
    "Select weather variables for SARIMAX",
    meteo_columns,
    default=[]
)

# 4. SARIMAX PARAMETERS
st.subheader("SARIMAX Parameters")

with st.expander("Show SARIMAX settings"):
    col_p, col_d, col_q = st.columns(3)
    p = col_p.number_input("p (AR)", value=1, min_value=0, max_value=5)
    d = col_d.number_input("d (Diff)", value=1, min_value=0, max_value=2)
    q = col_q.number_input("q (MA)", value=1, min_value=0, max_value=5)

    col_P, col_D, col_Q, col_s = st.columns(4)
    P = col_P.number_input("P (Seasonal AR)", value=0, min_value=0, max_value=5)
    D = col_D.number_input("D (Seasonal Diff)", value=1, min_value=0, max_value=2)
    Q = col_Q.number_input("Q (Seasonal MA)", value=1, min_value=0, max_value=5)
    s = col_s.number_input("Seasonal period (s)", value=7, min_value=1, max_value=365)


# 5. PREPARE DATA
energy_series = time_series_data[selected_group][selected_area]
energy_series = energy_series.loc[str(train_start):str(train_end)]

if energy_series.empty:
    st.error("Selected training window has no data.")
    st.stop()

# Exogenous 
if selected_exog:
    df_m = df_meteo.set_index("time")[selected_exog]
    df_m = df_m.resample("D").mean()
    df_m = df_m.reindex(energy_series.index).interpolate()
    exog_train = df_m
else:
    exog_train = None


# 6. FIT SARIMAX
st.subheader("Run Forecast")


# --- AFTER YOUR FORECAST AND PLOT ---
if st.button("Train & Forecast"):

    try:
        model = SARIMAX(
            energy_series,
            order=(p, d, q),
            seasonal_order=(P, D, Q, s),
            exog=exog_train,
            enforce_stationarity=False,
            enforce_invertibility=False,
        )

        results = model.fit()
        st.success("Model successfully trained.")
        st.write(results.summary())

        # Forecast code here...
        future_index = pd.date_range(
            start=energy_series.index[-1] + pd.Timedelta(days=1),
            periods=forecast_horizon,
            freq="D"
        )

        if selected_exog:
            exog_future = df_meteo.set_index("time")[selected_exog].resample("D").mean()
            exog_future = exog_future.reindex(future_index, method="ffill")
        else:
            exog_future = None

        forecast = results.get_forecast(steps=forecast_horizon, exog=exog_future)
        forecast_mean = forecast.predicted_mean
        conf_int = forecast.conf_int()

        # Plot
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=energy_series.index, y=energy_series.values, mode="lines", name="Training Data", line=dict(color="blue")))
        fig.add_trace(go.Scatter(x=future_index, y=forecast_mean.values, mode="lines", name="Forecast", line=dict(color="orange")))
        fig.add_trace(go.Scatter(x=future_index, y=conf_int.iloc[:, 0], mode="lines", line=dict(width=0), showlegend=False))
        fig.add_trace(go.Scatter(x=future_index, y=conf_int.iloc[:, 1], mode="lines", fill="tonexty", name="Confidence Interval", line=dict(width=0, color="rgba(255,165,0,0.2)")))
        fig.update_layout(title=f"SARIMAX Forecast – {selected_group} in {selected_area}", xaxis_title="Date", yaxis_title="Energy", template="plotly_white", height=600)
        st.plotly_chart(fig, use_container_width=True)

        # --- CREATE PDF OF SARIMAX SUMMARY ---
        pdf_buffer = io.BytesIO()
        c = canvas.Canvas(pdf_buffer, pagesize=letter)
        textobject = c.beginText(40, 750)
        textobject.setFont("Helvetica", 10)

        summary_str = results.summary().as_text()
        for line in summary_str.splitlines():
            textobject.textLine(line)
        c.drawText(textobject)
        c.showPage()
        c.save()
        pdf_buffer.seek(0)

        # --- SAVE PLOT AS PNG ---
        png_buffer = io.BytesIO()
        pio.write_image(fig, file=png_buffer, format='png')
        png_buffer.seek(0)

        # --- STREAMLIT DOWNLOAD BUTTONS ---
        st.download_button(
            label="📥 Download SARIMAX Summary (PDF)",
            data=pdf_buffer,
            file_name=f"sarimax_summary_{selected_group}_{selected_area}.pdf",
            mime="application/pdf"
        )

        st.download_button(
            label="📥 Download Forecast Plot (PNG)",
            data=png_buffer,
            file_name=f"sarimax_forecast_{selected_group}_{selected_area}.png",
            mime="image/png"
        )

    except Exception as e:
        st.error(f"SARIMAX failed: {e}")
