import streamlit as st
import pandas as pd
from db import Database
from model import Model

def show_train():

    db = Database()
    model = Model()

    st.subheader("🤖 Train Model")

    user_id = st.number_input("User ID", min_value=1)

    data = db.fetch_data(user_id)

    if len(data) < 5:
        st.warning("Not enough data")
        return

    df = pd.DataFrame(data, columns=[
        "user_id","date","meter_reading","daily_usage","region"
    ])

    # convert date
    df['date'] = pd.to_datetime(df['date'])

    # sort data
    df = df.sort_values(by='date')

    # validate usage
    if df['daily_usage'].sum() == 0:
        st.error("Invalid data. Add proper readings first.")
        return

    if st.button("Train"):

        # simulate lag effect
        temp = df.copy()
        temp['lag1'] = temp['daily_usage'].shift(1)
        temp['lag2'] = temp['daily_usage'].shift(2)
        temp = temp.dropna()

        if len(temp) == 0:
            st.error("Not enough usable data after processing")
            return

        try:
            model.train(df)
            st.success("Model trained successfully ✅")
        except Exception as e:
            st.error(f"Training failed: {str(e)}")
