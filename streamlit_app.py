import streamlit as st

# Define all pages
home_page = st.Page("pages/home.py", title="Home Page", icon=":material/house:")
elhub_api_page = st.Page("pages/elhubapi.py", title="Elhub API")
new_A = st.Page("pages/new_A.py", title="New A")
table_page = st.Page("pages/table.py", title="Table Page", icon=":material/table:")
plot_page = st.Page("pages/plot.py", title="Plot Page", icon=":material/chart_data:")
new_B = st.Page("pages/new_B.py", title="New B")
dummy_page = st.Page("pages/dummy.py", title="Dummy Page", icon=":material/robot_2:")
map_page = st.Page("pages/map.py", title="Map and Snowdrift", icon="❄️")
forecast_page = st.Page("pages/sarimax.py", title="SARIMAX Forecasting", icon="🔮")

# Set up navigation with grouped sections
pg = st.navigation({
    "Main": [home_page, elhub_api_page, new_A, table_page, plot_page, new_B, dummy_page],
    "Geospatial Analysis": [map_page],
    "Energy Analytics": [forecast_page]
})

st.set_page_config(
    page_title="IND320 Eftedal", 
    page_icon=":material/edit:",
    layout="wide"
)

pg.run()
