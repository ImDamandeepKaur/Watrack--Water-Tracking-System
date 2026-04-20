import streamlit as st

st.set_page_config(layout="wide")

st.title("💧 Watrack System")

st.sidebar.title("📊 Menu")

page = st.sidebar.radio(
    "Navigate",
    ["Dashboard", "Add Reading", "Train Model", "Prediction"]
)

if page == "Dashboard":
    from pages.dashboard import show_dashboard
    show_dashboard()

elif page == "Add Reading":
    from pages.add_reading import show_add
    show_add()

elif page == "Train Model":
    from pages.train import show_train
    show_train()

elif page == "Prediction":
    from pages.predict import show_predict
    show_predict()
