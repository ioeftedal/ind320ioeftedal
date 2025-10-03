import streamlit as st
from read import read_csv_file, filter_by_month, get_month_options, get_month_number

# Get and store the data from the csv file
@st.cache_data
def get_data():
    return read_csv_file("data/open-meteo-subset.csv")

data_df = get_data()


# A container to select which month you want to retrieve the data from
with st.container(border=True):
    selected_month = st.selectbox(
        "Select Month",
        get_month_options(),
    )

# Store the data for the selected month
month_nr = get_month_number(selected_month)
filtered_df = filter_by_month(data_df, month_nr)

# Switch the rows and columns, and turn all of the entries into a list
data_transposed = filtered_df.drop(['time', 'time_str'], axis=1).T
data_transposed['combined'] = data_transposed.values.tolist()

# Plot the transposed dataframe with the list valies
st.dataframe(
    data_transposed['combined'],
    column_config={
        "combined": st.column_config.LineChartColumn(),
    },
)
