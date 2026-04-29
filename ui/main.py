# app.py

import streamlit as st
import pandas as pd
import base64

from dashboard_utils import (
    render_summary_metrics,
    render_map_view,
    render_incident_feed,
    render_analytics,
    convert_df_to_csv,
)
from api_client import fetch_data, post_upload_pdf

# ---------------- CONFIG ----------------
st.set_page_config(
    page_title="Airline Threat Monitor Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
)

CRITICAL_COLOR = "#FF4B4B"

# ---------------- SESSION STATE ----------------
if 'filter_flight' not in st.session_state:
    st.session_state['filter_flight'] = ''
if 'filter_status' not in st.session_state:
    st.session_state['filter_status'] = 'All'

# ---------------- HELPERS ----------------
def display_pdf(file):
    base64_pdf = base64.b64encode(file.getbuffer()).decode("utf-8")
    st.markdown(
        f"""
        <iframe src="data:application/pdf;base64,{base64_pdf}"
                width="100%" height="500"></iframe>
        """,
        unsafe_allow_html=True
    )

# ---------------- SIDEBAR ----------------
with st.sidebar:
    st.markdown(
        f"""
        <h1 style='color: {CRITICAL_COLOR};'>🚨 ALERT</h1>
        <p>Operational Status: <b>Real-Time Monitoring</b></p>
        """,
        unsafe_allow_html=True
    )

    st.markdown("---")
    st.subheader("📄 Upload Threat PDF")

    uploaded_pdf = st.file_uploader(
        "Upload PDF",
        type=["pdf"]
    )

    if uploaded_pdf:
        with st.spinner("Uploading and processing PDF..."):
            response = post_upload_pdf(uploaded_pdf)

        if isinstance(response, dict) and response.get("status") == "success":
            st.success("PDF uploaded and processed successfully")
            st.info(f"🧠 Detected Threat Type: **{response.get('threat_type', 'Unknown')}**")
            display_pdf(uploaded_pdf)
        else:
            st.error(response)

# ---------------- MAIN ----------------
st.title("🚨 Airline Crisis Management")
st.markdown("Real-time monitoring of flight disruptions and automated threat response.")

# ---------------- API DATA ----------------
incident_feed_data = fetch_data("/dashboard/summary")
map_data = fetch_data("/dashboard/map")
status_data = fetch_data("/analytics/status-distribution")
escalation_rate = fetch_data("/analytics/escalation-rate")

if incident_feed_data is None and map_data is None:
    st.warning("Waiting for API connection. Ensure Flask server is running.")
    st.stop()

# ---------------- DASHBOARD ----------------
render_summary_metrics(incident_feed_data)

col_map, col_analytics = st.columns([2, 1])
with col_map:
    render_map_view(map_data)
with col_analytics:
    render_analytics(status_data, escalation_rate)

st.markdown("---")
st.markdown("### 🔍 Incident Search & Filter")

col_search, col_filter, col_download = st.columns([3, 2, 1])

with col_search:
    flight_search = st.text_input(
        "Search Flight Number",
        value=st.session_state['filter_flight'],
        placeholder="F1001"
    )
    st.session_state['filter_flight'] = flight_search

with col_filter:
    try:
        status_options = ['All'] + sorted(
            pd.DataFrame(incident_feed_data)['Status'].unique().tolist()
        )
    except:
        status_options = ['All', 'Cancelled', 'Rerouted', 'Resolved']

    status_filter = st.selectbox("Status", status_options)
    st.session_state['filter_status'] = status_filter

with col_download:
    full_df = pd.DataFrame(incident_feed_data)
    download_df = full_df.copy()

    if st.session_state['filter_flight']:
        download_df = download_df[
            download_df['Flight'].str.contains(
                st.session_state['filter_flight'], case=False, na=False
            )
        ]

    if st.session_state['filter_status'] != 'All':
        download_df = download_df[
            download_df['Status'] == st.session_state['filter_status']
        ]

    csv = convert_df_to_csv(download_df)
    st.download_button(
        "⬇ Download CSV",
        csv,
        "filtered_incidents.csv",
        "text/csv",
        use_container_width=True
    )

# ---------------- INCIDENT FEED ----------------
render_incident_feed(
    incident_feed_data,
    flight_filter=st.session_state['filter_flight'],
    status_filter=st.session_state['filter_status']
)
