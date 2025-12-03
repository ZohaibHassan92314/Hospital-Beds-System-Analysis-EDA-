import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime

# ================= PAGE CONFIG =================
st.set_page_config(
    page_title="Hospital Bed Intelligence System",
    page_icon="🏥",
    layout="wide"
)

# ================= HEADER =================
st.markdown(
    """
    <h1 style='text-align:center;'>🏥 Hospital Bed Intelligence Dashboard</h1>
    <p style='text-align:center;color:gray;font-size:18px'>
    Real-Time Decision Support for ICU, Emergency & Ward Management
    </p>
    """,
    unsafe_allow_html=True
)

# ================= DATA GENERATION (Notebook Logic) =================
@st.cache_data
def generate_data():
    np.random.seed(42)

    hospitals = ["City Hospital", "Central Hospital", "National Medical Center"]
    wards = ["ICU", "Emergency", "General", "Maternity"]
    dates = pd.date_range(end=datetime.today(), periods=30)

    data = []
    bed_no = 1

    for date in dates:
        for hosp in hospitals:
            for ward in wards:
                capacity = {"ICU": 20, "Emergency": 30, "General": 50, "Maternity": 25}[ward]
                occupied = np.random.randint(int(capacity*0.5), capacity)

                for i in range(capacity):
                    data.append({
                        "date": date,
                        "hospital": hosp,
                        "ward": ward,
                        "bed_id": f"B-{bed_no}",
                        "occupied": 1 if i < occupied else 0
                    })
                    bed_no += 1

    return pd.DataFrame(data)

df = generate_data()

# ================= SIDEBAR (UPGRADED) =================
st.sidebar.markdown("## 🔧 Control Panel")

hospital = st.sidebar.selectbox(
    "🏥 Hospital",
    ["All"] + sorted(df["hospital"].unique())
)

ward = st.sidebar.multiselect(
    "🛏️ Select Ward(s)",
    df["ward"].unique(),
    default=df["ward"].unique()
)

bed_status = st.sidebar.radio(
    "📌 Bed Status",
    ["All", "Available", "Occupied"]
)

critical_view = st.sidebar.checkbox("🚨 ICU & Emergency Only")

date_range = st.sidebar.slider(
    "📅 Date Range",
    min_value=df["date"].min().date(),
    max_value=df["date"].max().date(),
    value=(df["date"].min().date(), df["date"].max().date())
)

# ================= FILTERING =================
data = df.copy()

if hospital != "All":
    data = data[data["hospital"] == hospital]

data = data[data["ward"].isin(ward)]

if critical_view:
    data = data[data["ward"].isin(["ICU", "Emergency"])]

if bed_status == "Available":
    data = data[data["occupied"] == 0]
elif bed_status == "Occupied":
    data = data[data["occupied"] == 1]

data = data[
    (data["date"].dt.date >= date_range[0]) &
    (data["date"].dt.date <= date_range[1])
]

# ================= KPI SECTION =================
total_beds = data["bed_id"].nunique()
occupied = data["occupied"].sum()
available = total_beds - occupied
occ_rate = (occupied / total_beds * 100) if total_beds else 0

k1, k2, k3, k4 = st.columns(4)
k1.metric("🛏️ Total Beds", total_beds)
k2.metric("❌ Occupied", occupied)
k3.metric("✅ Available", available)
k4.metric("📊 Occupancy %", f"{occ_rate:.1f}")

st.markdown("---")

# ================= GRAPH 1: OCCUPANCY TREND =================
trend = data.groupby("date").agg(
    total=("bed_id", "nunique"),
    occupied=("occupied", "sum")
).reset_index()
trend["occupancy_pct"] = trend["occupied"] / trend["total"] * 100

st.subheader("📈 Bed Occupancy Trend")
st.plotly_chart(
    px.line(trend, x="date", y="occupancy_pct", markers=True),
    use_container_width=True
)

# ================= GRAPH 2: WARD UTILIZATION =================
ward_util = data.groupby("ward").agg(
    occupied=("occupied", "sum"),
    total=("bed_id", "nunique")
).reset_index()
ward_util["usage_pct"] = ward_util["occupied"] / ward_util["total"] * 100

st.subheader("🏨 Ward Utilization Rate")
st.plotly_chart(
    px.bar(ward_util, x="ward", y="usage_pct", color="ward"),
    use_container_width=True
)

# ================= GRAPH 3: HOSPITAL COMPARISON =================
hospital_util = data.groupby("hospital").agg(
    occupied=("occupied", "sum"),
    total=("bed_id", "nunique")
).reset_index()
hospital_util["occ_pct"] = hospital_util["occupied"] / hospital_util["total"] * 100

st.subheader("🏥 Hospital-wise Occupancy Comparison")
st.plotly_chart(
    px.bar(hospital_util, x="hospital", y="occ_pct", color="hospital"),
    use_container_width=True
)

# ================= GRAPH 4: CRITICAL VS NON-CRITICAL =================
data["category"] = data["ward"].apply(
    lambda x: "Critical" if x in ["ICU", "Emergency"] else "Non-Critical"
)

critical_cmp = data.groupby("category").agg(
    occupied=("occupied", "sum"),
    total=("bed_id", "nunique")
).reset_index()
critical_cmp["pct"] = critical_cmp["occupied"] / critical_cmp["total"] * 100

st.subheader("🚨 Critical vs Non-Critical Beds")
st.plotly_chart(
    px.pie(critical_cmp, names="category", values="pct", hole=0.4),
    use_container_width=True
)

# ================= GRAPH 5: DAILY ADMISSIONS PRESSURE =================
daily_load = data.groupby("date")["occupied"].sum().reset_index()

st.subheader("📆 Daily Admission Pressure")
st.plotly_chart(
    px.area(daily_load, x="date", y="occupied"),
    use_container_width=True
)

# ================= GRAPH 6: BED AVAILABILITY DISTRIBUTION =================
availability_dist = data["occupied"].map({0: "Available", 1: "Occupied"}).value_counts().reset_index()
availability_dist.columns = ["status", "count"]

st.subheader("🛏️ Bed Availability Distribution")
st.plotly_chart(
    px.bar(availability_dist, x="status", y="count", color="status"),
    use_container_width=True
)

# ================= GRAPH 7: WARD + HOSPITAL HEATMAP =================
heatmap = data.groupby(["hospital", "ward"]).agg(
    occ=("occupied", "mean")
).reset_index()

st.subheader("🔥 Occupancy Heatmap")
st.plotly_chart(
    px.density_heatmap(
        heatmap,
        x="ward",
        y="hospital",
        z="occ",
        color_continuous_scale="Reds"
    ),
    use_container_width=True
)

# ================= DATA TABLE =================
st.subheader("📋 Live Bed View")
data["status"] = data["occupied"].map({1: "Occupied", 0: "Available"})
st.dataframe(data[["date", "hospital", "ward", "bed_id", "status"]], use_container_width=True)
