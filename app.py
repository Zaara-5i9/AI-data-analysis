"""
AI Data Analysis App
---------------------
Upload a spreadsheet, get instant charts + summary stats, and ask
questions about your data in plain English (powered by OpenAI).

Run with:  streamlit run app.py
"""

import io

import pandas as pd
import plotly.express as px
import streamlit as st

# ---------------------------------------------------------------------------
# Page setup
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="AI Data Analysis",
    page_icon="📊",
    layout="wide",
)

st.title("📊 AI Data Analysis")
st.caption("Turn raw data into actionable insights in seconds.")


# ---------------------------------------------------------------------------
# Sidebar: file upload + OpenAI key
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("1. Upload your data")
    uploaded_file = st.file_uploader(
        "CSV or Excel file", type=["csv", "xlsx", "xls"]
    )

    st.header("2. Connect OpenAI (optional)")
    api_key = st.text_input(
        "OpenAI API key",
        type="password",
        help="Get one at platform.openai.com/api-keys. "
        "Needed only for the 'Ask your data' feature below — "
        "the charts and summaries work without it.",
    )
    model_name = st.selectbox(
        "Model",
        options=["gpt-4o-mini", "gpt-4o", "gpt-4.1-mini"],
        index=0,
        help="gpt-4o-mini is the cheapest/fastest option and works well for this.",
    )

    st.divider()
    st.caption(
        "Your API key is only used in this browser session to call OpenAI "
        "directly — it isn't stored or sent anywhere else."
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def load_data(file) -> pd.DataFrame:
    name = file.name.lower()
    if name.endswith(".csv"):
        return pd.read_csv(file)
    return pd.read_excel(file)


def detect_date_column(df: pd.DataFrame):
    """Return the first column that looks like a date, if any."""
    for col in df.columns:
        if "date" in col.lower() or "time" in col.lower():
            try:
                pd.to_datetime(df[col], errors="raise")
                return col
            except Exception:
                continue
    return None


def build_data_context(df: pd.DataFrame, max_rows: int = 8) -> str:
    """Summarize the dataframe as text so it can be sent to the LLM
    without shipping the whole dataset."""
    buffer = io.StringIO()
    df.info(buf=buffer)
    info_str = buffer.getvalue()

    describe_str = df.describe(include="all").transpose().to_string()
    sample_str = df.head(max_rows).to_string()

    return (
        f"Dataset shape: {df.shape[0]} rows x {df.shape[1]} columns\n\n"
        f"Column info:\n{info_str}\n\n"
        f"Summary statistics:\n{describe_str}\n\n"
        f"Sample rows:\n{sample_str}"
    )


def ask_openai(question: str, context: str, api_key: str, model: str) -> str:
    from openai import OpenAI

    client = OpenAI(api_key=api_key)
    system_prompt = (
        "You are a helpful data analyst. You are given a description of a "
        "dataset (its columns, summary statistics, and a few sample rows), "
        "not the full data. Answer the user's question as accurately as "
        "possible using only this information. If the exact answer can't be "
        "computed from the summary provided, say what you can tell from the "
        "summary and be explicit about the limitation. Keep answers concise "
        "and concrete, using numbers where you can."
    )
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"Dataset summary:\n{context}\n\nQuestion: {question}",
            },
        ],
        temperature=0.2,
    )
    return response.choices[0].message.content


# ---------------------------------------------------------------------------
# Main app
# ---------------------------------------------------------------------------
if uploaded_file is None:
    st.info("👈 Upload a CSV or Excel file from the sidebar to get started.")
    st.stop()

df = load_data(uploaded_file)

# --- KPI row -----------------------------------------------------------
numeric_cols = df.select_dtypes(include="number").columns.tolist()
categorical_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
missing_pct = round(df.isna().mean().mean() * 100, 1)

k1, k2, k3, k4 = st.columns(4)
k1.metric("Rows", f"{df.shape[0]:,}")
k2.metric("Columns", df.shape[1])
k3.metric("Numeric columns", len(numeric_cols))
k4.metric("Missing data", f"{missing_pct}%")

# --- Data preview --------------------------------------------------------
st.subheader("Data preview")
st.dataframe(df.head(20), use_container_width=True)

with st.expander("Summary statistics"):
    st.dataframe(df.describe(include="all").transpose(), use_container_width=True)

# --- Auto charts -----------------------------------------------------------
st.subheader("Charts")

date_col = detect_date_column(df)

chart_cols = st.columns(2)

# Trend chart if a date-like column exists and there's at least one numeric column
if date_col and numeric_cols:
    with chart_cols[0]:
        y_col = st.selectbox("Trend — value over time", numeric_cols, key="trend_y")
        trend_df = df[[date_col, y_col]].copy()
        trend_df[date_col] = pd.to_datetime(trend_df[date_col], errors="coerce")
        trend_df = trend_df.dropna().sort_values(date_col)
        fig = px.line(trend_df, x=date_col, y=y_col, markers=True)
        st.plotly_chart(fig, use_container_width=True)

# Distribution of a numeric column
if numeric_cols:
    with chart_cols[1 if date_col else 0]:
        num_col = st.selectbox("Distribution", numeric_cols, key="dist_col")
        fig = px.histogram(df, x=num_col)
        st.plotly_chart(fig, use_container_width=True)

# Category breakdown
if categorical_cols:
    with chart_cols[1]:
        cat_col = st.selectbox("Category breakdown", categorical_cols, key="cat_col")
        counts = df[cat_col].value_counts().head(10).reset_index()
        counts.columns = [cat_col, "count"]
        fig = px.pie(counts, names=cat_col, values="count")
        st.plotly_chart(fig, use_container_width=True)

# Correlation heatmap
if len(numeric_cols) >= 2:
    st.subheader("Correlation between numeric columns")
    corr = df[numeric_cols].corr()
    fig = px.imshow(corr, text_auto=".2f", color_continuous_scale="RdBu_r", zmin=-1, zmax=1)
    st.plotly_chart(fig, use_container_width=True)

# --- Ask your data -----------------------------------------------------------
st.subheader("💬 Ask your data")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

for role, msg in st.session_state.chat_history:
    with st.chat_message(role):
        st.markdown(msg)

question = st.chat_input("e.g. Which category had the highest growth last month?")

if question:
    st.session_state.chat_history.append(("user", question))
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        if not api_key:
            answer = (
                "I need an OpenAI API key to answer questions about your data — "
                "add one in the sidebar (get one free at platform.openai.com/api-keys), "
                "then ask again."
            )
            st.warning(answer)
        else:
            with st.spinner("Thinking..."):
                try:
                    context = build_data_context(df)
                    answer = ask_openai(question, context, api_key, model_name)
                    st.markdown(answer)
                except Exception as e:
                    answer = f"Something went wrong calling OpenAI: {e}"
                    st.error(answer)

    st.session_state.chat_history.append(("assistant", answer))
