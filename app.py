import streamlit as st
import plotly.express as px
import pandas as pd
from main import Argus

# Initialize Argus :: Load Data
argus = Argus()
argus.init_local_data()
argus.update_local_data()
output_data = argus.transform_data()

all_data = output_data["all_data"]
ticker_year = output_data["ticker_year"]
ticker_total = output_data["ticker_total"]
portfolio_value = all_data.groupby("Date")["Position Value"].sum().reset_index()

# Built Website
st.title("Portfolio Performance Dashboard")

# KPI
total_value = ticker_year["Position Value"].sum()
total_pl = ticker_year["Aggregated P/L"].sum()
total_div = ticker_year["Dividend Payout"].sum()

col1, col2, col3 = st.columns(3)
col1.metric("Total Value (EUR)" , f"€{total_value:,.2f}")
col2.metric("Total P/L", f"€{total_pl:,.2f}", delta=f"{total_pl:,.2f}")
col3.metric("Total Dividends", f"€{total_div:,.2f}")

st.divider()

# Chart over Time
st.subheader("Performance Over Time")
fig_line = px.line(portfolio_value, x="Date", y="Position Value", title="Position Value")
st.plotly_chart(fig_line, use_container_width=True)


# Pie / Bar Chart
col4, col5 = st.columns(2)
with col4:
    st.subheader("Asset Allocation")
    fig_pie = px.pie(ticker_total.reset_index(), values='Position Value', names='Ticker', hole=0.4)
    st.plotly_chart(fig_pie, use_container_width=True)

with col5:
    st.subheader("Yearly P/L Breakdown")
    fig_bar = px.bar(ticker_year.reset_index(), x='Year', y='Aggregated P/L', color='Ticker', barmode='group')
    st.plotly_chart(fig_bar, use_container_width=True)



