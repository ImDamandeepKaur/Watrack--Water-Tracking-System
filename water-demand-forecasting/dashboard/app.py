import streamlit as st
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime
import pickle
from xgboost import XGBRegressor
import os
import plotly.express as px
import plotly.graph_objects as go

# ---------------- PATH ----------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_DIR = os.path.join(BASE_DIR, "data")
MODEL_DIR = os.path.join(BASE_DIR, "models")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(MODEL_DIR, exist_ok=True)

DB = os.path.join(DATA_DIR, "water_data.db")
MODEL_FILE = os.path.join(MODEL_DIR, "xgb_model.pkl")

# ---------------- LOAD MODEL ----------------
@st.cache_resource
def load_model():
    if os.path.exists(MODEL_FILE):
        with open(MODEL_FILE, "rb") as f:
            return pickle.load(f)
    return None

# ---------------- DB ----------------
def get_db():
    return sqlite3.connect(DB, check_same_thread=False)

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
st.set_page_config(page_title="Watrack", layout="wide")

st.title("💧 Watrack - Water Tracking System")

st.markdown("""
<h3 style='color:#4CAF50;'>Smart Water Consumption Monitoring & Prediction</h3>
""", unsafe_allow_html=True)

# Sidebar
st.sidebar.title("💧 Menu")
menu = st.sidebar.radio(
    "Navigate",
    ["Dashboard", "Add Reading", "Train Model", "Prediction"]
)

# Inputs
user_id = st.number_input("User ID", min_value=1)
reading = st.number_input("Today's Meter Reading", min_value=0.0)
region = st.selectbox("Region", ["North","South","East","West"])

# ---------------- LOAD DATA ----------------
conn = get_db()
df = pd.read_sql(
    "SELECT * FROM water_usage WHERE user_id=? ORDER BY date",
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

        st.subheader("📈 Usage Trend")
        chart_df = df[df["daily_usage"] > 0].copy()
        chart_df['date'] = pd.to_datetime(chart_df['date'])

        fig = px.line(chart_df, x='date', y='daily_usage',
                      title="Water Usage Trend", markers=True)
        st.plotly_chart(fig, use_container_width=True)

        if df.iloc[-1]['daily_usage'] > df['daily_usage'].mean():
            st.error("⚠️ High consumption today")
        else:
            st.success("✅ Normal usage")
    else:
        st.info("No data available")

# ---------------- ADD READING ----------------
if menu == "Add Reading":
    st.subheader("➕ Add Reading")

    if st.button("Add Reading"):
        conn = get_db()
        cursor = conn.cursor()

        today = datetime.now().strftime('%Y-%m-%d')

        cursor.execute("""
            SELECT meter_reading FROM water_usage
            WHERE user_id=? ORDER BY date DESC LIMIT 1
        """, (user_id,))
        prev = cursor.fetchone()

        if prev and reading < prev[0]:
            st.error("❌ Reading cannot be less than previous!")
            st.stop()

        daily_usage = reading - prev[0] if prev else 0

        cursor.execute("""
            INSERT INTO water_usage VALUES (?,?,?,?,?)
        """, (user_id, today, reading, daily_usage, region))

        conn.commit()
        conn.close()

        st.success(f"Usage: {daily_usage:.2f} L")

        avg = df["daily_usage"].mean() if len(df) > 0 else 400
        if daily_usage > avg * 1.5:
            st.warning("⚠️ Unusually high usage detected!")

# ---------------- TRAIN MODEL ----------------
def train_model():
    if len(df) < 5:
        st.warning("Not enough data!")
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

    st.success("✅ Model trained successfully!")

if menu == "Train Model":
    st.subheader("🤖 Train Model")

    if st.button("Train Model"):
        with st.spinner("Training model..."):
            train_model()

# ---------------- PREDICT ----------------
if menu == "Prediction":
    st.subheader("🔮 Predict Tomorrow Usage")

    if st.button("Predict Tomorrow"):
        try:
            model = load_model()

            if model is None:
                st.error("⚠️ Train model first!")
                st.stop()

            if len(df) < 2:
                st.warning("Not enough data for prediction!")
                st.stop()

            with st.spinner("Predicting..."):

                last = df.iloc[-1]
                lag1 = last['daily_usage']
                lag2 = df.iloc[-2]['daily_usage']

                region_map = {'North':0,'South':1,'East':2,'West':3}

                X = np.array([[datetime.now().weekday(),
                               region_map[last['region']],
                               lag1, lag2]])

                pred = model.predict(X)[0]

            st.success(f"💧 Tomorrow Usage: {pred:.2f} L")

            # Gauge Chart
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=pred,
                title={'text': "Predicted Usage"},
                gauge={
                    'axis': {'range': [0, 1000]},
                    'steps': [
                        {'range': [0, 400], 'color': "green"},
                        {'range': [400, 700], 'color': "yellow"},
                        {'range': [700, 1000], 'color': "red"},
                    ]
                }
            ))

            st.plotly_chart(fig)

            diff = pred - df.iloc[-1]['daily_usage']

            if diff > 0:
                st.info(f"📈 Expected increase of {diff:.0f} L")
            else:
                st.info(f"📉 Expected decrease of {abs(diff):.0f} L")

        except Exception as e:
            st.error(f"Error: {e}")

# ---------------- FOOTER ----------------
st.markdown("---")
st.markdown("👨‍💻 Developed by Damandeep Kaur | 💧 Water Intelligence System")
