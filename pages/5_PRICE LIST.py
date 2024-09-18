import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import matplotlib.pyplot as plt
import time

# Load user credentials from secrets
def load_credentials():
    return st.secrets["users"]

# Check if the provided credentials are correct
def authenticate(username, password, credentials):
    return credentials.get(username) == password

# Main function to run the Streamlit app
def main():
    # Initialize session state for login status
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.show_success = False

    # Load credentials
    credentials = load_credentials()

    if not st.session_state.logged_in:
        st.title("Login")
        # Create login form
        username = st.text_input("Email")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            if authenticate(username, password, credentials):
                st.session_state.logged_in = True
                st.session_state.show_success = True
                st.rerun()
            else:
                st.error("Invalid username or password")

    if st.session_state.logged_in:
        if st.session_state.show_success:
            st.success("Login successful!")
            time.sleep(3)
            st.session_state.show_success = False
            st.rerun()

        # Google Sheets connection and data display

        # Set page to always wide
        st.set_page_config(layout="wide")

        st.title("Price List")

        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(worksheet="PRICE LIST", ttl=5)
        # df = df.dropna(how="all")

        st.dataframe(df)

if __name__ == "__main__":
    main()

