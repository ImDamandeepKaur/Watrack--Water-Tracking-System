import streamlit as st
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime
import pickle
from xgboost import XGBRegressor
import os

# ---------------- PATH ----------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "..", "data")
MODEL_DIR = os.path.join(BASE_DIR, "..", "models")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(MODEL_DIR, exist_ok=True)

DB = os.path.join(DATA_DIR, "water_data.db")
MODEL_FILE = os.path.join(MODEL_DIR, "xgb_model.pkl")

# ---------------- DB ----------------
def get_db():
    return sqlite3.connect(DB)

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
st.title("💧 Watrack- Water Tracking System")

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

# ---------------- ADD DATA ----------------
if st.button("Add Reading"):
    conn = get_db()
    cursor = conn.cursor()

    today = datetime.now().strftime('%Y-%m-%d')

    cursor.execute("""
        SELECT meter_reading FROM water_usage
        WHERE user_id=? ORDER BY date DESC LIMIT 1
    """, (user_id,))
    prev = cursor.fetchone()

    # ✅ validation
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

    # ✅ anomaly detection (safe even if no df)
    avg = df["daily_usage"].mean() if len(df) > 0 else 400

    if daily_usage > avg * 1.5:
        st.warning("⚠️ Unusually high usage detected!")

# ---------------- METRICS ----------------
if len(df) > 0:
    col1, col2 = st.columns(2)
    col1.metric("Last Usage", f"{df.iloc[-1]['daily_usage']:.0f} L")
    col2.metric("Avg Usage", f"{df['daily_usage'].mean():.0f} L")

# ---------------- CHART ----------------
if len(df) > 0:
    st.subheader("📈 Usage Trend")

    chart_df = df[df["daily_usage"] > 0].copy()
    chart_df['date'] = pd.to_datetime(chart_df['date'])

    st.line_chart(chart_df.set_index('date')['daily_usage'])

# ---------------- STATUS ----------------
if len(df) > 0:
    if df.iloc[-1]['daily_usage'] > df['daily_usage'].mean():
        st.error("⚠️ High consumption today")
    else:
        st.success("✅ Normal usage")

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

    st.success("Model trained!")

if st.button("Train Model"):
    train_model()

# ---------------- PREDICT ----------------
if st.button("Predict Tomorrow"):
    try:
        with open(MODEL_FILE, "rb") as f:
            model = pickle.load(f)

        if len(df) < 2:
            st.warning("Not enough data for prediction!")
            st.stop()

        last = df.iloc[-1]
        lag1 = last['daily_usage']
        lag2 = df.iloc[-2]['daily_usage']

        region_map = {'North':0,'South':1,'East':2,'West':3}

        X = np.array([[datetime.now().weekday(),
                       region_map[last['region']],
                       lag1, lag2]])

        pred = model.predict(X)[0]

        st.success(f"Tomorrow Usage: {pred:.2f} L")

        # ✅ smart message
        diff = pred - df.iloc[-1]['daily_usage']

        if diff > 0:
            st.info(f"📈 Expected increase of {diff:.0f} L")
        else:
            st.info(f"📉 Expected decrease of {abs(diff):.0f} L")

        if pred > 600:
            st.warning("⚠️ High usage expected!")

    except:
        st.error("Train model first!")