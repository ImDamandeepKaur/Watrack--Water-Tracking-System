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
            #sort by date
            data = sorted(data, key=lambda x: x[1])
            
            #region consistency
            if len(data) > 0:
                existing_region = data[0][4]
                if existing_region != region:
                    st.error(f"❌ User already assigned to {existing_region}")
                    st.stop()
                    
            #prevent duplicate date
            for row in data:
                if row[1] == date:
                    st.error("❌ Entry for this date already exists")
                    st.stop()
                    
            #prevent past entry
            if len(data) > 0:
                last_date = data[-1][1]
                if date < last_date:
                    st.error("❌ Cannot add past date entry")
                    st.stop() 
                    
            prev = None
            if len(data) > 0:
                prev = data[-1][2]
                st.info(f"Last Reading: {prev} L")

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
