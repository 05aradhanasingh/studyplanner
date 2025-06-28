import streamlit as st
import pandas as pd
from datetime import time, datetime
from fpdf import FPDF
import io
import time as t
import plotly.express as px
import os

# --- Setup ---
st.set_page_config(page_title="Study Planner", layout="centered")

# --- CSS ---
def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

local_css("styles.css")

# --- File Paths ---
DATA_DIR = "data"
DATA_FILE = os.path.join(DATA_DIR, "productivity_log.csv")
os.makedirs(DATA_DIR, exist_ok=True)

# --- Helper Functions ---
def load_productivity_log():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    return pd.DataFrame(columns=["Timestamp", "Minutes", "Date"])

def save_productivity_log(df):
    df.drop_duplicates(inplace=True)
    df.to_csv(DATA_FILE, index=False)

# --- Initialize session state ---
if "start_time" not in st.session_state:
    st.session_state["start_time"] = None
if "elapsed" not in st.session_state:
    st.session_state["elapsed"] = 0
if "productivity_log" not in st.session_state:
    st.session_state["productivity_log"] = load_productivity_log().to_dict(orient="records")
if "tasks" not in st.session_state:
    st.session_state["tasks"] = []

# --- Header Layout ---
col_left, _, col_right = st.columns([1, 4, 1])

with col_left:
    if st.button("Start Timer"):
        st.session_state.start_time = t.time()
        st.success("Timer started!")

    if st.button("Stop Timer"):
        if st.session_state.start_time is not None:
            session_time = t.time() - st.session_state.start_time
            st.session_state.elapsed += session_time
            new_entry = {
                "Timestamp": datetime.now().replace(second=0, microsecond=0).strftime("%H:%M"),
                "Minutes": round(session_time / 60, 2),
                "Date": datetime.now().strftime("%Y-%m-%d")
            }
            st.session_state["productivity_log"].append(new_entry)
            df_all = pd.DataFrame(st.session_state["productivity_log"])
            save_productivity_log(df_all)
            st.session_state.start_time = None

    elapsed_sec = int(st.session_state.elapsed)
    hours, remainder = divmod(elapsed_sec, 3600)
    minutes, seconds = divmod(remainder, 60)
    st.markdown(
        f"<b>Time Tracked:</b><br>{hours} hours<br>{minutes} minutes<br>{seconds} seconds>",
        unsafe_allow_html=True
    )

with col_right:
    st.image("avatar1.png", width=120)

st.title("Study Planner")

# --- Task Input ---
st.subheader("Add New Task")

with st.form("add_task_form"):
    col1, col2 = st.columns(2)
    subject = col1.text_input("Subject")
    topic = col2.text_input("Topic")

    col3, col4 = st.columns(2)
    date = col3.date_input("Date")
    time_slot = col4.time_input("Time", time(10, 0))

    submitted = st.form_submit_button("Add Task")
    if submitted and subject and topic:
        st.session_state["tasks"].append({
            "Subject": subject,
            "Topic": topic,
            "Date": date.strftime("%Y-%m-%d"),
            "Time": time_slot.strftime("%H:%M"),
            "Completed": False
        })
        st.success("Task added.")

# --- Study Plan Display ---
st.subheader("Your Study Plan")

if st.session_state["tasks"]:
    df = pd.DataFrame(st.session_state["tasks"])
    updated_tasks = []

    for i, row in df.iterrows():
        col1, col2, col3, col4, col5, col6 = st.columns([2, 2, 2, 1.5, 1, 1])
        col1.write(row["Subject"])
        col2.write(row["Topic"])
        col3.write(row["Date"])
        col4.write(row["Time"])
        is_done = col5.checkbox("Done", key=f"done_{i}", value=row["Completed"])
        delete = col6.button("❌", key=f"delete_{i}")

        if not delete:
            row["Completed"] = is_done
            updated_tasks.append(row)

    st.session_state["tasks"] = updated_tasks

    st.download_button("Download as CSV", df.to_csv(index=False), "study_plan.csv", "text/csv")

    def create_pdf(dataframe):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, "Study Plan", ln=True, align="C")
        pdf.ln(10)
        for idx, row in dataframe.iterrows():
            line = f"{idx + 1}. {row['Subject']} - {row['Topic']} on {row['Date']} at {row['Time']} | Done: {'Yes' if row['Completed'] else 'No'}"
            pdf.cell(200, 10, line, ln=True)
        return io.BytesIO(pdf.output(dest='S').encode('latin1'))

    st.download_button("Download as PDF", create_pdf(df), "study_plan.pdf", "application/pdf")
else:
    st.info("No tasks added yet.")

# --- Daily Productivity Plot ---
st.subheader("Today's Productivity")

prod_df = pd.DataFrame(st.session_state["productivity_log"]).drop_duplicates()
today_str = datetime.now().strftime("%Y-%m-%d")
prod_df_day = prod_df[prod_df["Date"] == today_str].copy()

if not prod_df_day.empty:
    prod_df_day["Timestamp_dt"] = pd.to_datetime(prod_df_day["Timestamp"], format="%H:%M")
    prod_df_day.sort_values(by="Timestamp_dt", inplace=True)

    fig = px.line(prod_df_day, x="Timestamp_dt", y="Minutes", title="Tracked Study Time Today", markers=True)
    fig.update_traces(line=dict(color="#cd8495", width=3), marker=dict(color="#cd8495", size=8))
    fig.update_layout(
        xaxis_title="Time of Day", yaxis_title="Minutes Spent",
        xaxis=dict(tickformat="%H:%M", title_font=dict(color="#cd8495"), tickfont=dict(color="#cd8495")),
        yaxis=dict(title_font=dict(color="#cd8495"), tickfont=dict(color="#cd8495")),
        font=dict(color="#cd8495"),
        title_font=dict(color="#cd8495"),
        plot_bgcolor="#ffe6f0",
        paper_bgcolor="#ffe6f0"
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No study sessions recorded yet.")

# --- Weekly Productivity Plot ---
st.subheader("Weekly Productivity")

if not prod_df.empty and "Date" in prod_df.columns:
    prod_df["Date"] = pd.to_datetime(prod_df["Date"])
    today = pd.to_datetime(datetime.today())
    week_df = prod_df[prod_df["Date"] >= (today - pd.Timedelta(days=6))]

    if not week_df.empty:
        week_summary = week_df.groupby(week_df["Date"].dt.strftime("%a %d"))["Minutes"].sum().reset_index()
        fig_week = px.line(week_summary, x="Date", y="Minutes", title="Weekly Study Summary", markers=True)
        fig_week.update_traces(line=dict(color="#cd8495", width=3), marker=dict(color="#cd8495", size=8))
        fig_week.update_layout(
            xaxis_title="Day", yaxis_title="Total Minutes",
            xaxis=dict(title_font=dict(color="#cd8495"), tickfont=dict(color="#cd8495")),
            yaxis=dict(title_font=dict(color="#cd8495"), tickfont=dict(color="#cd8495")),
            font=dict(color="#cd8495"),
            title_font=dict(color="#cd8495"),
            plot_bgcolor='#ffe6f0',
            paper_bgcolor='#ffe6f0'
        )
        st.plotly_chart(fig_week, use_container_width=True)
    else:
        st.info("No data for this week yet.")
else:
    st.info("No productivity data available.")
