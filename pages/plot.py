import streamlit as st
from read import read_csv_file, filter_by_month, get_month_options, get_month_number

# Get and store the data from the csv file
@st.cache_data
def get_data():
    return read_csv_file("data/open-meteo-subset.csv")

data_df = get_data()


# List of the different measurement a user should be able to select
measurement = ["temperature_2m (°C)", "precipitation (mm)", "wind_speed_10m (m/s)", "wind_gusts_10m (m/s)", "wind_direction_10m (°)" ]

# Conatiner where you can select measurement and month
with st.container(border=True):
    col1, col2 = st.columns(2)
    with col1:
        option = st.selectbox(
            "Select Measurement",
            (measurement),
        )
    with col2:
        selected_month = st.select_slider(
            "Select Month",
            get_month_options(),
        )
    

# Store the data for the selected month
month_nr = get_month_number(selected_month)
filtered_df = filter_by_month(data_df, month_nr)

# Display data for every day in the selected month
chart_data = filtered_df.set_index('time_str')[option]
st.line_chart(chart_data, height=600)
