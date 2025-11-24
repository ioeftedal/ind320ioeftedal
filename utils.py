import openmeteo_requests
import requests_cache

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

from retry_requests import retry
from scipy.fftpack import dct, idct
from statsmodels.tsa.seasonal import STL
from sklearn.neighbors import LocalOutlierFactor
from scipy.signal import spectrogram

# Setup the Open-Meteo API client with cache and retry on error
cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
openmeteo = openmeteo_requests.Client(session = retry_session)

def save_data(latitude: float, longitude: float, year) -> pd.DataFrame:
    # Make sure all required weather variables are listed here
    # The order of variables in hourly or daily is important to assign them correctly below
    """ Change the url to fetch the data we need"""
    url = "https://archive-api.open-meteo.com/v1/era5"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": [
            "temperature_2m",
            "precipitation",
            "wind_speed_10m",
            "wind_gusts_10m",
            "wind_direction_10m"
        ],
        "models": "era5",
        "start_date": f"{year}-01-01",
        "end_date": f"{year}-12-31",
    }
    responses = openmeteo.weather_api(url, params=params)

    # Process first location. Add a for-loop for multiple locations or weather models
    response = responses[0]
    print(f"Coordinates: {response.Latitude()}°N {response.Longitude()}°E")
    print(f"Elevation: {response.Elevation()} m asl")
    print(f"Timezone difference to GMT+0: {response.UtcOffsetSeconds()}s")

    # Process hourly data. The order of variables needs to be the same as requested.
    hourly = response.Hourly()
    hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()
    hourly_precipication = hourly.Variables(1).ValuesAsNumpy()
    hourly_wind_speed_10m = hourly.Variables(2).ValuesAsNumpy()
    hourly_wind_gusts_10m = hourly.Variables(3).ValuesAsNumpy()
    hourly_wind_direction_10m = hourly.Variables(4).ValuesAsNumpy()

    hourly_data = {"date": pd.date_range(
        start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
        end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
        freq=pd.Timedelta(seconds=hourly.Interval()),
        inclusive="left"
    ), "temperature_2m": hourly_temperature_2m, "precipication": hourly_precipication,
        "wind_speed_10m": hourly_wind_speed_10m, "wind_gusts_10m": hourly_wind_gusts_10m,
        "wind_direction_10m": hourly_wind_direction_10m}

    hourly_dataframe = pd.DataFrame(data = hourly_data)

    return hourly_dataframe

# Temperature Outlier Detection
def detect_temperature_outliers(df, temp_col='temperature_2m', cutoff=100, std_mult=2):
    """
    Detect temperature outliers using DCT + Robust SPC.
    Returns a figure, axes, and summary DataFrame.
    """
    df = df.copy().sort_values('date')
    time = pd.to_datetime(df['date'])
    temp = df[temp_col].values

    # DCT decomposition
    dct_coeff = dct(temp, norm='ortho')
    dct_low = np.copy(dct_coeff)
    dct_low[cutoff:] = 0
    trend = idct(dct_low, norm='ortho')
    satv = temp - trend

    # Robust statistics
    med_satv = np.median(satv)
    mad_satv = np.median(np.abs(satv - med_satv))

    # Correct robust sigma (normal-consistent)
    robust_sigma = 1.4826 * mad_satv

    # Correct SPC-like control limits
    upper_band = trend + std_mult * robust_sigma
    lower_band = trend - std_mult * robust_sigma

    # Detect outliers
    mask_temp_out = (temp > upper_band) | (temp < lower_band)
    temp_outliers = df.loc[mask_temp_out, ['date', temp_col]]

    # Plot
    fig, ax = plt.subplots(figsize=(14, 6))
    ax.plot(time, temp, label='Temperature (°C)', color='tab:blue', alpha=0.8)
    ax.plot(time, trend, color='orange', label='Trend (low-freq)')
    ax.plot(time, upper_band, 'g--', label=f'+{std_mult}σ (robust)')
    ax.plot(time, lower_band, 'g--')
    ax.scatter(temp_outliers['date'], temp_outliers[temp_col], color='red', label='Outliers', zorder=5)
    ax.fill_between(time, lower_band, upper_band, color='green', alpha=0.1)
    ax.set_title('Temperature Outlier Detection (DCT + Robust SPC)')
    ax.set_ylabel('Temperature (°C)')
    ax.legend()
    ax.grid(True, linestyle='--', alpha=0.4)

    summaries = {'temperature_outliers': temp_outliers}
    return fig, ax, summaries

