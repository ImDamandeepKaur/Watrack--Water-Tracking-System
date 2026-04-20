import streamlit as st
import pandas as pd
from db import Database
from model import Model
from utils import Analytics
import plotly.express as px

st.set_page_config(layout="wide")

db = Database()
db.create_table()

model_obj = Model()
analytics = Analytics()

st.title("💧 Watrack - Smart Dashboard")

user_id = st.number_input("User ID", min_value=1)
region = st.selectbox("Region", ["North","South","East","West"])

# -------- LOAD DATA --------
data = db.fetch_data(user_id)

if data:
    df = pd.DataFrame(data, columns=[
        "user_id","date","meter_reading","daily_usage","region"
    ])
    df = analytics.preprocess(df)

    # -------- KPI --------
    kpi = analytics.kpis(df)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("💧 Total", f"{kpi['total']:.0f}")
    col2.metric("📊 Avg", f"{kpi['avg']:.0f}")
    col3.metric("📅 Days", kpi['days'])
    col4.metric("⚡ Latest", f"{kpi['latest']:.0f}")

    # -------- CHARTS --------
    col1, col2 = st.columns(2)

    with col1:
        fig1 = px.line(df, x='date', y='daily_usage', markers=True)
        st.plotly_chart(fig1)

    with col2:
        fig2 = px.bar(df, x='date', y='daily_usage', color='daily_usage')
        st.plotly_chart(fig2)

    # Moving average
    df['moving_avg'] = df['daily_usage'].rolling(3).mean()
    fig3 = px.line(df, x='date', y=['daily_usage','moving_avg'])
    st.plotly_chart(fig3)

    # Histogram
    fig4 = px.histogram(df, x='daily_usage')
    st.plotly_chart(fig4)

    # -------- INSIGHTS --------
    max_day, min_day = analytics.insights(df)

    st.info(f"🔥 Max: {max_day['daily_usage']} on {max_day['date']}")
    st.info(f"💧 Min: {min_day['daily_usage']} on {min_day['date']}")

    # -------- RESET --------
    if st.button("🗑️ Reset My Data"):
        db.delete_user(user_id)
        st.success("Data deleted")

    # -------- TRAIN --------
    if st.button("Train Model"):
        model_obj.train(df)
        st.success("Model trained")

    # -------- PREDICT --------
    if st.button("Predict"):
        model = model_obj.load()

        if model is None:
            model_obj.train(df)
            model = model_obj.load()

        pred = model_obj.predict(model, df)
        st.success(f"Prediction: {pred:.2f}")

else:
    st.warning("No data available")
