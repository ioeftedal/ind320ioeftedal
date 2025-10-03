import streamlit as st
from read import read_transpose_csv_file


@st.cache_data
def get_data():
    return read_transpose_csv_file("open-meteo-subset.csv")

data_df = get_data()

st.dataframe(
    data_df,
    column_config={
        "combined": st.column_config.LineChartColumn(),
    },
)
