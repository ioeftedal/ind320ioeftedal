import streamlit as st
import pandas as pd
from utils import save_data, decompose_production_stl, plot_production_spectrogram

st.title("New A – Time Series Decomposition & Spectrogram")

# --- Input for location and year ---
col1, col2, col3 = st.columns(3)
with col1:
    latitude = st.number_input("Latitude", value=59.91)
with col2:
    longitude = st.number_input("Longitude", value=10.75)
with col3:
    year = st.number_input("Year", min_value=1979, max_value=2025, value=2023, step=1)

# --- Fetch data and store in session state ---
if st.button("Fetch Data"):
    df = save_data(latitude, longitude, year)
    df["date"] = pd.to_datetime(df["date"])
    st.session_state["df"] = df
    st.success(f"Data fetched for {latitude}°, {longitude}° in {year}!")

# --- Use dataframe from session state if available ---
if "df" in st.session_state:
    df = st.session_state["df"]

    tab1, tab2 = st.tabs(["STL Analysis", "Spectrogram"])

    # TAB 1: STL
    with tab1:
        st.subheader("STL (Seasonal-Trend Decomposition)")

        col1, col2, col3 = st.columns(3)
        with col1:
            period = st.number_input("Period", value=24, key="stl_period")
        with col2:
            seasonal = st.number_input("Seasonal", value=7, key="stl_seasonal")
        with col3:
            trend = st.number_input("Trend", value=73, key="stl_trend")

        if st.button("Run STL Decomposition", key="stl_btn"):
            fig, result = decompose_production_stl(
                df,
                area=None,
                group=None,
                period=period,
                seasonal=seasonal,
                trend=trend,
            )
            st.plotly_chart(fig, use_container_width=True)
            st.markdown("### Component Summary")
            st.dataframe(result.trend.describe().to_frame("Trend"))
            st.dataframe(result.seasonal.describe().to_frame("Seasonal"))

    # TAB 2: Spectrogram
    with tab2:
        st.subheader("Spectrogram Analysis")

        col1, col2 = st.columns(2)
        with col1:
            window_length = st.slider("Window Length", min_value=64, max_value=1024, value=256, step=64, key="spec_window")
        with col2:
            overlap = st.slider("Overlap", min_value=32, max_value=512, value=128, step=32, key="spec_overlap")

        if st.button("Generate Spectrogram", key="spec_btn"):
            fig, (f, t, Sxx) = plot_production_spectrogram(
                df,
                area=None,
                group=None,
                window_length=window_length,
                overlap=overlap
            )
            st.plotly_chart(fig, use_container_width=True)
            st.markdown("Spectrogram generated for selected location.")
