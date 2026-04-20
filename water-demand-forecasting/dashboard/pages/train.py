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

    if st.button("Train"):
        model.train(df)
        st.success("Model trained")
