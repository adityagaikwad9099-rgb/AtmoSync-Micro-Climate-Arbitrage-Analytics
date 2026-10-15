import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import requests

from datetime import datetime, timedelta



# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="AtmoSync Analytics",
    page_icon="🌦️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# --------------------------------------------------
# CUSTOM CSS
# --------------------------------------------------

st.markdown(
    """
    <style>
        .stApp {
            background-color: #f5f8fc;
        }

        .main-title {
            font-size: 38px;
            font-weight: 800;
            color: #12304a;
        }

        .subtitle {
            color: #64748b;
            font-size: 16px;
        }

        div[data-testid="stMetric"] {
            background-color: white;
            padding: 18px;
            border-radius: 12px;
            border: 1px solid #e2e8f0;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# --------------------------------------------------
# REAL-TIME WEATHER DATA
# --------------------------------------------------

WEATHER_LOCATIONS = {
    "Pune": {"latitude": 18.5204, "longitude": 73.8567},
    "Mumbai": {"latitude": 19.0760, "longitude": 72.8777},
    "Nashik": {"latitude": 19.9975, "longitude": 73.7898},
    "Solapur": {"latitude": 17.6599, "longitude": 75.9064},
}


@st.cache_data(ttl=600, show_spinner=False)
def fetch_current_weather():
    """Fetch current weather observations for four Indian cities."""

    records = []

    for location, coordinates in WEATHER_LOCATIONS.items():
        response = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": coordinates["latitude"],
                "longitude": coordinates["longitude"],
                "current": (
                    "temperature_2m,"
                    "relative_humidity_2m,"
                    "wind_speed_10m"
                ),
            },
            timeout=15,
        )

        response.raise_for_status()

        payload = response.json()
        current = payload.get("current", {})

        temperature = current.get("temperature_2m")
        humidity = current.get("relative_humidity_2m")
        timestamp = current.get("time")

        if temperature is None or humidity is None or timestamp is None:
            continue

        records.append({
            "timestamp": pd.to_datetime(timestamp),
            "location": location,
            "temperature_c": float(temperature),
            "humidity_pct": float(humidity),
            "wind_speed_kmh": float(
                current.get("wind_speed_10m", 0)
            ),
            "solar_irradiance_wm2": 0.0,
        })

    if not records:
        raise ValueError(
            "No current weather observations were returned."
        )

    return pd.DataFrame(records)


# --------------------------------------------------
# SAMPLE DATA GENERATOR
# --------------------------------------------------
# --------------------------------------------------
# SAMPLE DATA GENERATOR
# --------------------------------------------------

def generate_sample_data():

    np.random.seed(42)

    locations = {
        "Pune": {
            "temperature": 29,
            "humidity": 55,
        },
        "Mumbai": {
            "temperature": 32,
            "humidity": 75,
        },
        "Nashik": {
            "temperature": 27,
            "humidity": 48,
        },
        "Solapur": {
            "temperature": 35,
            "humidity": 38,
        },
    }

    records = []

    now = datetime.now()

    for location, values in locations.items():

        for hour in range(48):

            timestamp = now - timedelta(
                hours=47 - hour
            )

            temperature = (
                values["temperature"]
                + 3 * np.sin(hour / 5)
                + np.random.normal(0, 0.8)
            )

            humidity = (
                values["humidity"]
                - 5 * np.sin(hour / 6)
                + np.random.normal(0, 2)
            )

            wind_speed = max(
                0,
                np.random.normal(12, 3)
            )

            solar_irradiance = max(
                0,
                650 * np.sin(
                    np.pi * (hour % 24) / 24
                ) + np.random.normal(0, 30)
            )

            records.append(
                {
                    "timestamp": timestamp,
                    "location": location,
                    "temperature_c": round(
                        temperature, 2
                    ),
                    "humidity_pct": round(
                        np.clip(humidity, 0, 100), 2
                    ),
                    "wind_speed_kmh": round(
                        wind_speed, 2
                    ),
                    "solar_irradiance_wm2": round(
                        solar_irradiance, 2
                    ),
                }
            )

    return pd.DataFrame(records)
    
# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------

st.sidebar.title("AtmoSync")

st.sidebar.caption(
    "Micro-Climate Arbitrage Analytics"
)

st.sidebar.divider()

st.sidebar.subheader("Data Source")

source_mode = st.sidebar.selectbox(
    "Choose data source",
    [
        "Real-Time Weather",
        "Simulated Data",
        "Upload CSV",
    ],
)

uploaded_file = None

if source_mode == "Real-Time Weather":
    st.sidebar.info(
        "Fetch current weather for four Indian cities."
    )

elif source_mode == "Simulated Data":
    st.sidebar.info(
        "Use simulated climate data for demonstration."
    )

else:
    uploaded_file = st.sidebar.file_uploader(
        "Upload climate CSV",
        type=["csv"],
    )

st.sidebar.divider()

st.sidebar.subheader("Alert Settings")

temperature_limit = st.sidebar.slider(
    "High temperature threshold (°C)",
    min_value=20,
    max_value=50,
    value=35,
)

humidity_limit = st.sidebar.slider(
    "High humidity threshold (%)",
    min_value=30,
    max_value=100,
    value=80,
)

st.sidebar.divider()

st.sidebar.subheader("About AtmoSync")

st.sidebar.caption(
    "Micro-climate monitoring and analytics "
    "for multiple Indian cities."
)
# --------------------------------------------------
# LOAD DATA
# --------------------------------------------------

if source_mode == "Upload CSV":

    if uploaded_file is None:
        st.info("Please upload a climate CSV file.")
        st.stop()

    try:
        df = pd.read_csv(uploaded_file)

        required_columns = [
            "timestamp",
            "location",
            "temperature_c",
            "humidity_pct",
        ]

        missing_columns = [
            column
            for column in required_columns
            if column not in df.columns
        ]

        if missing_columns:
            st.error(
                f"Missing required CSV columns: {missing_columns}"
            )
            st.stop()

        df["timestamp"] = pd.to_datetime(
            df["timestamp"],
            errors="coerce",
        )

        numeric_columns = [
            "temperature_c",
            "humidity_pct",
            "wind_speed_kmh",
            "solar_irradiance_wm2",
        ]

        for column in numeric_columns:
            if column in df.columns:
                df[column] = pd.to_numeric(
                    df[column],
                    errors="coerce",
                )

        df["location"] = (
            df["location"].astype("string").str.strip()
        )

        df = df.dropna(
            subset=[
                "timestamp",
                "location",
                "temperature_c",
                "humidity_pct",
            ]
        )

        if df.empty:
            st.error("No valid climate records were found.")
            st.stop()

        data_source = "Uploaded CSV"

    except Exception as error:
        st.error(f"Unable to read the CSV file: {error}")
        st.stop()

elif source_mode == "Real-Time Weather":

    try:
        with st.spinner("Fetching current weather data..."):
            df = fetch_current_weather()

        data_source = "Open-Meteo Real-Time Weather"

    except Exception as error:
        st.warning(
            f"Real-time weather is unavailable. "
            f"Showing simulated data instead. Details: {error}"
        )

        df = generate_sample_data()
        data_source = "Simulated Sample Data (API fallback)"

else:
    df = generate_sample_data()
    data_source = "Simulated Sample Data"

# --------------------------------------------------
# VALIDATE DATA
# --------------------------------------------------

df = df[
    df["location"].notna()
    & (df["location"] != "")
    & df["temperature_c"].between(-60, 60)
    & df["humidity_pct"].between(0, 100)
].copy()

if df.empty:
    st.error("No valid climate data available.")
    st.stop()


# --------------------------------------------------
# HEADER
# --------------------------------------------------

st.markdown(
    '<div class="main-title">'
    'AtmoSync Analytics'
    '</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="subtitle">'
    'Micro-Climate Monitoring, Location Comparison '
    'and Climate Insights'
    '</div>',
    unsafe_allow_html=True,
)

st.caption(
    f"Data source: {data_source} | "
    f"Last dashboard refresh: "
    f"{datetime.now().strftime('%d %b %Y, %I:%M %p')}"
)

st.divider()


# --------------------------------------------------
# FILTERS
# --------------------------------------------------

locations = sorted(
    df["location"].unique().tolist()
)

selected_locations = st.multiselect(
    "Select locations to analyze",
    options=locations,
    default=locations,
)

if not selected_locations:
    st.warning("Please select at least one location.")
    st.stop()

filtered_df = df[
    df["location"].isin(selected_locations)
].copy()


# --------------------------------------------------
# KEY METRICS
# --------------------------------------------------

average_temperature = filtered_df[
    "temperature_c"
].mean()

average_humidity = filtered_df[
    "humidity_pct"
].mean()

location_count = filtered_df[
    "location"
].nunique()

high_temperature_count = (
    filtered_df["temperature_c"] > temperature_limit
).sum()

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Average Temperature",
    f"{average_temperature:.1f} °C",
)

col2.metric(
    "Average Humidity",
    f"{average_humidity:.1f}%",
)

col3.metric(
    "Locations Monitored",
    location_count,
)

col4.metric(
    "High-Temperature Readings",
    int(high_temperature_count),
)


# --------------------------------------------------
# TEMPERATURE TREND
# --------------------------------------------------

st.subheader("📈 Temperature Trends")

temperature_fig = px.line(
    filtered_df.sort_values("timestamp"),
    x="timestamp",
    y="temperature_c",
    color="location",
    markers=True,
    title="Temperature Over Time",
    labels={
        "timestamp": "Time",
        "temperature_c": "Temperature (°C)",
        "location": "Location",
    },
)

temperature_fig.update_layout(
    template="plotly_white",
    hovermode="x unified",
)

st.plotly_chart(
    temperature_fig,
    use_container_width=True,
)


# --------------------------------------------------
# LOCATION COMPARISON
# --------------------------------------------------

st.subheader("📍 Micro-Climate Comparison")

location_summary = (
    filtered_df.groupby("location")
    .agg(
        average_temperature=(
            "temperature_c", "mean"
        ),
        average_humidity=(
            "humidity_pct", "mean"
        ),
        minimum_temperature=(
            "temperature_c", "min"
        ),
        maximum_temperature=(
            "temperature_c", "max"
        ),
        readings=("temperature_c", "count"),
    )
    .reset_index()
)

comparison_fig = px.bar(
    location_summary,
    x="location",
    y="average_temperature",
    color="average_temperature",
    text_auto=".1f",
    title="Average Temperature by Location",
    labels={
        "location": "Location",
        "average_temperature": "Average Temperature (°C)",
    },
    color_continuous_scale="RdYlBu_r",
)

comparison_fig.update_layout(
    template="plotly_white",
    coloraxis_showscale=False,
)

st.plotly_chart(
    comparison_fig,
    use_container_width=True,
)


# --------------------------------------------------
# MICRO-CLIMATE DIFFERENTIAL
# --------------------------------------------------

st.subheader("🔍 Temperature Differential Analysis")

if len(location_summary) >= 2:

    warmest = location_summary.loc[
        location_summary["average_temperature"].idxmax()
    ]

    coolest = location_summary.loc[
        location_summary["average_temperature"].idxmin()
    ]

    temperature_difference = (
        warmest["average_temperature"]
        - coolest["average_temperature"]
    )

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Warmest Location",
        str(warmest["location"]),
        f'{warmest["average_temperature"]:.1f} °C',
    )

    col2.metric(
        "Coolest Location",
        str(coolest["location"]),
        f'{coolest["average_temperature"]:.1f} °C',
    )

    col3.metric(
        "Temperature Difference",
        f"{temperature_difference:.1f} °C",
    )

    st.caption(
        "This difference describes the selected dataset. "
        "It is not, by itself, evidence of a profitable "
        "arbitrage opportunity."
    )

else:

    st.info(
        "Select at least two locations to compare "
        "their average temperatures."
    )


# --------------------------------------------------
# HUMIDITY ANALYSIS
# --------------------------------------------------

st.subheader("💧 Humidity Analysis")

humidity_fig = px.area(
    filtered_df.sort_values("timestamp"),
    x="timestamp",
    y="humidity_pct",
    color="location",
    title="Humidity Trends by Location",
    labels={
        "timestamp": "Time",
        "humidity_pct": "Humidity (%)",
        "location": "Location",
    },
)

humidity_fig.update_layout(
    template="plotly_white",
)

st.plotly_chart(
    humidity_fig,
    use_container_width=True,
)


# --------------------------------------------------
# ALERTS
# --------------------------------------------------

st.subheader("⚠️ Climate Alerts")

temperature_alerts = filtered_df[
    filtered_df["temperature_c"] > temperature_limit
]

humidity_alerts = filtered_df[
    filtered_df["humidity_pct"] > humidity_limit
]

if temperature_alerts.empty and humidity_alerts.empty:

    st.success(
        "No readings exceed the configured thresholds."
    )

else:

    if not temperature_alerts.empty:

        st.warning(
            f"{len(temperature_alerts)} readings exceed "
            f"{temperature_limit} °C."
        )

    if not humidity_alerts.empty:

        st.warning(
            f"{len(humidity_alerts)} readings exceed "
            f"{humidity_limit}% humidity."
        )


# --------------------------------------------------
# DATA TABLE
# --------------------------------------------------

st.subheader("📋 Climate Data Records")

st.dataframe(
    filtered_df.sort_values(
        "timestamp", ascending=False
    ),
    use_container_width=True,
    hide_index=True,
)

csv_data = filtered_df.to_csv(
    index=False
).encode("utf-8")

st.download_button(
    label="Download Climate Data as CSV",
    data=csv_data,
    file_name="atmosync_climate_data.csv",
    mime="text/csv",
)


# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.divider()

st.caption(
    "AtmoSync Analytics | Climate data exploration "
    "and micro-climate comparison"
)