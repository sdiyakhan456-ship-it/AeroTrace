import streamlit as st
import pandas as pd
import snowflake.connector

st.set_page_config(
    page_title="AeroTrace",
    page_icon="🌍",
    layout="wide"
)

# =====================================================
# SNOWFLAKE CONNECTION
# =====================================================

def get_connection():
    s = st.secrets["snowflake"]

    return snowflake.connector.connect(
        account=s["account"],
        user=s["user"],
        password=s["password"],
        warehouse=s["warehouse"],
        database=s["database"],
        schema=s["schema"],
        role=s["role"],
        client_session_keep_alive=True
    )


def run_query(query):
    conn = get_connection()

    try:
        return pd.read_sql(query, conn)
    finally:
        conn.close()


# =====================================================
# HEADER
# =====================================================

st.title("🌍 AeroTrace")
st.subheader("Air Pollution Source Detection & Risk Analysis")

st.divider()


# =====================================================
# CITY SELECTION
# =====================================================

st.markdown("## 📍 Select City / Area")

city = st.selectbox(
    "Choose a city",
    ["Lucknow", "Delhi", "Kanpur", "Mumbai"]
)

st.write("Selected Area:", city)


# =====================================================
# TOP KPI CARDS
# =====================================================

if city == "Lucknow":

    latest_query = """
    SELECT
        POLLUTANT,
        VALUE,
        UNIT,
        DATETIME_LOCAL
    FROM AEROTRACE_DB.RAW.AEROTRACE_AIR_QUALITY_ENRICHED
    WHERE LOWER(POLLUTANT) IN
        ('pm25','pm10','no2','co','so2','o3')
    QUALIFY ROW_NUMBER() OVER (
        PARTITION BY LOWER(POLLUTANT)
        ORDER BY DATETIME_LOCAL DESC
    ) = 1
    """

    latest_data = run_query(latest_query)

    def get_value(name):
        row = latest_data[
            latest_data["POLLUTANT"].str.lower() == name
        ]

        if not row.empty:
            return row.iloc[0]["VALUE"]

        return None

    pm25 = get_value("pm25")
    pm10 = get_value("pm10")
    no2 = get_value("no2")

    weather_latest_query = """
    SELECT
        wind_speed
    FROM AEROTRACE_DB.RAW.AEROTRACE_WEATHER_HISTORICAL
    ORDER BY datetime_local DESC
    LIMIT 1
    """

    wind_data = run_query(weather_latest_query)

    wind = None

    if not wind_data.empty:
        wind = wind_data.iloc[0]["WIND_SPEED"]

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "🌫️ PM2.5",
        f"{pm25:.2f}" if pm25 is not None else "N/A"
    )

    c2.metric(
        "🌫️ PM10",
        f"{pm10:.2f}" if pm10 is not None else "N/A"
    )

    c3.metric(
        "🚗 NO₂",
        f"{no2:.2f}" if no2 is not None else "N/A"
    )

    c4.metric(
        "💨 Wind Speed",
        f"{wind:.2f} m/s" if wind is not None else "N/A"
    )


st.divider()


# =====================================================
# INTERACTIVE POLLUTION MAP
# =====================================================

st.markdown("## 🗺️ Interactive Pollution Map")

if city == "Lucknow":

    map_query = """
    SELECT
        hotspot_latitude AS "latitude",
        hotspot_longitude AS "longitude"
    FROM AEROTRACE_DB.ANALYTICS.POLLUTION_HOTSPOTS
    """

    map_data = run_query(map_query)

    if not map_data.empty:

        st.map(
            map_data[["latitude", "longitude"]],
            zoom=10
        )

        st.caption(
            "📍 Pollution hotspots detected from AeroTrace air-quality data."
        )

    else:
        st.info("No hotspot locations available.")

else:

    st.info(
        "Pollution map data for this city will be connected next."
    )


st.divider()


# =====================================================
# POLLUTION MONITORING
# =====================================================

st.markdown("## 📊 Pollution Monitoring")

