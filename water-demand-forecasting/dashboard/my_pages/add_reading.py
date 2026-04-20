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
            # Fetch previous data
            data = db.fetch_data(user_id)

            prev = None
            if len(data) > 0:
                prev = data[-1][2]   # meter_reading column

            #validation
            if prev is not None and reading < prev:
                st.error("❌ Reading cannot be less than previous")
                st.stop()

            # calculate usage
            usage = reading - prev if prev else 0

            #insert correct data
            db.insert_data(user_id, date, reading, usage, region)

            st.success(f"Usage added: {usage:.2f} L")

            #refresh dashboard
            st.rerun()

        except Exception as e:
            st.error(str(e))
