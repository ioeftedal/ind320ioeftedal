import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from mongodb import get_data

st.title("Electricity Consumption Analysis")

# Load data from MongoDB
items = get_data()
df = pd.DataFrame(items)

# Prepare the data
df["starttime"] = pd.to_datetime(df["starttime"])
df["endtime"] = pd.to_datetime(df["endtime"])
df["month"] = df["starttime"].dt.month_name()
df["hour"] = df["starttime"].dt.hour

col1, col2 = st.columns(2)

with col1:
    st.subheader("Consumption Distribution by Price Area")

    # Select pricearea as radio buttons
    price_areas = sorted(df["pricearea"].unique())
    selected_pricearea = st.radio("Select a Price Area:", price_areas)

    # Filter by price area
    df_area = df[df["pricearea"] == selected_pricearea]

    # Pie chart: consumption distribution by consumption group
    pie_data = df_area.groupby("consumptiongroup")["quantitykwh"].sum().reset_index()
    
    fig1 = px.pie(
        pie_data, 
        names="consumptiongroup", 
        values="quantitykwh", 
        title=f"Consumption Distribution in {selected_pricearea}",
        hole=0.3
    )
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    st.subheader("Consumption Trend by Production Group")

    # Pills for selecting production groups
    groups = sorted(df["consumptiongroup"].unique())
    selected_groups = st.multiselect(
        "Select Production Groups", groups, default=groups
    )

    # Month selection (dropdown)
    months = sorted(df["month"].unique())
    selected_month = st.selectbox("Select Month:", months)

    # Filter data based on all selections
    df_filtered = df[
        (df["pricearea"] == selected_pricearea)
        & (df["consumptiongroup"].isin(selected_groups))
        & (df["month"] == selected_month)
    ]

    # Group by hour for line chart
    df_line = (
        df_filtered.groupby(["hour", "consumptiongroup"])["quantitykwh"]
        .sum()
        .reset_index()
    )

    # Line chart
    fig2 = go.Figure()
    for group in selected_groups:
        group_data = df_line[df_line["consumptiongroup"] == group]
        fig2.add_trace(
            go.Scatter(
                x=group_data["hour"],
                y=group_data["quantitykwh"],
                mode="lines+markers",
                name=group
            )
        )

    fig2.update_layout(
        title=f"Hourly Consumption in {selected_pricearea} ({selected_month})",
        xaxis_title="Hour of Day",
        yaxis_title="Total Consumption (kWh)",
        xaxis=dict(dtick=1)
    )
    st.plotly_chart(fig2, use_container_width=True)

with st.expander("Data Source Information"):
    st.markdown("""
    **Data Source:**  
    Data is retrieved from the `elhub_data` MongoDB database, 
    that was retrieved from the elhub data api. It is specifically 
    from the `consumption_2021` collection in the MongoDB database.  

    The dataset represents hourly electricity consumption in 2021,  
    grouped by price area and consumption group.
    """)
