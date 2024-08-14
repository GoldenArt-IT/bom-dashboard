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
                st.experimental_rerun()
            else:
                st.error("Invalid username or password")

    if st.session_state.logged_in:
        if st.session_state.show_success:
            st.success("Login successful!")
            time.sleep(3)
            st.session_state.show_success = False
            st.experimental_rerun()

        # Google Sheets connection and data display

        # Set page to always wide
        st.set_page_config(layout="wide")

        st.title("Data BOM for Wood Material")

        conn = st.experimental_connection("gsheets", type=GSheetsConnection)
        df = conn.read(worksheet="ORDER BY WOOD", ttl=5)
        df = df.dropna(how="all")

        # st.dataframe(df)

        # Convert date column to datetime
        date_column = 'TIMESTAMP'
        df[date_column] = pd.to_datetime(df[date_column], errors='coerce')

        delivery_date_column = 'DELIVERY PLAN DATE'
        df[delivery_date_column] = pd.to_datetime(df[delivery_date_column], errors='coerce')

        # Extract unique values
        df['month_year'] = df[date_column].dt.strftime('%b %Y')
        unique_months = df['month_year'].dropna().unique()
        unique_months = sorted(unique_months, key=lambda x: pd.to_datetime(x, format='%b %Y'), reverse=True)

        df['delivery_month_year'] = df[delivery_date_column].dt.strftime('%b %Y')
        unique_delivery_month = df['delivery_month_year'].dropna().unique()
        unique_delivery_month = sorted(unique_delivery_month, key=lambda x: pd.to_datetime(x, format='%b %Y'), reverse=True)

        unique_category = df['CATEGORY'].dropna().unique()
        unique_trip = df['TRIP'].dropna().unique()

        # Sidebar for month filter
        # st.sidebar.title("Filters")

        selected_months = st.sidebar.multiselect("Select Month(s) by Orders", unique_months, default=unique_months)
        selected_category = st.sidebar.multiselect("Select Category(s)", unique_category, default=unique_category)
        selected_trip = st.sidebar.multiselect("Select Trip(s)", unique_trip, default=unique_trip)
        # selected_delivery_months = st.sidebar.multiselect("Select Month(s) by Delivery", unique_delivery_month, default=unique_delivery_month)

        # Filter DataFrame by selected months
        filtered_df = df[df['month_year'].isin(selected_months) 
                        & df['CATEGORY'].isin(selected_category) 
                        & df['TRIP'].isin(selected_trip)
                        ]

        # Display filtered DataFrame
        st.dataframe(filtered_df)

        material_wood_columns = [col for col in filtered_df.columns if 'MATERIAL WOOD' in col]
        wood_columns = [col for col in filtered_df.columns if col.startswith('WOOD')]

        # Combine material wood columns into a single series without duplicates
        unique_materials = pd.Series(df[material_wood_columns].values.ravel()).dropna().unique()

        # Initialize a DataFrame to store the results
        result_data = [] 

        # Loop through each unique material and sum its corresponding wood values
        for material in unique_materials:
            total_value = 0
            for material_col, wood_col in zip(material_wood_columns, wood_columns):
                material_mask = filtered_df[material_col] == material
                wood_values = pd.to_numeric(filtered_df.loc[material_mask, wood_col], errors='coerce').dropna()
                total_value += (wood_values * filtered_df.loc[material_mask, 'QTY']).sum()
            result_data.append({'Wood Material': material, 'Total Usage': total_value})

        result_df = pd.DataFrame(result_data)
        result_df = result_df.sort_values(by='Total Usage', ascending=False)

        st.subheader("Total Wood Material Usage")
        result_df

        # Create a bar chart using matplotlib
        st.subheader("Bar Chart of Total Usage by Wood Material")
        st.bar_chart(result_df.set_index('Wood Material'))

if __name__ == "__main__":
    main()

