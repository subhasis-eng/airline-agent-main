# dashboard_utils.py

import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static

# Define standard colors
CRITICAL_COLOR = "#FF4B4B"  # Red
WARNING_COLOR = "#FFCC00"  # Yellow
OKAY_COLOR = "#00CC99"  # Green
PRIMARY_COLOR = "#F63366"  # Pink


@st.cache_data
def convert_df_to_csv(df):
    """Utility function to convert DataFrame to CSV for the download button."""
    return df.to_csv(index=False).encode("utf-8")


def render_summary_metrics(incident_feed_data):
    """Renders the top-level KPI metrics."""
    if not incident_feed_data:
        st.info("No incident data for metrics.")
        return

    df = pd.DataFrame(incident_feed_data)
    total_incidents = len(df)
    escalated = df[df["Escalated"] == "Yes"].shape[0]
    total_passengers = df["Passengers Affected"].sum()
    escalation_rate = (escalated / total_incidents * 100) if total_incidents else 0

    st.markdown("### 📊 Operational Summary")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            label="No.Incidents Today",
            value=f"{total_incidents:,}",
            delta=f"{escalated} requiring escalation",
            delta_color="normal" if escalated > 0 else "off",
        )

    with col2:
        st.metric(
            label="Escalation Rate",
            value=f"{escalation_rate:.1f}%",
            delta="High Priority",
            delta_color="inverse" if escalation_rate > 10 else "normal",
        )

    with col3:
        st.metric(label="Passengers Affected", value=f"{total_passengers:,}")
    st.markdown("---")


# dashboard_utils.py (Revised _create_map_with_markers)

# ... (imports and previous functions) ...


@st.cache_data(show_spinner=False)
def _create_map_with_markers(df_map):
    """
    Creates the Folium map object and adds all markers.
    Now accepts a DataFrame directly.
    """
    if df_map.empty:
        return folium.Map(location=[20, 0], zoom_start=2, control_scale=True)

    required_cols = ["latitude", "longitude"]

    # 1. Ensure required columns exist (Defensive check)
    if any(col not in df_map.columns for col in required_cols):
        st.error(
            f"Map data missing required columns: {required_cols}. Check API output."
        )
        return folium.Map(location=[20, 0], zoom_start=2, control_scale=True)

    # 2. Drop rows with missing coordinates
    # THIS LINE WILL NOW WORK because df_map has the correct column names
    valid_df = df_map.dropna(subset=required_cols)

    if valid_df.empty:
        st.info("No valid coordinates to plot on the map.")
        return folium.Map(location=[20, 0], zoom_start=2, control_scale=True)

    # Calculate center based on valid data
    center_lat = valid_df["latitude"].mean()
    center_lon = valid_df["longitude"].mean()

    m = folium.Map(location=[center_lat, center_lon], zoom_start=2, control_scale=True)

    # 3. Add Markers
    for _, row in valid_df.iterrows():
        # ... (Marker logic remains the same, using 'latitude' and 'longitude')
        if row["event_type"] == "Bomb Threat":
            color = "red"
        elif row["status"] == "Rerouted":
            color = "orange"
        else:
            color = "blue"

        popup_html = f"""
        **Flight:** {row.get('flight_number', 'N/A')}<br>
        **City:** {row.get('city', 'N/A')}<br>
        **Event:** {row['event_type']}<br>
        **Status:** **{row['status']}**<br>
        **Affected:** {row['affected_passengers']} Pax
        """

        folium.Marker(
            location=[row["latitude"], row["longitude"]],
            popup=popup_html,
            icon=folium.Icon(color=color, icon="plane", prefix="fa"),
        ).add_to(m)

    return m


def render_map_view(map_data):
    """Renders the disruption map using cached Folium object."""
    st.markdown("### 🗺️ Real-Time Disruption Map")

    if not map_data:
        st.info("Map data loading or unavailable.")
        folium_static(folium.Map(location=[20, 0], zoom_start=2), width=900, height=500)
        return

    # 1. Create the DataFrame immediately
    df_map = pd.DataFrame(map_data)

    # 2. Call the cached function with the DataFrame
    # Note: Streamlit handles caching of DataFrame inputs automatically since v1.18.0.
    m = _create_map_with_markers(df_map)

    folium_static(m, width=900, height=500)


# dashboard_utils.py (MODIFIED for older Streamlit versions)


def render_incident_feed(incident_feed_data, flight_filter: str, status_filter: str):
    """Renders the detailed incident list, applying dynamic filters."""
    st.markdown("### 🚨 Incident Feed Table")

    if incident_feed_data:
        df = pd.DataFrame(incident_feed_data)

        # --- 1. Apply Filtering ---
        filtered_df = df.copy()

        # ... (Filtering logic remains here) ...
        if flight_filter:
            filtered_df = filtered_df[
                filtered_df["Flight"].str.contains(flight_filter, case=False, na=False)
            ]
        if status_filter != "All":
            filtered_df = filtered_df[filtered_df["Status"] == status_filter]

        # --- 2. Render Filtered Data ---
        if not filtered_df.empty:
            st.dataframe(
                filtered_df,
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("No active incidents match your current filters.")
    else:
        st.info("No active incidents to display.")
    st.markdown("---")


def render_analytics(status_data, escalation_rate):
    """Renders the analytics visualizations."""
    st.markdown("### 📈 Analytics")

    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown("**Status Distribution**")
        if status_data:
            df_status = pd.DataFrame(status_data.items(), columns=["Status", "Count"])
            st.bar_chart(df_status.set_index("Status"), color=PRIMARY_COLOR)
        else:
            st.info("No status data.")

    with col2:
        st.markdown("**Escalation Trend**")
        if escalation_rate:
            rate = escalation_rate.get("Escalation Rate (%)", 0)
            st.progress(rate / 100, text=f"Current Escalation Rate: **{rate:.1f}%**")
            st.info(f"The current rate of manual intervention is **{rate:.1f}%**.")
        else:
            st.info("No escalation rate data.")