if city == "Lucknow":

    pollution_query = """
    SELECT
        datetime_local,
        pollutant,
        value,
        unit,
        latitude,
        longitude
    FROM AEROTRACE_DB.CLEAN.AIR_QUALITY_CLEAN
    ORDER BY datetime_local DESC
    LIMIT 50
    """

    pollution = run_query(pollution_query)

    if not pollution.empty:

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "Measurements",
            len(pollution)
        )

        c2.metric(
            "Pollutants",
            pollution["POLLUTANT"].nunique()
        )

        c3.metric(
            "Latest Reading",
            str(pollution["DATETIME_LOCAL"].max())
        )

        st.dataframe(
            pollution,
            use_container_width=True
        )

    else:
        st.info("No pollution data available.")

else:
    st.info("Pollution monitoring will be connected for this city.")


# =====================================================
# HOTSPOT DETECTION
# =====================================================

st.markdown("## 🔥 Hotspot Detection")

if city == "Lucknow":

    hotspot_query = """
    SELECT
        hotspot_latitude,
        hotspot_longitude,
        pollutant,
        avg_pollution,
        measurements
    FROM AEROTRACE_DB.ANALYTICS.POLLUTION_HOTSPOTS
    ORDER BY avg_pollution DESC
    LIMIT 10
    """

    hotspots = run_query(hotspot_query)

    if not hotspots.empty:

        st.markdown("### 🔥 Top Pollution Hotspots")

        chart_hotspots = hotspots.copy()

        chart_hotspots["HOTSPOT"] = (
            chart_hotspots["HOTSPOT_LATITUDE"].round(3).astype(str)
            + ", "
            + chart_hotspots["HOTSPOT_LONGITUDE"].round(3).astype(str)
        )

        st.bar_chart(
            chart_hotspots.set_index("HOTSPOT")["AVG_POLLUTION"]
        )

        st.dataframe(
            hotspots,
            use_container_width=True
        )

    else:
        st.info("No pollution hotspots detected.")

else:
    st.info("Hotspot detection will be connected for this city.")


# =====================================================
# SPIKE DETECTION
# =====================================================

st.markdown("## 📈 Spike Detection")

if city == "Lucknow":

    spike_query = """
    SELECT
        datetime_local,
        pollutant,
        value,
        previous_value,
        increase_percent,
        latitude,
        longitude
    FROM AEROTRACE_DB.ANALYTICS.POLLUTION_SPIKES
    ORDER BY increase_percent DESC
    LIMIT 10
    """

    spikes = run_query(spike_query)

    if not spikes.empty:

        st.markdown("### ⚡ Detected Pollution Spikes")

        st.dataframe(
            spikes,
            use_container_width=True
        )

    else:
        st.info("No significant pollution spikes detected.")

else:
    st.info("Spike detection will be connected for this city.")


# =====================================================
# SOURCE ANALYSIS
# =====================================================

st.markdown("## 🔎 Source Analysis")

if city == "Lucknow":

    source_query = """
    SELECT
        hotspot_latitude,
        hotspot_longitude,
        pollutant,
        avg_pollution,
        feature_type,
        nearby_features
    FROM AEROTRACE_DB.ANALYTICS.HOTSPOT_SOURCE_CONTEXT
    ORDER BY avg_pollution DESC, nearby_features DESC
    LIMIT 15
    """

    sources = run_query(source_query)

    if not sources.empty:

        st.markdown("### 🔎 Nearby Source Categories")

        source_chart = (
            sources
            .groupby("FEATURE_TYPE")["AVG_POLLUTION"]
            .mean()
            .sort_values(ascending=False)
        )

        st.bar_chart(source_chart)

        st.dataframe(
            sources,
            use_container_width=True
        )

        st.caption(
            "Source categories represent nearby mapped features "
            "and spatial clues. They do not establish causation."
        )

    else:
        st.info("No source context available.")

else:
    st.info("Source analysis will be connected for this city.")


# =====================================================
# WEATHER & WIND
# =====================================================

st.markdown("## 🌬️ Weather & Wind Context")

