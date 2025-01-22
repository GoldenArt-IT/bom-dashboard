import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import matplotlib.pyplot as plt
import time

def main():
    if not st.session_state.get("logged_in", False):
        st.error("Please log in from the WOOD MATERIAL page.")
        return

    # Google Sheets connection and data display
    # Set page to always wide
    st.set_page_config(layout="wide")

    st.title("Data BOM for Fabric Material")

    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(worksheet="ORDER BY FABRIC", ttl=5)
    df = df.dropna(how="all")

    df_price_list = conn.read(worksheet="PRICE LIST", ttl=5)
    df_price_list= df_price_list.dropna(how="all")

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

    # unique_category = df['CATEGORY'].dropna().unique()
    unique_trip = df['TRIP'].dropna().unique()
    unique_pi = df['PI NUMBER'].dropna().unique()
    
    unique_plan_date = sorted(df['PLAN DATE'].dropna().unique())

    # Sidebar for month filter
    # st.sidebar.title("Filters")

    selected_plan_date = st.sidebar.multiselect("Select Plan(s) Date", unique_plan_date)

    pi_option = st.sidebar.radio("Choose Filter by Specific PI(s):", ('Select all PI(s)', 'Filter by PI(s)'), index=0)
    if pi_option == 'Filter by PI(s)':
        selected_pi = st.sidebar.multiselect("Select PI(s) by Orders", unique_pi)
    else:
        selected_pi = unique_pi
    
    date_option = st.sidebar.radio("Choose Filter by Date:", ('Order', 'Delivery'), index=0)
    if date_option == 'Order':
        selected_months = st.sidebar.multiselect("Select Month(s) by Orders", unique_months, default=unique_months)
        selected_delivery_months = unique_delivery_month
    else:
        selected_delivery_months = st.sidebar.multiselect("Select Month(s) by Delivery", unique_delivery_month, default=unique_delivery_month)
        selected_months = unique_months
    
    # selected_category = st.sidebar.multiselect("Select Category(s)", unique_category, default=unique_category)
    selected_trip = st.sidebar.multiselect("Select Trip(s)", unique_trip, default=unique_trip)
    

    # Filter DataFrame by selected months
    filtered_df = df[
                        df['month_year'].isin(selected_months) & 
                        df['delivery_month_year'].isin(selected_delivery_months) & 
                        df['PI NUMBER'].isin(selected_pi) & 
                        df['TRIP'].isin(selected_trip) & 
                        (df['PLAN DATE'].isin(selected_plan_date) if selected_plan_date else True)
                        ]

    # Display filtered DataFrame
    st.dataframe(filtered_df)

    material_fabric_columns = [col for col in filtered_df.columns if 'MATERIAL FABRIC' in col]
    fabric_columns = [col for col in filtered_df.columns if col.startswith('FABRIC')]

    # Combine material fabric columns into a single series without duplicates
    unique_materials = pd.Series(df[material_fabric_columns].values.ravel()).dropna().str.strip().str.upper().unique()

    # Initialize a DataFrame to store the results
    result_data = [] 

    # Loop through each unique material and sum its corresponding fabric values
    for material in unique_materials:
        total_value = 0
        for material_col, fabric_col in zip(material_fabric_columns, fabric_columns):
            material_mask = filtered_df[material_col] == material
            fabric_values = pd.to_numeric(filtered_df.loc[material_mask, fabric_col], errors='coerce').dropna()
            total_value += (fabric_values * filtered_df.loc[material_mask, 'QTY']).sum()
        result_data.append({'Fabric Material': material, 'Total Usage': total_value})

    result_df = pd.DataFrame(result_data)

    
    df_price_list['Description'] = df_price_list['Description'].str.strip().str.upper()
    merge_result_price = pd.merge(result_df, df_price_list[['Description' ,'Unit Price']], left_on='Fabric Material', right_on='Description', how='left')
    merge_result_price['Total Price'] = merge_result_price['Total Usage'] * merge_result_price['Unit Price']
    merge_result_price.drop(columns=['Description'], inplace=True)
    merge_result_price = merge_result_price[merge_result_price['Total Usage'] > 0]
    merge_result_price = merge_result_price.drop_duplicates(subset=['Fabric Material'], keep='first')
    merge_result_price = merge_result_price.sort_values(by='Total Price', ascending=False)

    # Key Metrics
    total_pi, total_qty, total_material, total_price = st.columns(4)
    with total_pi:
        st.metric("Total PI", value=len(filtered_df))
    with total_qty:
        st.metric("Total QTY", value=filtered_df['QTY'].sum())
    with total_material:
        st.metric("Total Material", value=len(merge_result_price))
    with total_price:
        st.metric("Total Price", value="RM " + str(round(merge_result_price['Total Price'].sum(), 2)))

    st.subheader("Total Fabric Material Usage")
    st.dataframe(merge_result_price)

    # Create a bar chart using matplotlib
    st.subheader("Bar Chart of Total Usage by Fabric Material")
    st.bar_chart(result_df.set_index('Fabric Material'))

if __name__ == "__main__":
    main()