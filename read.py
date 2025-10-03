import pandas as pd
import streamlit as st

@st.cache_data
def read_csv_file(filepath: str) -> pd.DataFrame:
    df = pd.read_csv(f"{filepath}").drop(columns=['time'])

    # df['time'] = df['time'].dt.strftime('%Y-%m-%d %h:%m')
    # time_list = df['time'].tolist()
    # temp_list = df['temperature_2m (°C)'].tolist()
    # precipitation_list = df['precipitation (mm)'].tolist()
    # wind_speed_list = df['wind_speed_10m (m/s)'].tolist()
    # wind_gusts_list = df['wind_gusts_10m (m/s)'].tolist()
    # wind_direction_list = df['wind_direction_10m (°)'].tolist()

    return df


@st.cache_data
def read_transpose_csv_file(filepath):
    data = read_csv_file(filepath)
    data_transposed = data.T
    data_transposed['combined'] = data_transposed.values.tolist()

    return data_transposed['combined']