if city == "Lucknow":

    weather_query = """
    SELECT
        datetime_local,
        temperature,
        relative_humidity,
        precipitation,
        wind_speed,
        wind_direction,
        surface_pressure
    FROM AEROTRACE_DB.RAW.AEROTRACE_WEATHER_HISTORICAL
    ORDER BY datetime_local ASC
    """

    weather = run_query(weather_query)

    if not weather.empty:

        latest = weather.iloc[-1]

        c1, c2, c3, c4 = st.columns(4)

        c1.metric(
            "🌡️ Temperature",
            f"{latest['TEMPERATURE']} °C"
        )

        c2.metric(
            "💧 Humidity",
            f"{latest['RELATIVE_HUMIDITY']} %"
        )

        c3.metric(
            "💨 Wind Speed",
            f"{latest['WIND_SPEED']}"
        )

        c4.metric(
            "🧭 Wind Direction",
            f"{latest['WIND_DIRECTION']}°"
        )

        st.markdown("### 🌬️ Weather Trend")

        weather_chart = weather[
            [
                "DATETIME_LOCAL",
                "WIND_SPEED",
                "TEMPERATURE"
            ]
        ].copy()

        weather_chart = weather_chart.set_index(
            "DATETIME_LOCAL"
        )

        st.line_chart(
            weather_chart
        )

        st.dataframe(
            weather.tail(10),
            use_container_width=True
        )

    else:
        st.info("Weather data unavailable.")

else:
    st.info("Weather data will be connected for this city.")


# =====================================================
# POPULATION EXPOSURE
# =====================================================

st.markdown("## 👥 Population Exposure")

if city == "Lucknow":

    population_query = """
    SELECT
        area_name,
        ward_id,
        population,
        exposure_population_level
    FROM AEROTRACE_DB.ANALYTICS.POPULATION_EXPOSURE
    ORDER BY population DESC
    LIMIT 15
    """

    population = run_query(population_query)

    if not population.empty:

        st.dataframe(
            population,
            use_container_width=True
        )

        st.caption(
            "Population level indicates population size by urban ward; "
            "it is not a direct estimate of pollution exposure."
        )

    else:
        st.info("Population data unavailable.")

else:
    st.info("Population exposure will be connected for this city.")


# =====================================================
# SIMILAR EVENT DETECTION
# =====================================================

st.markdown("## 🔍 Similar Event Detection")

if city == "Lucknow":

    event_query = """
    SELECT
        datetime_local,
        latitude,
        longitude,
        avg_pollution,
        avg_temperature,
        avg_humidity,
        avg_wind_speed,
        avg_wind_direction
    FROM AEROTRACE_DB.ANALYTICS.POLLUTION_EVENT_SIGNATURE
    ORDER BY avg_pollution DESC
    LIMIT 10
    """

    events = run_query(event_query)

    if not events.empty:

        st.markdown("### 🔍 Historical Event Signatures")

        st.dataframe(
            events,
            use_container_width=True
        )

        st.caption(
            "These signatures can be used to compare future pollution "
            "events with historical patterns."
        )

    else:
        st.info("No event signatures available.")

else:
    st.info("Similar event detection will be connected for this city.")


# =====================================================
# SMART ALERTS + RISK
# =====================================================

st.markdown("## 🚨 Smart Alerts + Risk Analysis")

if city == "Lucknow":

    risk_query = """
    SELECT
        hotspot_latitude,
        hotspot_longitude,
        pollutant,
        avg_pollution,
        increase_percent,
        temperature,
        relative_humidity,
        wind_speed,
        wind_direction,
        risk_level
    FROM AEROTRACE_DB.ANALYTICS.SMART_RISK_SIGNALS
    ORDER BY
        CASE risk_level
            WHEN 'HIGH' THEN 1
            WHEN 'MEDIUM' THEN 2
            WHEN 'LOW' THEN 3
            ELSE 4
        END,
        avg_pollution DESC
    LIMIT 15
    """

    risks = run_query(risk_query)

    if not risks.empty:

        st.markdown("### 🚨 Risk Distribution")

        risk_counts = (
            risks["RISK_LEVEL"]
            .value_counts()
        )

        st.bar_chart(risk_counts)

        st.markdown("### Active Risk Signals")

        st.dataframe(
            risks,
            use_container_width=True
        )

        st.caption(
            "Risk level is a data-driven monitoring signal based on "
            "pollution and environmental context. It is not a medical "
            "or public-health risk assessment."
        )

    else:
        st.info("No active risk signals.")

else:
    st.info("Smart alerts will be connected for this city.")


# =====================================================
# PM2.5 SHORT-TERM ESTIMATE
# =====================================================

st.markdown("## 🔮 PM2.5 Short-Term Estimate")

