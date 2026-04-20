import streamlit as st
import pandas as pd
from db import Database
from utils import Analytics
import plotly.express as px

def show_dashboard():

    db = Database()
    analytics = Analytics()

    st.subheader("📊 Dashboard")

    user_id = st.sidebar.number_input("User ID", min_value=1)

    data = db.fetch_data(user_id)

    if not data:
        st.warning("No data available")
        return

    df = pd.DataFrame(data, columns=[
        "user_id","date","meter_reading","daily_usage","region"
    ])

    df = analytics.preprocess(df)

    # ✅ sort data
    df = df.sort_values(by='date')

    # -------- KPI --------
    kpi = analytics.kpis(df)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("💧 Total Usage", f"{kpi['total']:.0f}")
    col2.metric("📊 Avg Usage", f"{kpi['avg']:.0f}")
    col3.metric("📅 Days", kpi['days'])
    col4.metric("⚡ Latest", f"{df.iloc[-1]['daily_usage']:.0f}")

    # -------- DATE FILTER --------
    st.subheader("📅 Select Date Range")

    start, end = st.date_input(
        "Choose range",
        [df['date'].min(), df['date'].max()]
    )

    filtered_df = df[
        (df['date'] >= pd.to_datetime(start)) &
        (df['date'] <= pd.to_datetime(end))
    ]

    # ✅ handle empty/zero data
    if len(filtered_df) == 0 or filtered_df['daily_usage'].sum() == 0:
        st.warning("No valid usage data in selected range")
        return

    # -------- LINE CHART --------
    st.subheader("📈 Usage Trend")
    st.caption("Shows water usage over time")

    fig_line = px.line(
        filtered_df,
        x='date',
        y='daily_usage',
        markers=True
    )
    st.plotly_chart(fig_line, use_container_width=True)

    # -------- BAR CHART --------
    st.subheader("📊 Daily Comparison")
    st.caption("Compare usage day-by-day")

    fig_bar = px.bar(
        filtered_df,
        x='date',
        y='daily_usage'
    )
    st.plotly_chart(fig_bar, use_container_width=True)

    # -------- INSIGHTS --------
    st.subheader("📌 Insights")

    max_day = filtered_df.loc[filtered_df['daily_usage'].idxmax()]
    min_day = filtered_df.loc[filtered_df['daily_usage'].idxmin()]

    st.info(f"🔥 Highest usage: {max_day['daily_usage']} L on {max_day['date'].date()}")
    st.info(f"💧 Lowest usage: {min_day['daily_usage']} L on {min_day['date'].date()}")

    # -------- RESET --------
    if st.button("🗑️ Reset My Data"):
        db.delete_user(user_id)
        st.success("Data deleted")
        st.rerun()
