import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from babel.numbers import format_currency

# Setup Streamlit page
st.set_page_config(layout="wide")

# Load data
@st.cache_data
def load_data():
    df = pd.read_csv("dashboard/all_data.csv")
    df['order_purchase_timestamp'] = pd.to_datetime(df['order_purchase_timestamp'], errors='coerce')
    df['year'] = df['order_purchase_timestamp'].dt.year
    df['month'] = df['order_purchase_timestamp'].dt.month
    return df

all_df = load_data()

# Sidebar Filters
st.sidebar.header('Filter Waktu')

year_filter = st.sidebar.multiselect(
    'Pilih Tahun', 
    options=all_df['year'].dropna().unique(), 
    default=all_df['year'].dropna().unique()
)

month_filter = st.sidebar.multiselect(
    'Pilih Bulan', 
    options=range(1, 13), 
    format_func=lambda x: pd.to_datetime(f'2024-{x}-01').strftime('%B'), 
    default=range(1, 13)
)

# Filter data based on user input
filtered_all_df = all_df[
    (all_df['year'].isin(year_filter)) & 
    (all_df['month'].isin(month_filter))
]

# Dashboard Title
st.title('Dashboard Analisis Pelanggan')
st.markdown('Dashboard ini memberikan wawasan tentang pelanggan dan aktivitas penjualan berdasarkan data yang tersedia.')

# Daily Orders
st.subheader('Daily Orders')

# Calculate daily orders
daily_orders_df = filtered_all_df.groupby(
    filtered_all_df['order_purchase_timestamp'].dt.date
).agg({
    'order_id': 'count',
    'payment_value': 'sum'
}).reset_index()

daily_orders_df.columns = ['order_date', 'order_count', 'revenue']

col1, col2 = st.columns(2)

with col1:
    total_orders = daily_orders_df.order_count.sum()
    st.metric("Total orders", value=total_orders)

with col2:
    total_revenue = format_currency(daily_orders_df.revenue.sum(), "BRL", locale='pt_BR')
    st.metric("Total Revenue", value=total_revenue)

fig, ax = plt.subplots(figsize=(16, 8))
ax.plot(
    daily_orders_df["order_date"],
    daily_orders_df["order_count"],
    marker='o', 
    linewidth=2,
    color="#90CAF9"
)
ax.tick_params(axis='y', labelsize=20)
ax.tick_params(axis='x', labelsize=15)
plt.title("Daily Orders", fontsize=20)
plt.xlabel("Date", fontsize=15)
plt.ylabel("Number of Orders", fontsize=15)
st.pyplot(fig)


col1, col2 = st.columns(2)

with col1:
    st.header('Distribusi Pelanggan Berdasarkan Negara Bagian')
    state_counts = filtered_all_df['customer_state'].value_counts().head(10)
    fig1, ax1 = plt.subplots(figsize=(10, 6))
    sns.barplot(x=state_counts.index, y=state_counts.values, palette='viridis', ax=ax1)
    ax1.set_title('Distribusi Pelanggan Berdasarkan Negara Bagian', fontsize=16)
    ax1.set_xlabel('Negara Bagian', fontsize=12)
    ax1.set_ylabel('Jumlah Pelanggan', fontsize=12)
    plt.xticks(rotation=45)
    st.pyplot(fig1)

with col2:
    st.header('10 Kota dengan Pelanggan Terbanyak')
    city_counts = filtered_all_df['customer_city'].value_counts().head(10)
    fig2, ax2 = plt.subplots(figsize=(10, 6))
    sns.barplot(x=city_counts.index, y=city_counts.values, palette='Blues_d', ax=ax2)
    ax2.set_title('10 Kota dengan Pelanggan Terbanyak', fontsize=16)
    ax2.set_xlabel('Kota', fontsize=12)
    ax2.set_ylabel('Jumlah Pelanggan', fontsize=12)
    plt.xticks(rotation=45)
    st.pyplot(fig2)


st.header('Jumlah Order per Bulan')
filtered_all_df['purchase_month'] = filtered_all_df['order_purchase_timestamp'].dt.to_period('M')
monthly_orders = filtered_all_df.groupby('purchase_month').size().reset_index(name='count')
monthly_orders['purchase_month'] = monthly_orders['purchase_month'].astype(str)

fig3, ax3 = plt.subplots(figsize=(12, 6))
sns.lineplot(x='purchase_month', y='count', data=monthly_orders, marker='o', ax=ax3)
ax3.set_title('Jumlah Order per Bulan', fontsize=16)
ax3.set_xlabel('Bulan', fontsize=12)
ax3.set_ylabel('Jumlah Order', fontsize=12)
plt.xticks(rotation=45)
st.pyplot(fig3)

st.header('RFM Analysis')

latest_date = filtered_all_df['order_purchase_timestamp'].max()

rfm_df = filtered_all_df.groupby('customer_unique_id').agg({
    'order_purchase_timestamp': lambda x: (latest_date - x.max()).days,
    'order_id': 'count',
    'payment_value': 'sum'
}).reset_index()

rfm_df.columns = ['customer_unique_id', 'recency', 'frequency', 'monetary']

col1, col2, col3 = st.columns(3)

with col1:
    avg_recency = round(rfm_df['recency'].mean(), 1)
    st.metric("Average Recency (days)", value=avg_recency)

with col2:
    avg_frequency = round(rfm_df['frequency'].mean(), 2)
    st.metric("Average Frequency", value=avg_frequency)

with col3:
    avg_monetary = format_currency(rfm_df['monetary'].mean(), "BRL", locale='pt_BR')
    st.metric("Average Monetary", value=avg_monetary)

st.subheader("Top 5 Customers by RFM Metrics")

fig, ax = plt.subplots(nrows=1, ncols=3, figsize=(20, 6))
colors = ["#90CAF9"] * 5

sns.barplot(y="recency", x="customer_unique_id", data=rfm_df.sort_values(by="recency").head(5), palette=colors, ax=ax[0])
ax[0].set_ylabel("Days")
ax[0].set_xlabel("Customer ID")
ax[0].set_title("Top 5 by Recency (Lower is Better)")
plt.setp(ax[0].xaxis.get_majorticklabels(), rotation=45, ha='right')

sns.barplot(y="frequency", x="customer_unique_id", data=rfm_df.sort_values(by="frequency", ascending=False).head(5), palette=colors, ax=ax[1])
ax[1].set_ylabel("Number of Orders")
ax[1].set_xlabel("Customer ID")
ax[1].set_title("Top 5 by Frequency")
plt.setp(ax[1].xaxis.get_majorticklabels(), rotation=45, ha='right')

sns.barplot(y="monetary", x="customer_unique_id", data=rfm_df.sort_values(by="monetary", ascending=False).head(5), palette=colors, ax=ax[2])
ax[2].set_ylabel("Total Spend")
ax[2].set_xlabel("Customer ID")
ax[2].set_title("Top 5 by Monetary Value")
plt.setp(ax[2].xaxis.get_majorticklabels(), rotation=45, ha='right')

plt.tight_layout()
st.pyplot(fig)

st.markdown("---")
st.markdown("Data diambil dari sumber yang dapat diandalkan. Analisis ini bertujuan untuk memberikan wawasan tentang perilaku pelanggan.")