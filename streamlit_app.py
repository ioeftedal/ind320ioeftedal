import streamlit as st

home_page = st.Page("home.py", title="Home Page", icon=":material/house:")
table_page = st.Page("table.py", title="Table Page", icon=":material/table:")
plot_page = st.Page("plot.py", title="Plot Page", icon=":material/add_circle:")
dummy_page = st.Page("dummy.py", title="Dummy Page", icon=":material/add_circle:")

pg = st.navigation([home_page, table_page, plot_page, dummy_page])
st.set_page_config(page_title="IND320 Eftedal", page_icon=":material/edit:")
pg.run()
