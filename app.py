import streamlit as st
import pandas as pd

from core.preprocess import load_subject_data
from core.student_analytics import student_summary
from core.predictor import predict_subject
from core.slm_client import generate_student_report


# ---------------- CONFIG ----------------

st.set_page_config(
    page_title="Academic Intelligence Platform",
    layout="wide"
)

@st.cache_data
def load_data():
    df = load_subject_data()
    df.columns = df.columns.str.strip()
    return df

df = load_data()

# ---------------- UI ----------------

st.title("🎓 Academic Intelligence Platform")

tabs = st.tabs([
    "📁 Dataset Preview",
    "📊 Student Performance Dashboard",
    "📉 Subject Risk Analytics",
    "🎓 Admission Risk Prediction"
])

# ====================================================
# TAB 0 — DATASET PREVIEW
# ====================================================

with tabs[0]:

    st.header("📁 Academic Dataset Preview")

    col1, col2, col3 = st.columns(3)

    col1.metric("Total Records", len(df))
    col2.metric("Total Students", df["Register Number"].nunique())
    col3.metric("Total Subjects", df["Course Code"].nunique())

    st.subheader("Raw Dataset")

    st.dataframe(df, use_container_width=True)


# ====================================================
# TAB 1 — STUDENT DASHBOARD
# ====================================================

with tabs[1]:

    st.header("📊 Student Performance Dashboard")

    student_list = sorted(df["Register Number"].astype(str).unique())

    reg_no = st.selectbox(
        "Select Register Number",
        student_list
    )

    analyze_btn = st.button("Analyze Student")

    if analyze_btn:

        result = student_summary(df, reg_no)

        if result is None:
            st.error("Student Not Found ❌")

        else:

            st.subheader(f"Student Name: {result['student_name']}")

            # ---------------- METRICS ----------------

            col1, col2, col3 = st.columns(3)

            col1.metric("Avg Internal", result["avg_internal"])
            col2.metric("Avg External", result["avg_external"])
            col3.metric("Avg GP", result["avg_gp"])

            # ---------------- WEAK INTERNAL ----------------

            st.subheader("Weak Internal Subjects")

            if len(result["weak_subjects"]) == 0:
                st.success("No weak internal subjects detected ✅")
            else:
                st.dataframe(result["weak_subjects"], use_container_width=True)

            # ---------------- ML RISK ----------------

            st.subheader("Predicted Risk Subjects")

            risk_rows = []

            for _, row in result["raw"].iterrows():

                sem = row["Sem No"]
                course = row["Course Code"]
                internal = row["Internal Mark"]
                gap = row["Internal-External Gap"]
                credit = row["Credit Points"]

                pred, prob = predict_subject(sem, course, internal, gap, credit)

                if prob is not None and prob < 0.6:
                    risk_rows.append({
                        "Course Code": course,
                        "Course Name": row["Course Name"],
                        "Pass Probability (%)": round(prob * 100, 2)
                    })

            if len(risk_rows) == 0:
                st.success("No high-risk subjects predicted ✅")
            else:
                st.dataframe(pd.DataFrame(risk_rows), use_container_width=True)

            # ---------------- GAP ----------------

            st.subheader("High Internal-External Gap")

            if len(result["gap_subjects"]) == 0:
                st.success("No abnormal gap detected ✅")
            else:
                st.dataframe(result["gap_subjects"], use_container_width=True)

            # ---------------- AI REPORT ----------------

            with st.spinner("Generating AI Academic Report..."):
                report = generate_student_report(result)

            st.subheader("🧠 AI Academic Advisor Report")
            st.write(report)


# ====================================================
# TAB 2 — SUBJECT RISK ANALYTICS
# ====================================================

with tabs[2]:

    st.header("📉 Subject Risk Analytics")

    subject_stats = df.groupby("Course Code")["Result_Binary"].mean().reset_index()

    subject_stats["Fail Rate"] = 1 - subject_stats["Result_Binary"]

    def risk_label(x):
        if x >= 0.9:
            return "LOW"
        elif x >= 0.75:
            return "MEDIUM"
        else:
            return "HIGH"

    subject_stats["Risk Level"] = subject_stats["Result_Binary"].apply(risk_label)

    subject_stats.columns = ["Course Code", "Pass Rate", "Fail Rate", "Risk Level"]

    st.dataframe(subject_stats, use_container_width=True)

    st.subheader("Fail Rate Visualization")

    st.bar_chart(subject_stats.set_index("Course Code")["Fail Rate"])


# ====================================================
# TAB 3 — ADMISSION RISK PREDICTION
# ====================================================

with tabs[3]:

    st.header("🎓 New Admission Student Academic Projection")

    uploaded_file = st.file_uploader(
        "Upload New Student Dataset (Excel)",
        type=["xlsx"]
    )

    if uploaded_file:

        new_df = pd.read_excel(uploaded_file)
        new_df.columns = new_df.columns.str.strip()

        st.subheader("Uploaded Admission Dataset")

        st.dataframe(new_df, use_container_width=True)

        if st.button("Generate Academic Projection"):

            from core.projection_predictor import predict_new_students

            subject_template = pd.read_csv("models/subject_template.csv")

            with st.spinner("Projecting academic performance..."):

                projected_df = predict_new_students(
                    new_df,
                    subject_template
                )

                from core.slm_client import generate_projection_summary

                with st.spinner("Generating AI Academic Planning Summary..."):
                    batch_report = generate_projection_summary(projected_df)

                st.subheader("🧠 AI Batch Academic Planning Report")
                st.write(batch_report)  

            st.success("Projection Completed")

            st.subheader("Projected Academic Dataset")

            st.dataframe(projected_df, use_container_width=True)

            st.download_button(
                "Download Projected Dataset",
                projected_df.to_csv(index=False),
                "projected_academic_results.csv",
                mime="text/csv"
            )
