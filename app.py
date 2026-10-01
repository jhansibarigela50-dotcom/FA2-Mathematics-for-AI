import streamlit as st
import pandas as pd
import plotly.express as px

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="LogiSight Analytics - Last Mile Delivery",
    page_icon="🚚",
    layout="wide"
)

# --- LOAD PRE-CLEANED DATASET ---
@st.cache_data
def load_data(file_path):
    df = pd.read_csv(file_path)
    
    # Check if late flag exists; if not, create it based on Mean + 1 Std Dev
    if 'Is_Late' not in df.columns:
        threshold = df['Delivery_Time'].mean() + df['Delivery_Time'].std()
        df['Is_Late'] = df['Delivery_Time'] > threshold
        
    # Check if age group binning exists; if not, create it
    if 'Agent_Age_Group' not in df.columns and 'Agent_Age' in df.columns:
        bins = [0, 24, 40, 100]
        labels = ['<25', '25–40', '40+']
        df['Agent_Age_Group'] = pd.cut(df['Agent_Age'], bins=bins, labels=labels)
        
    return df

# Replace with your cleaned dataset filename
DATA_FILE = "cleaned_delivery_data.csv"

try:
    df = load_data(DATA_FILE)
except Exception as e:
    st.error(f"Error loading dataset file '{DATA_FILE}': {e}")
    st.stop()

# --- SIDEBAR FILTERS ---
st.sidebar.header("🔍 Filter Delivery Data")

def get_filter_options(col_name):
    return df[col_name].dropna().unique() if col_name in df.columns else []

weather_filter = st.sidebar.multiselect("Select Weather:", options=get_filter_options('Weather'), default=get_filter_options('Weather'))
traffic_filter = st.sidebar.multiselect("Select Traffic:", options=get_filter_options('Traffic'), default=get_filter_options('Traffic'))
vehicle_filter = st.sidebar.multiselect("Select Vehicle:", options=get_filter_options('Vehicle'), default=get_filter_options('Vehicle'))
category_filter = st.sidebar.multiselect("Select Category:", options=get_filter_options('Category'), default=get_filter_options('Category'))
area_filter = st.sidebar.multiselect("Select Area:", options=get_filter_options('Area'), default=get_filter_options('Area'))

# Apply Filters
filtered_df = df[
    (df['Weather'].isin(weather_filter)) &
    (df['Traffic'].isin(traffic_filter)) &
    (df['Vehicle'].isin(vehicle_filter)) &
    (df['Category'].isin(category_filter)) &
    (df['Area'].isin(area_filter))
]

# --- MAIN DASHBOARD & KPI CARDS ---
st.title("🚚 Last Mile Delivery Performance Dashboard")
st.markdown("Interactive analysis of delivery drivers, delays, routes, and overall operational efficiency.")

if filtered_df.empty:
    st.warning("No data matches the selected filters. Please expand your sidebar selections.")
    st.stop()

# Metrics Display
avg_delivery = filtered_df['Delivery_Time'].mean()
late_pct = (filtered_df['Is_Late'].sum() / len(filtered_df)) * 100
total_deliveries = len(filtered_df)

col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
col_kpi1.metric("Average Delivery Time", f"{avg_delivery:.1f} mins")
col_kpi2.metric("Late Delivery Rate", f"{late_pct:.1f}%")
col_kpi3.metric("Total Deliveries Analyzed", f"{total_deliveries}")

st.markdown("---")

# --- VISUALIZATIONS ---

# Row 1: Delay Analyzer & Vehicle Comparison
col1, col2 = st.columns(2)

with col1:
    st.subheader("1. Delay Analyzer")
    delay_df = filtered_df.groupby(['Weather', 'Traffic'], as_index=False)['Delivery_Time'].mean()
    fig1 = px.bar(
        delay_df, x='Weather', y='Delivery_Time', color='Traffic', barmode='group',
        labels={'Delivery_Time': 'Avg Delivery Time (mins)'},
        title="Avg Delivery Time by Weather & Traffic"
    )
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    st.subheader("2. Vehicle Performance")
    vehicle_df = filtered_df.groupby('Vehicle', as_index=False)['Delivery_Time'].mean()
    fig2 = px.bar(
        vehicle_df, x='Vehicle', y='Delivery_Time', color='Vehicle',
        labels={'Delivery_Time': 'Avg Delivery Time (mins)'},
        title="Avg Delivery Time by Vehicle Type"
    )
    st.plotly_chart(fig2, use_container_width=True)

# Row 2: Agent Performance Scatter Plot & Area Heatmap
col3, col4 = st.columns(2)

with col3:
    st.subheader("3. Agent Performance Scatter")
    fig3 = px.scatter(
        filtered_df, x='Agent_Rating', y='Delivery_Time', color='Agent_Age_Group',
        hover_data=['Agent_Age'] if 'Agent_Age' in filtered_df.columns else None,
        labels={'Agent_Rating': 'Agent Rating', 'Delivery_Time': 'Delivery Time (mins)', 'Agent_Age_Group': 'Age Group'},
        title="Agent Rating vs. Delivery Time"
    )
    st.plotly_chart(fig3, use_container_width=True)

with col4:
    st.subheader("4. Area Heatmap")
    area_df = filtered_df.groupby('Area', as_index=False)['Delivery_Time'].mean()
    fig4 = px.density_heatmap(
        area_df, x='Area', y='Delivery_Time', z='Delivery_Time',
        color_continuous_scale='Viridis',
        labels={'Delivery_Time': 'Avg Delivery Time (mins)'},
        title="Average Delivery Time Across Areas"
    )
    st.plotly_chart(fig4, use_container_width=True)

# Row 3: Product Category Visualizer
st.subheader("5. Product Category Distribution")
fig5 = px.box(
    filtered_df, x='Category', y='Delivery_Time', color='Category',
    labels={'Delivery_Time': 'Delivery Time (mins)'},
    title="Delivery Time Distribution by Product Category"
)
st.plotly_chart(fig5, use_container_width=True)
