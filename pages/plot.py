import streamlit as st
from read import read_csv_file, read_transpose_csv_file

@st.cache_data
def get_data():
    return read_csv_file("open-meteo-subset.csv")

data_df = get_data()

all_users = ["temperature_2m (°C)", "precipitation (mm)", "wind_speed_10m (m/s)", "wind_gusts_10m (m/s)", "wind_direction_10m (°)" ]

with st.container(border=True):
    # users = st.multiselect("Users", all_users, default=all_users)

    option = st.selectbox(
        "Option",
        (all_users),
    )

st.write("You selected:", option)

st.line_chart(data_df[f'{option}'], height=600)
