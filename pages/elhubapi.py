import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
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
    pie_data = df_area.groupby("consumptiongroup")["quantitykwh"].sum()

    fig1, ax1 = plt.subplots()
    ax1.pie(pie_data, labels=pie_data.index, autopct="%1.1f%%", startangle=90)
    ax1.axis("equal")
    st.pyplot(fig1)

with col2:
    st.subheader("Consumption Trend by Production Group")

    # Pills for selecting production groups
    groups = sorted(df["consumptiongroup"].unique())
    selected_groups = st.pills(
        "Select Production Groups",
        groups,
        default=groups,
        selection_mode="multi"
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

    # Making the line plot for the the right side of the page
    fig2, ax2 = plt.subplots()
    for group in selected_groups:
        group_data = df_line[df_line["consumptiongroup"] == group]
        ax2.plot(group_data["hour"], group_data["quantitykwh"], label=group)

    ax2.set_xlabel("Hour of Day")
    ax2.set_ylabel("Total Consumption (kWh)")
    ax2.set_title(f"Hourly Consumption in {selected_pricearea} ({selected_month})")
    st.pyplot(fig2)

with st.expander("Data Source Information"):
    st.markdown("""
    **Data Source:**  
    Data is retrieved from the `elhub_data` MongoDB database, 
    that was retrieved from the elhub data api. It is specifically 
    from the `consumption_2021` collection in the MongoDB database.  

    The dataset represents hourly electricity consumption in 2021,  
    grouped by price area and consumption group.
    """)

