import streamlit as st
import pandas as pd
from db import Database
from model import Model

def show_predict():

    db = Database()
    model_obj = Model()

    st.subheader("🔮 Prediction")

    user_id = st.number_input("User ID", min_value=1)

    data = db.fetch_data(user_id)

    if len(data) < 2:
        st.warning("Not enough data")
        return

    df = pd.DataFrame(data, columns=[
        "user_id","date","meter_reading","daily_usage","region"
    ])

    if st.button("Predict"):
        if df['daily_usage'].sum() == 0:
            st.error("No valid usage data. Add readings first.")
            st.stop()
            
        model = model_obj.load()

        if model is None:
            model_obj.train(df)
            model = model_obj.load()

        pred = model_obj.predict(model, df)

        st.success(f"Prediction: {pred:.2f}")
