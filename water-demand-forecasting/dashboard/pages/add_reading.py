import streamlit as st
from db import Database

def show_add():

    db = Database()

    st.subheader("➕ Add Reading")

    user_id = st.number_input("User ID", min_value=1)
    region = st.selectbox("Region", ["North","South","East","West"])
    reading = st.number_input("Meter Reading", min_value=0.0)

    date = st.date_input("Date").strftime('%Y-%m-%d')

    if st.button("Add"):

        try:
            db.insert_data(user_id, date, reading, 0, region)
            st.success("Added successfully")
        except Exception as e:
            st.error(str(e))
