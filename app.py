import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

st.set_page_config(
    page_title="India Unemployment Analysis",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------- Theme / CSS ----------
st.markdown("""
<style>
    .stApp { background: #f6f8fb; }
    [data-testid="stSidebar"] { background: #111827; }
    [data-testid="stSidebar"] * { color: #f9fafb !important; }
    .hero {
        padding: 28px 30px;
        border-radius: 18px;
        background: linear-gradient(135deg, #111827 0%, #1f2937 60%, #334155 100%);
        color: white;
        margin-bottom: 22px;
        box-shadow: 0 8px 25px rgba(15,23,42,.12);
    }
    .hero h1 { margin: 0 0 8px 0; font-size: 34px; }
    .hero p { margin: 0; color: #d1d5db; font-size: 15px; }
    .section-title { font-size: 22px; font-weight: 700; color: #111827; margin: 20px 0 10px; }
    .insight {
        background: white; border-left: 4px solid #2563eb; padding: 14px 16px;
        border-radius: 10px; margin: 8px 0; box-shadow: 0 2px 10px rgba(15,23,42,.05);
    }
    div[data-testid="stMetric"] {
        background: white; border-radius: 12px; padding: 12px 15px;
        box-shadow: 0 2px 10px rgba(15,23,42,.06); border: 1px solid #e5e7eb;
    }
</style>
""", unsafe_allow_html=True)

# ---------- Data ----------
@st.cache_data

def load_data():
    candidates = [
        Path("dataset/Unemployment in India.csv"),
        Path("Unemployment_Rate_upto_11_2020.csv"),
    ]
    path = next((p for p in candidates if p.exists()), None)
    if path is None:
        st.error("Dataset not found. Put 'Unemployment in India.csv' in the same folder as app.py.")
        st.stop()

    df = pd.read_csv(path)
    df.columns = df.columns.str.strip()
    df["Date"] = pd.to_datetime(df["Date"], dayfirst=True, errors="coerce")
    df["Region"] = df["Region"].astype(str).str.strip()
    df["Area"] = df["Area"].astype(str).str.strip()
    df["Frequency"] = df["Frequency"].astype(str).str.strip()
    df = df.dropna(subset=["Date", "Estimated Unemployment Rate (%)"])
    df["Year"] = df["Date"].dt.year
    df["Month"] = df["Date"].dt.month_name().str[:3]
    df["Period"] = df["Date"].apply(
        lambda x: "Pre-COVID" if x < pd.Timestamp("2020-03-01")
        else ("COVID Period" if x <= pd.Timestamp("2020-06-30") else "Post-Lockdown")
    )
    return df

df = load_data()
rate_col = "Estimated Unemployment Rate (%)"
employed_col = "Estimated Employed"
participation_col = "Estimated Labour Participation Rate (%)"

# ---------- Sidebar ----------
st.sidebar.markdown("## 📊 Dashboard Controls")
st.sidebar.caption("Filter the unemployment dataset interactively.")

regions = sorted(df["Region"].dropna().unique())
areas = sorted(df["Area"].dropna().unique())
years = sorted(df["Year"].dropna().unique())

selected_regions = st.sidebar.multiselect("Region", regions, default=regions)
selected_areas = st.sidebar.multiselect("Area", areas, default=areas)
selected_years = st.sidebar.multiselect("Year", years, default=years)

min_date, max_date = df["Date"].min().date(), df["Date"].max().date()
date_range = st.sidebar.date_input("Date range", value=(min_date, max_date), min_value=min_date, max_value=max_date)

if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date, end_date = min_date, max_date

filtered = df[
    df["Region"].isin(selected_regions)
    & df["Area"].isin(selected_areas)
    & df["Year"].isin(selected_years)
    & (df["Date"].dt.date >= start_date)
    & (df["Date"].dt.date <= end_date)
].copy()

if filtered.empty:
    st.warning("No records match the selected filters. Adjust the sidebar filters.")
    st.stop()

# ---------- Header ----------
st.markdown("""
<div class="hero">
    <h1>India Unemployment Analysis</h1>
    <p>Interactive data science dashboard for unemployment trends, COVID-19 impact, regional differences and labour-market indicators.</p>
</div>
""", unsafe_allow_html=True)

# ---------- KPIs ----------
avg_rate = filtered[rate_col].mean()
peak_rate = filtered[rate_col].max()
peak_row = filtered.loc[filtered[rate_col].idxmax()]
avg_employed = filtered[employed_col].mean() if employed_col in filtered else 0
avg_participation = filtered[participation_col].mean() if participation_col in filtered else 0

c1, c2, c3, c4 = st.columns(4)
c1.metric("Average Unemployment", f"{avg_rate:.2f}%")
c2.metric("Peak Unemployment", f"{peak_rate:.2f}%", f"{peak_row['Date'].strftime('%b %Y')}")
c3.metric("Avg. Estimated Employed", f"{avg_employed/1e6:.2f}M")
c4.metric("Labour Participation", f"{avg_participation:.2f}%")

# ---------- Tabs ----------
tab1, tab2, tab3, tab4 = st.tabs(["📈 Overview", "🦠 COVID-19 Impact", "🗺️ Regional Analysis", "🔎 Data & Insights"])

# ---------- Overview ----------
with tab1:
    st.markdown('<div class="section-title">Overall Unemployment Trend</div>', unsafe_allow_html=True)
    monthly = filtered.groupby("Date", as_index=False)[rate_col].mean().sort_values("Date")

    fig = px.line(monthly, x="Date", y=rate_col, markers=True,
                  title="Average Unemployment Rate Over Time",
                  labels={rate_col: "Unemployment Rate (%)", "Date": "Date"})
    fig.add_vrect(x0="2020-03-01", x1="2020-06-30", fillcolor="red", opacity=0.08,
                  line_width=0, annotation_text="COVID period", annotation_position="top left")
    fig.update_layout(height=450, hovermode="x unified", margin=dict(l=20,r=20,t=60,b=20))
    st.plotly_chart(fig, use_container_width=True)

    left, right = st.columns(2)
    with left:
        area_avg = filtered.groupby("Area", as_index=False)[rate_col].mean()
        fig_area = px.bar(area_avg, x="Area", y=rate_col, text_auto=".2f",
                          title="Rural vs Urban Average Unemployment",
                          labels={rate_col: "Unemployment Rate (%)"})
        fig_area.update_layout(height=370)
        st.plotly_chart(fig_area, use_container_width=True)
    with right:
        year_avg = filtered.groupby("Year", as_index=False)[rate_col].mean()
        fig_year = px.bar(year_avg, x="Year", y=rate_col, text_auto=".2f",
                          title="Average Unemployment by Year",
                          labels={rate_col: "Unemployment Rate (%)"})
        fig_year.update_layout(height=370)
        st.plotly_chart(fig_year, use_container_width=True)

# ---------- COVID ----------
with tab2:
    st.markdown('<div class="section-title">COVID-19 Impact Analysis</div>', unsafe_allow_html=True)

    covid = filtered[filtered["Date"] >= "2020-01-01"].groupby("Date", as_index=False)[rate_col].mean()
    fig_covid = px.line(covid, x="Date", y=rate_col, markers=True,
                        title="Unemployment During the COVID-19 Period",
                        labels={rate_col: "Unemployment Rate (%)"})
    fig_covid.add_vrect(x0="2020-03-25", x1="2020-05-31", fillcolor="red", opacity=0.10,
                        line_width=0, annotation_text="National lockdown phase", annotation_position="top left")
    fig_covid.update_layout(height=430, hovermode="x unified")
    st.plotly_chart(fig_covid, use_container_width=True)

    pre = df[df["Date"] < "2020-03-01"][rate_col].mean()
    covid_avg = df[(df["Date"] >= "2020-03-01") & (df["Date"] <= "2020-06-30")][rate_col].mean()
    change = covid_avg - pre

    a, b, c = st.columns(3)
    a.metric("Pre-COVID Avg.", f"{pre:.2f}%")
    b.metric("COVID Period Avg.", f"{covid_avg:.2f}%")
    c.metric("Increase", f"{change:+.2f} percentage points")

    monthly_covid = df[(df["Date"] >= "2020-01-01") & (df["Date"] <= "2020-06-30")].copy()
    monthly_covid = monthly_covid.groupby(monthly_covid["Date"].dt.strftime("%b %Y"), as_index=False)[rate_col].mean()
    monthly_covid.columns = ["Month", "Average Unemployment"]
    st.dataframe(monthly_covid.style.format({"Average Unemployment": "{:.2f}%"}), use_container_width=True, hide_index=True)

    st.markdown("<div class='insight'><b>Key finding:</b> The dataset shows a sharp unemployment shock in April–May 2020, followed by a substantial decline in June 2020.</div>", unsafe_allow_html=True)

# ---------- Regional ----------
with tab3:
    st.markdown('<div class="section-title">Regional Differences</div>', unsafe_allow_html=True)
    region_avg = filtered.groupby("Region", as_index=False)[rate_col].mean().sort_values(rate_col, ascending=False)

    fig_region = px.bar(region_avg, x=rate_col, y="Region", orientation="h",
                        title="Average Unemployment Rate by Region",
                        labels={rate_col: "Average Unemployment Rate (%)"})
    fig_region.update_layout(height=max(500, len(region_avg) * 24), yaxis=dict(categoryorder="total ascending"))
    st.plotly_chart(fig_region, use_container_width=True)

    top = region_avg.head(10)
    bottom = region_avg.tail(10).sort_values(rate_col)
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Highest 10 regions**")
        st.dataframe(top.style.format({rate_col: "{:.2f}%"}), use_container_width=True, hide_index=True)
    with col2:
        st.markdown("**Lowest 10 regions**")
        st.dataframe(bottom.style.format({rate_col: "{:.2f}%"}), use_container_width=True, hide_index=True)

    st.markdown('<div class="section-title">COVID Impact by Region</div>', unsafe_allow_html=True)
    pre_region = df[df["Date"] < "2020-03-01"].groupby("Region")[rate_col].mean()
    covid_region = df[(df["Date"] >= "2020-03-01") & (df["Date"] <= "2020-06-30")].groupby("Region")[rate_col].mean()
    impact = pd.DataFrame({"Pre-COVID": pre_region, "COVID": covid_region}).dropna()
    impact["Change (pp)"] = impact["COVID"] - impact["Pre-COVID"]
    impact = impact.sort_values("Change (pp)", ascending=False).reset_index()

    fig_impact = px.bar(impact.head(15), x="Change (pp)", y="Region", orientation="h",
                        title="Top 15 Regions by Increase During COVID-19",
                        labels={"Change (pp)": "Change in Unemployment (percentage points)"})
    fig_impact.update_layout(height=520, yaxis=dict(categoryorder="total ascending"))
    st.plotly_chart(fig_impact, use_container_width=True)

# ---------- Data & Insights ----------
with tab4:
    st.markdown('<div class="section-title">Data Quality</div>', unsafe_allow_html=True)
    q1, q2, q3, q4 = st.columns(4)
    q1.metric("Rows", f"{len(df):,}")
    q2.metric("Columns", f"{df.shape[1]-3}")
    q3.metric("Regions", f"{df['Region'].nunique()}")
    q4.metric("Date Range", f"{df['Date'].min():%b %Y} – {df['Date'].max():%b %Y}")

    st.markdown("**Dataset preview**")
    st.dataframe(filtered.drop(columns=["Year", "Month", "Period"], errors="ignore"), use_container_width=True, hide_index=True)

    csv = filtered.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Download filtered data", csv, "filtered_unemployment_data.csv", "text/csv")

    st.markdown('<div class="section-title">Key Insights</div>', unsafe_allow_html=True)
    peak_month = peak_row["Date"].strftime("%B %Y")
    st.markdown(f"""
    <div class="insight"><b>1. Peak unemployment:</b> The highest filtered unemployment rate is <b>{peak_rate:.2f}%</b>, recorded in <b>{peak_month}</b>.</div>
    <div class="insight"><b>2. COVID shock:</b> April and May 2020 show a major rise in unemployment compared with the pre-COVID period.</div>
    <div class="insight"><b>3. Regional variation:</b> Average unemployment differs considerably between regions, so policy responses should not assume uniform effects.</div>
    <div class="insight"><b>4. Labour-market context:</b> Unemployment should be interpreted alongside employment and labour participation rather than as a standalone metric.</div>
    <div class="insight"><b>5. Seasonality limitation:</b> This dataset covers roughly one year, so it is not sufficient for a strong multi-year seasonal conclusion.</div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="section-title">Project Conclusion</div>', unsafe_allow_html=True)
    st.write(
        "The analysis demonstrates a pronounced deterioration in India's labour market during the early COVID-19 period, "
        "with unemployment peaking around April–May 2020 and declining afterward. Regional and rural/urban differences "
        "highlight the need for targeted employment policies."
    )

st.caption("Data Science Internship — Unemployment Analysis | Built with Python, Pandas, Plotly and Streamlit")
