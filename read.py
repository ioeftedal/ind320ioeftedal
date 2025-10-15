import pandas as pd
import streamlit as st

# Read the csv file and convert the date to datetime format so we can process it later
@st.cache_data
def read_csv_file(filepath: str) -> pd.DataFrame:
    df = pd.read_csv(f"{filepath}")

    df['time'] = pd.to_datetime(df['time'], format='%Y-%m-%dT%H:%M')
    df['time_str'] = df['time'].apply(str)

    return df

# Filter dataframe by month number (1-12). If month is 0 the entire year is returned
def filter_by_month(df: pd.DataFrame, month: int) -> pd.DataFrame:
    if month == 0:
        return df
    return df[df['time'].dt.month == month]

def get_month_options() -> list:
    return [
        "All Months",
        "January",
        "February", 
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December"
    ]

def get_month_number(month_name: str) -> int:
    months = get_month_options()
    return months.index(month_name)