# Precipitation Anomaly Detection
def detect_precipitation_anomalies(df, precip_col='precipication', lof_frac=0.01):
    """
    Detect precipitation anomalies using Local Outlier Factor (LOF).
    Returns a figure, axes, and summary DataFrame.
    """
    df = df.copy().sort_values('date')
    time = pd.to_datetime(df['date'])
    precip = df[precip_col].values.reshape(-1, 1)

    lof = LocalOutlierFactor(contamination=lof_frac)
    labels = lof.fit_predict(precip)
    mask_precip_out = labels == -1
    precip_outliers = df.loc[mask_precip_out, ['date', precip_col]]

    # Plot
    fig, ax = plt.subplots(figsize=(14, 6))
    ax.plot(time, df[precip_col], color='tab:gray', label='Precipitation')
    ax.scatter(precip_outliers['date'], precip_outliers[precip_col],
               color='red', label='LOF anomalies', zorder=5)
    ax.set_title('Precipitation Anomaly Detection (Local Outlier Factor)')
    ax.set_ylabel('Precipitation (mm)')
    ax.set_xlabel('Date')
    ax.legend()
    ax.grid(True, linestyle='--', alpha=0.4)

    summaries = {'precip_anomalies': precip_outliers}
    return fig, ax, summaries

def decompose_production_stl(df,
    area='NO1',
    group='hydro',
    period=24,
    seasonal=7,
    trend=73,
    robust=True,
    figsize=(16, 10)):
    """
    Perform STL decomposition (Seasonal-Trend decomposition using LOESS)
    on Elhub production data and plot results.
    """

    # Filter Data (if needed)
    df = df.copy()
    if 'area' in df.columns:
        df = df[df['area'] == area]
    if 'group' in df.columns:
        df = df[df['group'] == group]

    # Assume 'value' is the production measurement column
    value_col = 'value' if 'value' in df.columns else 'temperature_2m'
    df = df.sort_values('date')
    df['date'] = pd.to_datetime(df['date'])
    df = df.set_index('date')

    # STL decomposition
    stl = STL(df[value_col], period=period,
        seasonal=seasonal, trend=trend, robust=robust)
    result = stl.fit()

    # Plot
    fig = result.plot()
    fig.set_size_inches(figsize)
    fig.suptitle(f"STL Decomposition for {group} in {area}", fontsize=16)
    fig.tight_layout()

    return fig, result

def plot_production_spectrogram(df: pd.DataFrame,
    area: str ='NO1',
    group: str ='hydro',
    window_length=256,
    overlap=128):
    """
    Create and plot a spectrogram of Elhub production data.
    """

    df = df.copy()
    if 'area' in df.columns:
        df = df[df['area'] == area]
    if 'group' in df.columns:
        df = df[df['group'] == group]

    value_col = 'value' if 'value' in df.columns else 'temperature_2m'
    df = df.sort_values('date')
    values = df[value_col].values

    #Compute spectrogram
    fs = 1  # sampling frequency (1 sample per hour if hourly)
    f, t, Sxx = spectrogram(values, fs=fs,
    nperseg=window_length,
    noverlap=overlap,
    scaling='density')

    # Plot
    fig, ax = plt.subplots(figsize=(12, 6))
    pcm = ax.pcolormesh(t, f, 10 * np.log10(Sxx + 1e-12),
        shading='gouraud', cmap='viridis')
    ax.set_ylabel('Frequency [cycles/hour]')
    ax.set_xlabel('Time [samples]')
    ax.set_title(f"Spectrogram of {group} in {area}")
    fig.colorbar(pcm, ax=ax, label='Power (dB)')
    fig.tight_layout()

    return fig, (f, t, Sxx)
