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

        # Set the page layout to wide for better visualization
        st.set_page_config(layout="wide")

        # Establish a connection to Google Sheets
        conn = st.connection("gsheets", type=GSheetsConnection)

        # Read and clean the "DATA BOM" worksheet
        df_data_bom = conn.read(worksheet="DATA BOM", ttl=300)
        df_data_bom = df_data_bom.dropna(how="all")  # Drop rows where all elements are missing
        df_data_bom = df_data_bom.loc[:, ~df_data_bom.columns.str.contains('^Unnamed')]  # Remove any 'Unnamed' columns

        # Read and clean the "PRICE LIST" worksheet
        df_price_list = conn.read(worksheet="PRICE LIST", ttl=300)
        df_price_list = df_price_list.dropna(how="all")  # Drop rows where all elements are missing
        df_price_list = df_price_list.loc[:, ~df_price_list.columns.str.contains('^Unnamed')]  # Remove any 'Unnamed' columns

        # Read and clean the "ORDER LIST" worksheet
        df_order_list = conn.read(worksheet="ORDER LIST", ttl=300)
        df_order_list = df_order_list.dropna(how="all")  # Drop rows where all elements are missing
        df_order_list = df_order_list.loc[:, ~df_order_list.columns.str.contains('^Unnamed')]  # Remove any 'Unnamed' columns

        # Merge "ORDER LIST" with "DATA BOM" on the 'MODEL' and 'CONFIRM MODEL NAME' columns
        merge_data = pd.merge(df_order_list, df_data_bom, left_on='MODEL', right_on='CONFIRM MODEL NAME', how='left')

        # Filter columns that contain raw materials and corresponding values
        raw_materials = [col for col in merge_data.columns if 'MATERIAL' in col]
        raw_materials_value_columns = [col for col in merge_data.columns if col.startswith(('WOOD', 'FABRIC', 'SPONGE', 'O.M'))]

        # Melt the data to reshape it, extracting the raw materials and usage data
        materials = merge_data.melt(
            id_vars=['TIMESTAMP', 'PI NUMBER', 'ORDER', 'TYPE', 'MODEL', 'QTY'], 
            value_vars=raw_materials, 
            var_name='Material Column', 
            value_name='MATERIAL'
        )

        usage = merge_data.melt(
            id_vars=['PI NUMBER'], 
            value_vars=raw_materials_value_columns, 
            var_name='Usage Column', 
            value_name='USAGE'
        )

        # Concatenate materials and usage data
        materials_usage = pd.concat(
            [materials[['TIMESTAMP', 'PI NUMBER', 'ORDER', 'TYPE', 'MODEL', 'QTY', 'MATERIAL']], usage['USAGE']], 
            axis=1
        )

        # Drop rows with missing materials and remove duplicate records for each PI NUMBER and MATERIAL
        materials_usage = materials_usage.dropna(subset=['MATERIAL'])
        materials_usage = materials_usage.drop_duplicates(subset=['PI NUMBER', 'MATERIAL'])

        # Display the material usage data in the Streamlit app
        # st.title('Material Usage')
        # st.text(f"Total rows: {len(materials_usage)}")
        # st.dataframe(materials_usage)

        # Merge material usage with the price list data on 'MATERIAL' and 'Description' columns
        merge_material_usage_price = pd.merge(
            materials_usage, df_price_list, left_on='MATERIAL', right_on='Description', how='left'
        )

        # Clean the merged data by removing unnecessary columns and dropping duplicates
        merge_material_usage_price_clean = merge_material_usage_price.drop(
            labels=['UOM Count', 'Description', 'Stock Control', 'Is Active', 'Order Price', 'Update'],
            axis=1,
            inplace=False
        )

        merge_material_usage_price_clean = merge_material_usage_price_clean.drop_duplicates(subset=['PI NUMBER', 'MATERIAL'])

        # Create a new column 'TOTAL PRICE' as QTY x USAGE x Unit Price
        merge_material_usage_price_clean['TOTAL PRICE'] = merge_material_usage_price_clean['QTY'] * merge_material_usage_price_clean['USAGE'] * merge_material_usage_price_clean['Unit Price']

        # Display the merged data (material usage with prices) in the Streamlit app
        st.title('Merge Usage with Price')
        # st.text(f"Total rows: {len(merge_material_usage_price_clean)}")
        st.dataframe(merge_material_usage_price_clean)

        # Identify and display materials in the usage data that do not have a matching entry in the price list
        # unmatched_materials = materials_usage[~materials_usage['MATERIAL'].isin(df_price_list['Description'])]
        # st.text(f"Unmatched materials: {len(unmatched_materials)}")
        # st.dataframe(unmatched_materials)


if __name__ == "__main__":
    main()