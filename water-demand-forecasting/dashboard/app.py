import streamlit as st
import psycopg2
import pandas as pd
import numpy as np
from datetime import datetime
import pickle
from xgboost import XGBRegressor
import os
import plotly.express as px

# ---------------- CONFIG ----------------
st.set_page_config(page_title="Watrack", layout="wide")

# ---------------- DB CONNECTION ----------------
def get_db():
    return psycopg2.connect(os.getenv("DATABASE_URL"))

# ---------------- MODEL PATH ----------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, "models")
os.makedirs(MODEL_DIR, exist_ok=True)
MODEL_FILE = os.path.join(MODEL_DIR, "xgb_model.pkl")

# ---------------- LOAD MODEL (NO CACHE NOW) ----------------
def load_model():
    if os.path.exists(MODEL_FILE):
        with open(MODEL_FILE, "rb") as f:
            return pickle.load(f)
    return None

# ---------------- INIT DB ----------------
def init_db():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS water_usage (
            user_id INTEGER,
            date TEXT,
            meter_reading REAL,
            daily_usage REAL,
            region TEXT
        )
    """)

    conn.commit()
    conn.close()

init_db()

# ---------------- UI ----------------
st.title("💧 Watrack - Water Tracking System")

st.sidebar.title("💧 Menu")
menu = st.sidebar.radio(
    "Navigate",
    ["Dashboard", "Add Reading", "Train Model", "Prediction"]
)

# ---------------- INPUT ----------------
user_id = st.number_input("User ID", min_value=1)
region = st.selectbox("Region", ["North","South","East","West"])

# ---------------- LOAD DATA ----------------
conn = get_db()
df = pd.read_sql(
    "SELECT * FROM water_usage WHERE user_id=%s ORDER BY date",
    conn,
    params=(user_id,)
)
conn.close()

# ---------------- DASHBOARD ----------------
if menu == "Dashboard":
    st.subheader("📊 Dashboard")

    if len(df) > 0:
        col1, col2 = st.columns(2)
        col1.metric("💧 Last Usage", f"{df.iloc[-1]['daily_usage']:.0f} L")
        col2.metric("📊 Avg Usage", f"{df['daily_usage'].mean():.0f} L")

        chart_df = df.copy()
        chart_df['date'] = pd.to_datetime(chart_df['date'])

        fig = px.line(chart_df, x='date', y='daily_usage',
                      title="Water Usage Trend", markers=True)

        st.plotly_chart(fig)

        if df.iloc[-1]['daily_usage'] > df['daily_usage'].mean():
            st.error("⚠️ High consumption today")
        else:
            st.success("✅ Normal usage")
    else:
        st.warning("No data available. Add readings first.")

# ---------------- ADD READING ----------------
if menu == "Add Reading":
    st.subheader("➕ Add Reading")

    reading = st.number_input("Meter Reading", min_value=0.0)
    selected_date = st.date_input("Select Date")
    today = selected_date.strftime('%Y-%m-%d')

    if st.button("Add Reading"):
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT meter_reading FROM water_usage
            WHERE user_id=%s ORDER BY date DESC LIMIT 1
        """, (user_id,))
        prev = cursor.fetchone()

        if prev and reading < prev[0]:
            st.error("❌ Reading cannot be less than previous!")
            st.stop()

        daily_usage = reading - prev[0] if prev else 0

        cursor.execute("""
            INSERT INTO water_usage VALUES (%s,%s,%s,%s,%s)
        """, (user_id, today, reading, daily_usage, region))

        conn.commit()
        conn.close()

        st.success(f"Usage added: {daily_usage:.2f} L")

# ---------------- TRAIN MODEL ----------------
def train_model():
    if len(df) < 5:
        st.warning("Add more data to train model")
        return

    temp = df.copy()
    temp['date'] = pd.to_datetime(temp['date'])
    temp['day'] = temp['date'].dt.dayofweek

    temp['region'] = temp['region'].map({
        'North':0,'South':1,'East':2,'West':3
    })

    temp['lag1'] = temp['daily_usage'].shift(1)
    temp['lag2'] = temp['daily_usage'].shift(2)
    temp = temp.dropna()

    X = temp[['day','region','lag1','lag2']]
    y = temp['daily_usage']

    model = XGBRegressor()
    model.fit(X, y)

    with open(MODEL_FILE, "wb") as f:
        pickle.dump(model, f)

    st.success("Model trained successfully!")

if menu == "Train Model":
    st.subheader("🤖 Train Model")

    if st.button("Train Model"):
        with st.spinner("Training..."):
            train_model()

# ---------------- PREDICT ----------------
if menu == "Prediction":
    st.subheader("🔮 Prediction")

    if st.button("Predict Tomorrow"):

        model = load_model()

        # AUTO TRAIN FIX
        if model is None:
            st.warning("Model not found. Training automatically...")
            train_model()
            model = load_model()

        if model is None:
            st.error("Still no model available. Add more data and train.")
            st.stop()

        if len(df) < 2:
            st.warning("Not enough data")
            st.stop()

        last = df.iloc[-1]
        lag1 = last['daily_usage']
        lag2 = df.iloc[-2]['daily_usage']

        region_map = {'North':0,'South':1,'East':2,'West':3}

        X = np.array([[datetime.now().weekday(),
                       region_map[last['region']],
                       lag1, lag2]])

        pred = model.predict(X)[0]

        st.success(f"💧 Tomorrow Usage: {pred:.2f} L")

        if pred > 600:
            st.warning("⚠️ High usage expected!")
        else:
            st.success("Normal usage expected")

# ---------------- FOOTER ----------------
st.markdown("---")
st.markdown("👨‍💻 Developed by Damandeep Kaur | 💧 Water Intelligence System")
