import streamlit as st
from read import read_csv_file, read_transpose_csv_file

@st.cache_data
def get_data():
    return read_csv_file("open-meteo-subset.csv")

data_df = get_data()

print(data_df)

all_users = ["temperature_2m (°C)", "precipitation (mm)", "wind_speed_10m (m/s)", "wind_gusts_10m (m/s)", "wind_direction_10m (°)" ]

with st.container(border=True):
    users = st.multiselect("Users", all_users, default=all_users)

data = data_df

tab1, tab2 = st.tabs(["Chart", "Dataframe"])
tab1.line_chart(data, height=600)
tab2.dataframe(data, height=250, use_container_width=True)
