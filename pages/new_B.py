import streamlit as st
import pandas as pd
from utils import save_data, detect_temperature_outliers, detect_precipitation_anomalies

st.title("New B – Outlier & Anomaly Analysis")

col1, col2, col3 = st.columns(3)
with col1:
    latitude = st.number_input("Latitude", value=59.91)
with col2:
    longitude = st.number_input("Longitude", value=10.75)
with col3:
    year = st.number_input("Year", min_value=1979, max_value=2025, value=2023, step=1)

if st.button("Fetch Data"):
    df = save_data(latitude, longitude, year)
    df["date"] = pd.to_datetime(df["date"])
    st.session_state["df"] = df
    st.success(f"Data fetched for {latitude}°, {longitude}° in {year}!")

if "df" in st.session_state:
    df = st.session_state["df"]
    tab1, tab2 = st.tabs(["Outlier / SPC", "Anomaly / LOF"])

    with tab1:
        st.subheader("Outlier Detection (DCT + SPC)")
        col1, col2 = st.columns(2)
        with col1:
            cutoff = st.slider("DCT Cutoff", 10, 500, 100)
        with col2:
            std_mult = st.slider("Std Dev Multiplier", 1.0, 5.0, 2.0, 0.1)

        if st.button("Run Outlier/SPC Analysis"):
            fig, ax, summaries = detect_temperature_outliers(df, cutoff=cutoff, std_mult=std_mult)
            st.plotly_chart(fig, use_container_width=True)
            st.markdown("### Temperature Outliers")
            st.dataframe(summaries["temperature_outliers"].head())

    with tab2:
        st.subheader("Anomaly Detection (LOF)")
        lof_frac = st.slider("LOF contamination fraction", 0.001, 0.1, 0.01, 0.001)

        if st.button("Run LOF Analysis"):
            fig, ax, summaries = detect_precipitation_anomalies(df, lof_frac=lof_frac)
            st.plotly_chart(fig, use_container_width=True)
            st.markdown("### Precipitation Anomalies")
            st.dataframe(summaries["precip_anomalies"].head())
