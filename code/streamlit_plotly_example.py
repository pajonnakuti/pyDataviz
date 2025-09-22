import streamlit as st
import pandas as pd
import numpy as np

# Page config
st.set_page_config(page_title='Basic Sales Dashboard', layout='wide')

# Generate sample data
np.random.seed(42)
df = pd.DataFrame({
    'Date': pd.date_range('2024-01-01', periods=100),
    'Sales': np.random.randint(500, 2000, size=100),
    'Region': np.random.choice(['North', 'South', 'East', 'West'], size=100),
    'Product': np.random.choice(['Product A', 'Product B', 'Product C'], size=100)
})

# Sidebar filters
st.sidebar.title('Filters')
regions = st.sidebar.multiselect('Select Region', df['Region'].unique(), default=df['Region'].unique())
products = st.sidebar.multiselect('Select Product', df['Product'].unique(), default=df['Product'].unique())

# Filter data
filtered_df = df[(df['Region'].isin(regions)) & (df['Product'].isin(products))]

# Display metrics
col1, col2, col3 = st.columns(3)
col1.metric("Total Sales", f"${filtered_df['Sales'].sum():,}")
col2.metric("Average Sales", f"${filtered_df['Sales'].mean():.0f}")
col3.metric("Records", len(filtered_df))

# Display filtered data
st.subheader("Filtered Data")
st.dataframe(filtered_df)