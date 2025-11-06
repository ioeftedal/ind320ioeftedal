import streamlit as st

home_page = st.Page("pages/home.py", title="Home Page", icon=":material/house:")
elhub_api_page = st.Page("pages/elhubapi.py", title="Elhub API")
new_A = st.Page("pages/new_A.py", title="New A")
table_page = st.Page("pages/table.py", title="Table Page", icon=":material/table:")
plot_page = st.Page("pages/plot.py", title="Plot Page", icon=":material/chart_data:")
new_B = st.Page("pages/new_B.py", title="New B")
dummy_page = st.Page("pages/dummy.py", title="Dummy Page", icon=":material/robot_2:")

pg = st.navigation([
    home_page, 
    elhub_api_page, 
    new_A,
    table_page, 
    plot_page, 
    new_B,
    dummy_page
])

st.set_page_config(page_title="IND320 Eftedal", page_icon=":material/edit:")
pg.run()