if city == "Lucknow":

    forecast_query = """
    SELECT
        FORECAST_BASE_TIME,
        CURRENT_PM25,
        AVG_PM25,
        PREDICTED_PM25,
        FORECAST_NOTE
    FROM AEROTRACE_DB.ANALYTICS.PM25_FORECAST
    ORDER BY FORECAST_BASE_TIME DESC
    LIMIT 1
    """

    try:

        forecast = run_query(forecast_query)

        if not forecast.empty:

            predicted = forecast.iloc[0]["PREDICTED_PM25"]

            st.metric(
                "🔮 Estimated Next PM2.5",
                f"{predicted} µg/m³"
            )

            st.caption(
                forecast.iloc[0]["FORECAST_NOTE"]
            )

        else:
            st.info("No PM2.5 estimate available.")

    except Exception:
        st.info(
            "PM2.5 estimate is not available yet."
        )

# =====================================================
# POLLUTION SOURCE DETECTION CASE STUDY
# =====================================================

st.markdown("## 📚 Air Pollution Source Detection Case Study")

st.caption(
    "Combining air-quality, weather and road/traffic-context data "
    "to identify pollution source clues."
)

if city == "Lucknow":

    case_query = """
    SELECT
        DATETIME_LOCAL,
        PM25,
        PM10,
        NO2,
        CO,
        SO2,
        O3,
        TEMPERATURE,
        RELATIVE_HUMIDITY,
        WIND_SPEED,
        WIND_DIRECTION,
        NEARBY_ROAD_FEATURES,
        CASE_STUDY_FINDING
    FROM AEROTRACE_DB.ANALYTICS.POLLUTION_CASE_STUDY
    ORDER BY DATETIME_LOCAL DESC
    """

    case_data = run_query(case_query)

    if not case_data.empty:

        latest_case = case_data.iloc[0]

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "PM2.5",
            f"{latest_case['PM25']:.2f}"
        )

        c2.metric(
            "PM10",
            f"{latest_case['PM10']:.2f}"
        )

        c3.metric(
            "NO₂",
            f"{latest_case['NO2']:.2f}"
        )

        st.markdown("### 🔍 Case Study Finding")

        st.info(
            str(latest_case["CASE_STUDY_FINDING"])
        )

        st.markdown("### 🌬️ Environmental Context")

        st.write(
            f"Temperature: {latest_case['TEMPERATURE']} °C  |  "
            f"Humidity: {latest_case['RELATIVE_HUMIDITY']} %  |  "
            f"Wind Speed: {latest_case['WIND_SPEED']} m/s  |  "
            f"Wind Direction: {latest_case['WIND_DIRECTION']}°"
        )

        st.markdown("### 🚗 Road / Traffic Context")

        st.write(
            f"Nearby mapped road features: "
            f"**{latest_case['NEARBY_ROAD_FEATURES']}**"
        )

        st.dataframe(
            case_data,
            use_container_width=True
        )

        st.caption(
            "Road features provide spatial context only. "
            "They do not prove that traffic caused the observed pollution."
        )

    else:
        st.info("No case-study data available.")
    # =====================================================
# ASK AEROTRACE
# =====================================================

st.markdown("## 🤖 Ask AeroTrace")

if city == "Lucknow":

    ai_query = """
    SELECT
        AI_INSIGHT,
        DATETIME_LOCAL
    FROM AEROTRACE_DB.ANALYTICS.AEROTRACE_AI_LAB
    ORDER BY DATETIME_LOCAL DESC
    LIMIT 1
    """

    ai_data = run_query(ai_query)

    if not ai_data.empty:

        st.markdown("### 🧠 AI-Generated Pollution Analysis")

        ai_text = str(
            ai_data.iloc[0]["AI_INSIGHT"]
        )

        ai_text = ai_text.replace(
            "\\n",
            "\n"
        )

        ai_text = ai_text.strip().strip('"')

        st.markdown(ai_text)

        st.caption(
            "AI analysis is generated from AeroTrace pollution, "
            "weather and spatial-source context. It provides "
            "source clues and monitoring insights, not proof of causation."
        )

    else:
        st.info("No AI insight available.")

else:
    st.info(
        "AI analysis is currently connected to the Lucknow dataset."
    )


# =====================================================
# FOOTER
# =====================================================

st.divider()

st.markdown(
    "🌍 **AeroTrace** — Monitor → Locate Hotspot → "
    "Detect Spike → Investigate Source → Assess Exposure → Respond"
)
