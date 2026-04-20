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

    # convert date
    df['date'] = pd.to_datetime(df['date'])

    #sort data
    df = df.sort_values(by='date')

    if st.button("Predict"):

        try:
            #validate data
            if df['daily_usage'].sum() == 0:
                st.error("No valid usage data. Add readings first.")
                st.stop()

            #load model
            model = model_obj.load()

            #train if not exists
            if model is None:
                model_obj.train(df)
                model = model_obj.load()

            #predict
            pred = model_obj.predict(model, df)

            st.success(f"💧 Predicted Usage: {pred:.2f} L")

        except Exception as e:
            st.error(f"Prediction failed: {str(e)}")
