from __future__ import annotations

from html import escape
from typing import Any, Callable, Iterable

import pandas as pd
import streamlit as st

from core.slm_client import (
    generate_department_report,
    generate_principal_report,
    generate_projection_summary,
    generate_student_report,
    generate_subject_analytics_report,
    generate_subject_report,
)
from core.student_analytics import student_summary

AUTH_USERS: dict[str, dict[str, Any]] = {
    "Student": {
        "user": "student1",
        "pass": "123",
        "register_number": "24BAE001",
    },
    "Faculty": {
        "user": "faculty1",
        "pass": "123",
        "course_code": "24CSI101",
    },
    "Mentor": {
        "user": "mentor1",
        "pass": "123",
        "mentee_ids": [
            "24BAE001",
            "24BAE002",
            "24BAE003",
            "24BAE004",
            "24BAE005",
            "24BAE006",
        ],
    },
    "HOD": {
        "user": "hod1",
        "pass": "123",
        "department": "Aeronautical Engineering",
    },
    "Principal": {
        "user": "principal1",
        "pass": "123",
    },
}

ROLE_SECTIONS: dict[str, list[str]] = {
    "Student": ["Dashboard", "Subject Analytics"],
    "Faculty": ["Dashboard", "Subject Analytics", "Dataset Preview"],
    "Mentor": ["Dashboard", "Subject Analytics", "Dataset Preview"],
    "HOD": ["Dashboard", "Subject Analytics", "New Student Projection", "Dataset Preview"],
    "Principal": ["Dashboard", "Subject Analytics", "New Student Projection", "Dataset Preview"],
}

WEAK_MARK_THRESHOLD = 35
HIGH_GAP_THRESHOLD = 20
LOW_PASS_PROBABILITY = 0.60

REQUIRED_DATA_COLUMNS = [
    "Department",
    "Register Number",
    "Student Name",
    "Sem No",
    "Course Code",
    "Course Name",
    "Internal Mark",
    "External Mark",
    "Internal-External Gap",
    "gp",
    "Credit Points",
    "Result_Binary",
]

REQUIRED_PROJECTION_COLUMNS = [
    "Gender",
    "Department",
    "12th_Percentage",
    "Cutoff",
    "Board",
    "Medium",
    "Parent_Education_Index",
    "Total_Family_Income",
    "Admission_Year",
]


def apply_theme() -> None:
    st.markdown(
        """
        <style>
        :root {
            --bg: #08111f;
            --card: rgba(15, 24, 39, 0.78);
            --border: rgba(148, 163, 184, 0.18);
            --text: #e5eef9;
            --muted: #95a7c3;
            --accent: #5bc0ff;
            --accent-soft: rgba(91, 192, 255, 0.12);
            --success: #3fd29a;
            --shadow: 0 20px 50px rgba(0, 0, 0, 0.28);
        }

        .stApp {
            background:
                radial-gradient(circle at top left, rgba(91, 192, 255, 0.12), transparent 24%),
                radial-gradient(circle at top right, rgba(63, 210, 154, 0.08), transparent 20%),
                linear-gradient(180deg, #07101c 0%, #0a1424 40%, #09101b 100%);
            color: var(--text);
            font-family: "Trebuchet MS", "Segoe UI", sans-serif;
        }

        .block-container {
            padding-top: 1.2rem;
            padding-bottom: 2rem;
            max-width: 1440px;
        }

        [data-testid="stSidebar"] {
            background:
                linear-gradient(180deg, rgba(7, 15, 27, 0.98) 0%, rgba(10, 18, 32, 0.98) 100%);
            border-right: 1px solid var(--border);
        }

        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] div {
            color: var(--text);
        }

        div[data-baseweb="select"] > div,
        div[data-baseweb="input"] > div,
        div[data-testid="stTextInput"] input,
        div[data-testid="stNumberInput"] input {
            background: rgba(8, 17, 31, 0.9);
            color: var(--text);
            border-color: var(--border);
        }

        div[data-testid="stFileUploader"] {
            background: rgba(8, 17, 31, 0.8);
            border: 1px dashed rgba(91, 192, 255, 0.32);
            border-radius: 18px;
            padding: 0.6rem;
        }

        div[data-testid="stMetric"] {
            background: rgba(8, 17, 31, 0.82);
            border: 1px solid var(--border);
            border-radius: 18px;
            padding: 0.7rem 0.9rem;
            box-shadow: var(--shadow);
        }

        div[data-testid="stMetricLabel"] {
            color: var(--muted);
            font-weight: 700;
        }

        div[data-testid="stMetricValue"] {
            color: var(--text);
        }

        div[data-testid="stDataFrame"] {
            border: 1px solid var(--border);
            border-radius: 18px;
            overflow: hidden;
            background: rgba(8, 17, 31, 0.72);
        }

        button[kind="primary"] {
            background: linear-gradient(135deg, #1f6feb 0%, #38bdf8 100%);
            border: none;
            color: #ffffff;
        }

        button[kind="secondary"] {
            background: rgba(8, 17, 31, 0.88);
            border: 1px solid var(--border);
            color: var(--text);
        }

        .hero-panel {
            background:
                linear-gradient(135deg, rgba(12, 25, 45, 0.96) 0%, rgba(10, 18, 32, 0.92) 100%);
            border: 1px solid var(--border);
            border-radius: 28px;
            padding: 1.3rem 1.5rem;
            box-shadow: var(--shadow);
            margin-bottom: 1rem;
        }

        .hero-kicker {
            display: inline-flex;
            align-items: center;
            padding: 0.25rem 0.7rem;
            border-radius: 999px;
            background: var(--accent-soft);
            color: var(--accent);
            font-size: 0.78rem;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        .hero-title {
            margin: 0.8rem 0 0.4rem 0;
            font-size: 2rem;
            line-height: 1.1;
            color: var(--text);
        }

        .hero-copy {
            margin: 0;
            color: var(--muted);
            font-size: 0.98rem;
            line-height: 1.6;
            max-width: 56rem;
        }

        .panel {
            background: rgba(8, 17, 31, 0.78);
            border: 1px solid var(--border);
            border-radius: 22px;
            padding: 1rem 1.05rem;
            box-shadow: var(--shadow);
            margin-bottom: 1rem;
        }

        .panel-title {
            color: var(--text);
            margin: 0 0 0.35rem 0;
            font-size: 1rem;
            font-weight: 800;
        }

        .panel li {
            color: var(--muted);
            line-height: 1.6;
            font-size: 0.94rem;
        }

        .scope-pill {
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
            border-radius: 999px;
            padding: 0.3rem 0.72rem;
            background: rgba(63, 210, 154, 0.12);
            color: var(--success);
            font-size: 0.82rem;
            font-weight: 700;
        }

        .login-shell {
            background: rgba(10, 18, 32, 0.82);
            border: 1px solid var(--border);
            border-radius: 28px;
            padding: 1.2rem 1.25rem;
            box-shadow: var(--shadow);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def initialize_session_state() -> None:
    defaults = {
        "authenticated": False,
        "user_role": None,
        "username": None,
        "user_profile": {},
        "nav_section": None,
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def _rerun() -> None:
    rerun = getattr(st, "rerun", None)
    if callable(rerun):
        rerun()
        return

    experimental_rerun = getattr(st, "experimental_rerun", None)
    if callable(experimental_rerun):
        experimental_rerun()


def logout() -> None:
    st.session_state.clear()
    _rerun()


def render_login_screen() -> None:
    left_col, right_col = st.columns([1.1, 0.9], gap="large")

    with left_col:
        render_page_header(
            "Academic Intelligence Platform",
            "Role-Based Academic Intelligence Dashboard",
            (
                "A streamlined Streamlit experience with role-specific dashboards, subject analytics, "
                "new student projection, and safer Ollama-backed AI insights."
            ),
        )
        render_html_panel(
            "What changed",
            [
                "Single sidebar navigation instead of tab-heavy screens.",
                "Hardcoded role-based login for Student, Faculty, Mentor, HOD, and Principal.",
                "Cleaner dashboards that keep ML predictions and projection pipelines intact.",
                "Centralized AI calls with timeout handling and user-friendly fallback messages.",
            ],
        )

    with right_col:
        st.subheader("Sign in")
        st.caption("Use one of the hardcoded prototype accounts to open the relevant workspace.")

        with st.form("login_form", clear_on_submit=False):
            role = st.selectbox("Role", list(AUTH_USERS.keys()), key="login_role")
            username = st.text_input("Username", key="login_username")
            password = st.text_input("Password", type="password", key="login_password")
            submitted = st.form_submit_button("Log in", use_container_width=True)

        if submitted:
            credentials = AUTH_USERS.get(role, {})
            if (
                username.strip() == str(credentials.get("user", "")).strip()
                and password == credentials.get("pass")
            ):
                st.session_state["authenticated"] = True
                st.session_state["user_role"] = role
                st.session_state["username"] = username.strip()
                st.session_state["user_profile"] = credentials
                st.session_state["nav_section"] = ROLE_SECTIONS[role][0]
                _rerun()
            else:
                st.error("Invalid username or password for the selected role.")

        with st.expander("View prototype credentials"):
            credential_table = pd.DataFrame(
                [
                    {
                        "Role": role_name,
                        "Username": details["user"],
                        "Password": details["pass"],
                    }
                    for role_name, details in AUTH_USERS.items()
                ]
            )
            st.table(credential_table)


def render_authenticated_app(df: pd.DataFrame, enriched_df: pd.DataFrame) -> None:
    role = str(st.session_state.get("user_role") or "")
    context = get_role_context(enriched_df, role, st.session_state.get("user_profile", {}))
    section = render_sidebar(df, enriched_df, role, context)

    try:
        if section == "Dashboard":
            render_role_dashboard(role, df, enriched_df, context)
        elif section == "Subject Analytics":
            render_subject_analytics(role, enriched_df, context)
        elif section == "New Student Projection":
            render_projection_workspace()
        else:
            render_dataset_preview(enriched_df, role, context)
    except Exception as error:
        st.error(f"Unable to render this section right now: {error}")


def render_sidebar(
    df: pd.DataFrame,
    enriched_df: pd.DataFrame,
    role: str,
    context: dict[str, Any],
) -> str:
    allowed_sections = ROLE_SECTIONS.get(role, ["Dashboard"])
    if st.session_state.get("nav_section") not in allowed_sections:
        st.session_state["nav_section"] = allowed_sections[0]

    scope_df = context.get("scope_df", enriched_df)
    pass_rate = (
        float(scope_df["Result_Binary"].mean() * 100)
        if not scope_df.empty and "Result_Binary" in scope_df.columns
        else 0.0
    )
    health_score = calculate_health_score(scope_df if not scope_df.empty else enriched_df)

    with st.sidebar:
        st.markdown(
            """
            <div class="hero-panel" style="padding:1rem 1rem 0.95rem 1rem;">
                <div class="hero-kicker">Role Access</div>
                <div class="hero-title" style="font-size:1.28rem;">Academic Intelligence Platform</div>
                <p class="hero-copy">Clean navigation, scoped dashboards, and safer AI-assisted insights.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.caption(f"Signed in as {st.session_state.get('username')} ({role})")
        st.markdown(
            f'<div class="scope-pill">{escape(build_scope_label(role, context))}</div>',
            unsafe_allow_html=True,
        )
        st.write("")
        section = st.radio("Navigation", allowed_sections, key="nav_section")

        st.divider()
        st.caption("Current scope")
        metric_col1, metric_col2 = st.columns(2)
        metric_col1.metric("Students", int(scope_df["Register Number"].nunique()) if "Register Number" in scope_df.columns else 0)
        metric_col2.metric("Subjects", int(scope_df["Course Code"].nunique()) if "Course Code" in scope_df.columns else 0)

        metric_col3, metric_col4 = st.columns(2)
        metric_col3.metric("Pass rate", f"{pass_rate:.1f}%")
        metric_col4.metric("Health", f"{health_score:.1f}")

        st.caption(
            f"Institution dataset: {int(df['Register Number'].nunique())} students and {int(df['Course Code'].nunique())} subjects."
        )
        if st.button("Log out", use_container_width=True):
            logout()

    return section


def render_page_header(kicker: str, title: str, subtitle: str) -> None:
    st.markdown(
        f"""
        <div class="hero-panel">
            <div class="hero-kicker">{escape(kicker)}</div>
            <div class="hero-title">{escape(title)}</div>
            <p class="hero-copy">{escape(subtitle)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_section_heading(title: str, subtitle: str) -> None:
    st.subheader(title)
    st.caption(subtitle)


def render_metric_row(metrics: list[dict[str, str]]) -> None:
    if not metrics:
        return

    columns = st.columns(len(metrics))
    for column, metric in zip(columns, metrics):
        with column:
            st.metric(metric["label"], metric["value"])
            if metric.get("caption"):
                st.caption(metric["caption"])


def render_html_panel(title: str, lines: list[str]) -> None:
    bullet_items = "".join(f"<li>{escape(str(line))}</li>" for line in lines)
    st.markdown(
        f"""
        <div class="panel">
            <div class="panel-title">{escape(title)}</div>
            <ul>{bullet_items}</ul>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_ai_panel(
    title: str,
    description: str,
    report_key: str,
    button_label: str,
    generator: Callable[[], str],
) -> None:
    render_section_heading(title, description)
    if st.button(button_label, key=f"{report_key}_button", use_container_width=True):
        try:
            with st.spinner("Generating AI insights..."):
                st.session_state[report_key] = generator()
        except Exception as error:
            st.error(f"AI insights could not be generated: {error}")

    report = st.session_state.get(report_key)
    if report:
        st.markdown(report)
    else:
        st.info("No AI insight generated yet.")


def render_role_dashboard(
    role: str,
    df: pd.DataFrame,
    enriched_df: pd.DataFrame,
    context: dict[str, Any],
) -> None:
    if role == "Student":
        render_student_dashboard(context)
    elif role == "Faculty":
        render_faculty_dashboard(enriched_df, context)
    elif role == "Mentor":
        render_mentor_dashboard(context)
    elif role == "HOD":
        render_hod_dashboard(context)
    else:
        render_principal_dashboard(enriched_df, context)


def render_student_dashboard(context: dict[str, Any]) -> None:
    register_number = context.get("register_number")
    scope_df = context.get("scope_df", pd.DataFrame())
    profile = build_student_profile(scope_df, register_number) if register_number else None

    render_page_header(
        "Student Dashboard",
        "Personal Academic Performance",
        "Your dashboard focuses on semester performance, weak subjects, ML-driven risk prediction, and one-click AI guidance.",
    )

    if profile is None:
        st.error("No student record is available for this login profile.")
        return

    render_metric_row(
        [
            {"label": "Average Internal", "value": f"{profile['avg_internal']:.1f}", "caption": "Coursework signal"},
            {"label": "Average External", "value": f"{profile['avg_external']:.1f}", "caption": "Exam performance"},
            {"label": "Average GPA", "value": f"{profile['avg_gp']:.2f}", "caption": "Across completed subjects"},
            {"label": "Pass Rate", "value": f"{profile['pass_rate']:.1f}%", "caption": "Historical completion rate"},
        ]
    )

    left_col, right_col = st.columns([1.25, 0.95], gap="large")

    with left_col:
        render_section_heading("Semester trend", "Internal marks, external marks, and GPA across semesters.")
        trend_frame = profile["semester_trend"].set_index("Sem No")[
            ["Average Internal", "Average External", "Average GP"]
        ]
        if trend_frame.empty:
            st.info("Semester trend will appear when student semester data is available.")
        else:
            st.line_chart(trend_frame, use_container_width=True)

    with right_col:
        render_section_heading("Risk summary", "A simple view of immediate academic pressure areas.")
        risk_lines = [
            f"Student: {profile['student_name'].strip()} ({register_number})",
            f"Weak internal subjects: {profile['weak_count']}",
            f"High gap subjects: {profile['gap_count']}",
            f"Predicted high-risk subjects: {len(profile['risk_subjects'])}",
            f"Risk band: {profile['risk_band']}",
        ]
        render_html_panel("Current posture", risk_lines)

    weak_col, risk_col = st.columns(2, gap="large")

    with weak_col:
        render_section_heading("Weak subjects", "Subjects below the intervention threshold.")
        if profile["weak_subjects"].empty:
            st.success("No weak internal subjects detected for this student.")
        else:
            st.dataframe(profile["weak_subjects"], use_container_width=True, hide_index=True)

    with risk_col:
        render_section_heading("Risk prediction", "Subjects with lower predicted pass confidence.")
        risk_columns = [
            "Course Code",
            "Course Name",
            "Internal Mark",
            "External Mark",
            "Pass Probability %",
            "Risk Category",
        ]
        risk_view = profile["raw"].loc[
            profile["raw"]["Pass Probability"] < LOW_PASS_PROBABILITY,
            risk_columns,
        ].sort_values(["Pass Probability %", "Internal Mark"])
        if risk_view.empty:
            st.success("No subjects are currently below the configured pass-probability threshold.")
        else:
            st.dataframe(risk_view, use_container_width=True, hide_index=True)

    render_ai_panel(
        title="AI suggestions",
        description="Generate a concise student-facing intervention summary.",
        report_key=f"student_ai_{register_number}",
        button_label="Generate AI suggestions",
        generator=lambda: generate_student_report(profile["summary"]),
    )


def render_faculty_dashboard(
    enriched_df: pd.DataFrame,
    context: dict[str, Any],
) -> None:
    subject_meta = context.get("subject_meta")
    scope_df = context.get("scope_df", pd.DataFrame())

    render_page_header(
        "Faculty Dashboard",
        "Assigned Subject Performance",
        "Faculty view is scoped to one subject, highlighting failure pressure, high-risk students, and immediate intervention points.",
    )

    if subject_meta is None or scope_df.empty:
        st.error("No subject data is available for this faculty profile.")
        return

    high_risk_students = get_high_risk_students(scope_df)
    all_subjects = build_subject_summary(enriched_df)
    subject_ranking = all_subjects[
        ["Subject Label", "Fail Rate %", "High Risk Students", "Average GP"]
    ].head(10)

    render_metric_row(
        [
            {"label": "Failure Rate", "value": f"{subject_meta['Fail Rate %']:.1f}%", "caption": "Assigned subject fail share"},
            {"label": "Average Internal", "value": f"{subject_meta['Average Internal']:.1f}", "caption": "Average coursework mark"},
            {"label": "Average External", "value": f"{subject_meta['Average External']:.1f}", "caption": "Average exam mark"},
            {"label": "High-Risk Students", "value": str(int(subject_meta['High Risk Students'])), "caption": "Below threshold or failed"},
        ]
    )

    chart_col, table_col = st.columns([1.2, 1], gap="large")

    with chart_col:
        render_section_heading("Subject-wise failure view", "Performance spread for the assigned subject.")
        chart_data = scope_df[["Student Name", "Internal Mark", "External Mark"]].sort_values(
            ["Internal Mark", "External Mark"]
        )
        st.bar_chart(
            chart_data.set_index("Student Name")[["Internal Mark", "External Mark"]],
            use_container_width=True,
        )

    with table_col:
        render_section_heading("High-risk students", "Students who need follow-up in this subject.")
        if high_risk_students.empty:
            st.success("No high-risk students are currently flagged for this subject.")
        else:
            st.dataframe(
                high_risk_students[
                    [
                        "Register Number",
                        "Student Name",
                        "Internal Mark",
                        "External Mark",
                        "Pass Probability %",
                        "Risk Category",
                    ]
                ],
                use_container_width=True,
                hide_index=True,
            )

    render_section_heading("Subject ranking snapshot", "How the current subject sits against the rest of the dataset.")
    st.dataframe(subject_ranking, use_container_width=True, hide_index=True)


def render_mentor_dashboard(context: dict[str, Any]) -> None:
    scope_df = context.get("scope_df", pd.DataFrame())

    render_page_header(
        "Mentor Dashboard",
        "Mentee Risk and Attention Queue",
        "Mentor view focuses on mentee coverage, risk distribution, and the students who need attention first.",
    )

    if scope_df.empty:
        st.error("No mentee data is available for this mentor profile.")
        return

    priority_table = build_student_priority_table(scope_df)
    mentee_count = int(priority_table["Register Number"].nunique()) if not priority_table.empty else 0
    high_risk_count = int((priority_table["Risk Band"] == "High").sum()) if not priority_table.empty else 0
    moderate_risk_count = int((priority_table["Risk Band"] == "Moderate").sum()) if not priority_table.empty else 0

    render_metric_row(
        [
            {"label": "Mentees", "value": str(mentee_count), "caption": "Students in this mentor scope"},
            {"label": "High Risk", "value": str(high_risk_count), "caption": "Immediate follow-up needed"},
            {"label": "Moderate Risk", "value": str(moderate_risk_count), "caption": "Watch closely"},
            {"label": "Pass Rate", "value": f"{scope_df['Result_Binary'].mean() * 100:.1f}%", "caption": "Across mentee records"},
        ]
    )

    left_col, right_col = st.columns([1.05, 1], gap="large")

    with left_col:
        render_section_heading("Risk distribution", "Mentee count by blended academic risk band.")
        band_counts = (
            priority_table["Risk Band"].value_counts().reindex(["High", "Moderate", "Low"], fill_value=0)
            if not priority_table.empty
            else pd.Series([0, 0, 0], index=["High", "Moderate", "Low"])
        )
        st.bar_chart(band_counts, use_container_width=True)

    with right_col:
        render_section_heading("Mentee list", "A compact view of all students assigned to this mentor.")
        display_columns = ["Register Number", "Student Name", "Average GP", "Pass Rate %", "Risk Band"]
        st.dataframe(priority_table[display_columns], use_container_width=True, hide_index=True)

    render_section_heading("Students needing attention", "The highest-priority mentees sorted by risk score.")
    st.dataframe(priority_table.head(8), use_container_width=True, hide_index=True)


def render_hod_dashboard(context: dict[str, Any]) -> None:
    scope_df = context.get("scope_df", pd.DataFrame())
    department = context.get("department", "Department")

    render_page_header(
        "HOD Dashboard",
        f"{department} Department Overview",
        "Department-level analytics focus on failure heatmaps, semester trends, and subject bottlenecks that require intervention.",
    )

    if scope_df.empty:
        st.error("No department data is available for this HOD profile.")
        return

    subject_stats = build_subject_summary(scope_df)
    semester_summary = build_semester_summary(scope_df)
    health_score = calculate_health_score(scope_df)

    render_metric_row(
        [
            {"label": "Department Health", "value": f"{health_score:.1f}", "caption": "Blended pass and risk score"},
            {"label": "Pass Rate", "value": f"{scope_df['Result_Binary'].mean() * 100:.1f}%", "caption": "Department success rate"},
            {"label": "Average GPA", "value": f"{scope_df['gp'].mean():.2f}", "caption": "Across loaded semesters"},
            {"label": "High-Risk Subjects", "value": str(int((subject_stats['Risk Level'] == 'High').sum())), "caption": "Subjects needing escalation"},
        ]
    )

    heatmap_col, trend_col = st.columns([1.3, 1], gap="large")

    with heatmap_col:
        render_section_heading("Subject failure heatmap", "Semester-aligned fail rates for faster bottleneck spotting.")
        heatmap = build_subject_heatmap(subject_stats)
        if heatmap.empty:
            st.info("Heatmap is unavailable because the department subject summary is empty.")
        else:
            st.dataframe(heatmap.style.format("{:.1f}%").background_gradient(cmap="Reds"), use_container_width=True)

    with trend_col:
        render_section_heading("Semester trends", "Pass rate, GPA, and marks by semester.")
        trend_chart = semester_summary.set_index("Sem No")[
            ["Pass Rate %", "Average GP", "Average Internal", "Average External"]
        ]
        st.line_chart(trend_chart, use_container_width=True)

    render_section_heading("Top weak subjects", "Most fragile subjects in the department right now.")
    st.dataframe(
        subject_stats[
            [
                "Subject Label",
                "Fail Rate %",
                "High Risk Students",
                "Average Gap",
                "Risk Level",
            ]
        ].head(10),
        use_container_width=True,
        hide_index=True,
    )

    render_ai_panel(
        title="AI department summary",
        description="Generate a short HOD action brief from the current department view.",
        report_key=f"hod_ai_{department}",
        button_label="Generate HOD AI summary",
        generator=lambda: generate_department_report(
            {
                "department": department,
                "health_score": round(health_score, 1),
                "pass_rate": round(float(scope_df["Result_Binary"].mean() * 100), 1),
                "avg_gp": round(float(scope_df["gp"].mean()), 2),
                "top_weak_subjects": subject_stats["Course Name"].head(6).tolist(),
                "semester_summary": semester_summary[["Sem No", "Pass Rate %", "Average GP"]]
                .to_dict(orient="records"),
            }
        ),
    )


def render_principal_dashboard(
    enriched_df: pd.DataFrame,
    context: dict[str, Any],
) -> None:
    scope_df = context.get("scope_df", enriched_df)

    render_page_header(
        "Principal Dashboard",
        "Institution Performance Overview",
        "Executive view tracks overall performance summary, department comparison, and high-level academic risk.",
    )

    if scope_df.empty:
        st.error("No academic data is available for the principal dashboard.")
        return

    subject_stats = build_subject_summary(scope_df)
    semester_summary = build_semester_summary(scope_df)
    department_summary = build_department_summary(scope_df)
    projected_df = st.session_state.get("projection_results")
    projected_department_summary = build_projected_department_summary(projected_df)
    department_comparison = merge_department_comparison(
        department_summary,
        projected_department_summary,
    )
    health_score = calculate_health_score(scope_df)
    high_risk_share = float((scope_df["Pass Probability"] < LOW_PASS_PROBABILITY).mean() * 100)

    render_metric_row(
        [
            {"label": "Health Score", "value": f"{health_score:.1f}", "caption": "Institution-wide academic health"},
            {"label": "Pass Rate", "value": f"{scope_df['Result_Binary'].mean() * 100:.1f}%", "caption": "Overall completion rate"},
            {"label": "Average GPA", "value": f"{scope_df['gp'].mean():.2f}", "caption": "Academic quality signal"},
            {"label": "High-Risk Share", "value": f"{high_risk_share:.1f}%", "caption": "Records below prediction threshold"},
        ]
    )

    comparison_col, risk_col = st.columns([1.2, 1], gap="large")

    with comparison_col:
        render_section_heading("Department comparison", "Historical vs projected performance where projection data exists.")
        if department_comparison.empty:
            st.info("Department comparison will appear once department-level data is available.")
        else:
            st.dataframe(department_comparison, use_container_width=True, hide_index=True)
            if len(department_comparison) == 1:
                st.info("The current historical dataset contains one department. Comparison expands automatically when more departments are loaded.")

    with risk_col:
        render_section_heading("Risk overview", "Subjects with the highest failure pressure.")
        st.dataframe(
            subject_stats[
                [
                    "Department",
                    "Subject Label",
                    "Fail Rate %",
                    "High Risk Students",
                    "Risk Level",
                ]
            ].head(10),
            use_container_width=True,
            hide_index=True,
        )

    render_section_heading("Semester performance summary", "Institution trend across semesters.")
    semester_chart = semester_summary.set_index("Sem No")[
        ["Pass Rate %", "Average GP", "Average Internal", "Average External"]
    ]
    st.line_chart(semester_chart, use_container_width=True)

    render_ai_panel(
        title="AI executive briefing",
        description="Generate a presentation-ready principal summary from the current institutional view.",
        report_key="principal_ai_summary",
        button_label="Generate principal AI briefing",
        generator=lambda: generate_principal_report(
            {
                "health_score": round(health_score, 1),
                "pass_rate": round(float(scope_df["Result_Binary"].mean() * 100), 1),
                "avg_gp": round(float(scope_df["gp"].mean()), 2),
                "projected_pass_rate": (
                    None
                    if not isinstance(projected_df, pd.DataFrame) or projected_df.empty
                    else round(float(projected_df["Result_Binary"].mean() * 100), 1)
                ),
                "top_weak_subjects": subject_stats["Course Name"].head(6).tolist(),
                "department_summary": department_comparison.to_dict(orient="records"),
            }
        ),
    )


def render_subject_analytics(role: str, enriched_df: pd.DataFrame, context: dict[str, Any]) -> None:
    if role == "Student":
        render_student_subject_analytics(context)
    elif role == "Faculty":
        render_faculty_subject_analytics(context)
    elif role == "Mentor":
        render_mentor_subject_analytics(context)
    elif role == "HOD":
        render_hod_subject_analytics(context)
    else:
        render_principal_subject_analytics(enriched_df, context)


def render_student_subject_analytics(context: dict[str, Any]) -> None:
    register_number = context.get("register_number")
    scope_df = context.get("scope_df", pd.DataFrame())
    profile = build_student_profile(scope_df, register_number) if register_number else None

    render_page_header(
        "Subject Analytics",
        "Student Subject Breakdown",
        "A subject-level view of marks, gaps, and risk so the student can see exactly where support is needed.",
    )

    if profile is None:
        st.error("Student subject analytics are unavailable for this profile.")
        return

    render_metric_row(
        [
            {"label": "Subjects", "value": str(len(profile["raw"])), "caption": "Subjects in record"},
            {"label": "Weak Subjects", "value": str(profile["weak_count"]), "caption": "Below internal threshold"},
            {"label": "High Gap", "value": str(profile["gap_count"]), "caption": "Large internal-external gap"},
            {"label": "Predicted Risk", "value": str(len(profile["risk_subjects"])), "caption": "Lower-confidence subjects"},
        ]
    )

    chart_col, table_col = st.columns([1.15, 1], gap="large")

    with chart_col:
        render_section_heading("Subject mark profile", "Internal and external marks by subject.")
        chart_data = profile["raw"][["Course Name", "Internal Mark", "External Mark"]].sort_values(
            ["Internal Mark", "External Mark"]
        )
        st.bar_chart(chart_data.set_index("Course Name"), use_container_width=True)

    with table_col:
        render_section_heading("High gap subjects", "Subjects where exam conversion is weaker than coursework.")
        if profile["gap_subjects"].empty:
            st.success("No abnormal internal-external gaps detected.")
        else:
            st.dataframe(profile["gap_subjects"], use_container_width=True, hide_index=True)

    render_section_heading("Subject record", "Complete student subject history with prediction columns.")
    st.dataframe(
        profile["raw"][
            [
                "Sem No",
                "Course Code",
                "Course Name",
                "Internal Mark",
                "External Mark",
                "gp",
                "Pass Probability %",
                "Risk Category",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )

    render_ai_panel(
        title="AI subject insight",
        description="Generate a short subject-focused recommendation summary.",
        report_key=f"student_subject_ai_{register_number}",
        button_label="Generate subject analytics insight",
        generator=lambda: generate_subject_analytics_report(
            {
                "role": "Student",
                "scope": f"Subject analytics for {profile['student_name'].strip()}",
                "summary_points": [
                    f"Average GPA is {profile['avg_gp']:.2f}.",
                    f"Weak subject count is {profile['weak_count']}.",
                    f"High gap subject count is {profile['gap_count']}.",
                    f"Predicted risk subject count is {len(profile['risk_subjects'])}.",
                ],
                "priority_subjects": profile["risk_subjects"]["Course Name"].tolist(),
                "priority_students": [profile["student_name"].strip()],
            }
        ),
    )


def render_faculty_subject_analytics(context: dict[str, Any]) -> None:
    subject_meta = context.get("subject_meta")
    scope_df = context.get("scope_df", pd.DataFrame())

    render_page_header(
        "Subject Analytics",
        "Faculty Subject Risk Analytics",
        "Faculty subject analytics concentrate on the assigned course, the students at risk, and AI-backed next steps.",
    )

    if subject_meta is None or scope_df.empty:
        st.error("Faculty subject analytics are unavailable for this profile.")
        return

    high_risk_students = get_high_risk_students(scope_df)

    render_metric_row(
        [
            {"label": "Students", "value": str(scope_df["Register Number"].nunique()), "caption": "Learners in subject"},
            {"label": "Pass Rate", "value": f"{subject_meta['Pass Rate %']:.1f}%", "caption": "Historical success rate"},
            {"label": "Average Gap", "value": f"{subject_meta['Average Gap']:.1f}", "caption": "Internal-external gap"},
            {"label": "Weak Internals", "value": str(int(subject_meta['Weak Internal Students'])), "caption": "Below threshold internally"},
        ]
    )

    chart_col, table_col = st.columns([1.2, 1], gap="large")

    with chart_col:
        render_section_heading("Student score spread", "Performance distribution inside the assigned subject.")
        chart_data = scope_df[["Student Name", "Internal Mark", "External Mark"]].sort_values(
            ["Internal Mark", "External Mark"]
        )
        st.bar_chart(chart_data.set_index("Student Name"), use_container_width=True)

    with table_col:
        render_section_heading("Students needing intervention", "Failures, weak internals, and low prediction confidence.")
        if high_risk_students.empty:
            st.success("No high-risk students are currently flagged.")
        else:
            st.dataframe(
                high_risk_students[
                    [
                        "Register Number",
                        "Student Name",
                        "Internal Mark",
                        "External Mark",
                        "Pass Probability %",
                        "Risk Category",
                    ]
                ],
                use_container_width=True,
                hide_index=True,
            )

    render_ai_panel(
        title="AI subject insight",
        description="Generate a short intervention plan for this subject.",
        report_key=f"faculty_subject_ai_{subject_meta['Course Code']}",
        button_label="Generate subject analytics insight",
        generator=lambda: generate_subject_report(
            {
                "course_code": subject_meta["Course Code"],
                "course_name": subject_meta["Course Name"],
                "semester": int(subject_meta["Sem No"]),
                "pass_rate": round(float(subject_meta["Pass Rate %"]), 1),
                "fail_rate": round(float(subject_meta["Fail Rate %"]), 1),
                "avg_internal": round(float(subject_meta["Average Internal"]), 1),
                "avg_external": round(float(subject_meta["Average External"]), 1),
                "avg_gap": round(float(subject_meta["Average Gap"]), 1),
                "high_risk_students": high_risk_students["Student Name"].head(8).tolist(),
            }
        ),
    )


def render_mentor_subject_analytics(context: dict[str, Any]) -> None:
    scope_df = context.get("scope_df", pd.DataFrame())

    render_page_header(
        "Subject Analytics",
        "Mentor Cohort Subject Pressure",
        "This view surfaces the subjects that recur across mentee weakness and predicted risk so mentor effort can be focused.",
    )

    if scope_df.empty:
        st.error("Mentor subject analytics are unavailable for this profile.")
        return

    pressure_points = build_mentor_subject_pressure(scope_df)
    priority_table = build_student_priority_table(scope_df)

    render_metric_row(
        [
            {"label": "Tracked Subjects", "value": str(scope_df["Course Code"].nunique()), "caption": "Across mentees"},
            {"label": "Weak Subject Clusters", "value": str(len(pressure_points)), "caption": "Repeated risk hotspots"},
            {"label": "Average GPA", "value": f"{scope_df['gp'].mean():.2f}", "caption": "Cohort GPA"},
            {"label": "High-Risk Students", "value": str(int((priority_table['Risk Band'] == 'High').sum())), "caption": "Need mentor follow-up"},
        ]
    )

    chart_col, table_col = st.columns([1.15, 1], gap="large")

    with chart_col:
        render_section_heading("Repeated weak subjects", "Subjects that appear most often in weak or risky patterns.")
        chart_data = pressure_points.head(12).set_index("Course Name")["Students"]
        if chart_data.empty:
            st.info("No recurring subject pressure points were found.")
        else:
            st.bar_chart(chart_data, use_container_width=True)

    with table_col:
        render_section_heading("Priority students", "Students who should be contacted first.")
        st.dataframe(
            priority_table[
                [
                    "Register Number",
                    "Student Name",
                    "Average GP",
                    "Predicted Risk Subjects",
                    "Risk Score",
                    "Risk Band",
                ]
            ].head(10),
            use_container_width=True,
            hide_index=True,
        )

    render_section_heading("Subject pressure table", "Subject-level count of weak or risky mentee signals.")
    st.dataframe(pressure_points, use_container_width=True, hide_index=True)

    render_ai_panel(
        title="AI subject insight",
        description="Generate a mentor-oriented subject intervention summary.",
        report_key="mentor_subject_ai",
        button_label="Generate subject analytics insight",
        generator=lambda: generate_subject_analytics_report(
            {
                "role": "Mentor",
                "scope": "Mentee subject pressure summary",
                "summary_points": [
                    f"Mentee count is {priority_table['Register Number'].nunique()}.",
                    f"High-risk mentees: {int((priority_table['Risk Band'] == 'High').sum())}.",
                    f"Average GPA is {scope_df['gp'].mean():.2f}.",
                ],
                "priority_subjects": pressure_points["Course Name"].head(6).tolist(),
                "priority_students": priority_table["Student Name"].head(6).tolist(),
            }
        ),
    )


def render_hod_subject_analytics(context: dict[str, Any]) -> None:
    scope_df = context.get("scope_df", pd.DataFrame())
    department = context.get("department", "Department")

    render_page_header(
        "Subject Analytics",
        f"{department} Subject Analytics",
        "Department subject analytics highlight fail-rate hotspots, risk concentration, and semester-wise bottlenecks.",
    )

    if scope_df.empty:
        st.error("HOD subject analytics are unavailable for this profile.")
        return

    subject_stats = build_subject_summary(scope_df)
    heatmap = build_subject_heatmap(subject_stats)

    render_metric_row(
        [
            {"label": "Subjects", "value": str(subject_stats['Subject Label'].nunique()), "caption": "In department scope"},
            {"label": "High-Risk Subjects", "value": str(int((subject_stats['Risk Level'] == 'High').sum())), "caption": "Need action"},
            {"label": "Average Gap", "value": f"{scope_df['Internal-External Gap'].mean():.1f}", "caption": "Department gap"},
            {"label": "High-Risk Share", "value": f"{(scope_df['Pass Probability'] < LOW_PASS_PROBABILITY).mean() * 100:.1f}%", "caption": "Low-confidence records"},
        ]
    )

    heatmap_col, table_col = st.columns([1.25, 1], gap="large")

    with heatmap_col:
        render_section_heading("Failure heatmap", "Fail rate by semester and subject.")
        if heatmap.empty:
            st.info("Heatmap is unavailable for the current dataset.")
        else:
            st.dataframe(heatmap.style.format("{:.1f}%").background_gradient(cmap="Reds"), use_container_width=True)

    with table_col:
        render_section_heading("Highest-risk subjects", "Subjects ranked by fail rate and risk load.")
        st.dataframe(
            subject_stats[
                [
                    "Subject Label",
                    "Fail Rate %",
                    "High Risk Students",
                    "Average Gap",
                    "Risk Level",
                ]
            ].head(12),
            use_container_width=True,
            hide_index=True,
        )

    render_ai_panel(
        title="AI subject insight",
        description="Generate a short subject-analytics summary for departmental action.",
        report_key=f"hod_subject_ai_{department}",
        button_label="Generate subject analytics insight",
        generator=lambda: generate_subject_analytics_report(
            {
                "role": "HOD",
                "scope": f"Department subject analytics for {department}",
                "summary_points": [
                    f"Department pass rate is {scope_df['Result_Binary'].mean() * 100:.1f}%.",
                    f"Average GPA is {scope_df['gp'].mean():.2f}.",
                    f"High-risk subject count is {int((subject_stats['Risk Level'] == 'High').sum())}.",
                ],
                "priority_subjects": subject_stats["Course Name"].head(6).tolist(),
                "priority_students": [],
            }
        ),
    )


def render_principal_subject_analytics(
    enriched_df: pd.DataFrame,
    context: dict[str, Any],
) -> None:
    scope_df = context.get("scope_df", enriched_df)

    render_page_header(
        "Subject Analytics",
        "Institution Subject Analytics",
        "Executive subject analytics compare departments and identify the highest-concentration academic risk zones.",
    )

    if scope_df.empty:
        st.error("Principal subject analytics are unavailable.")
        return

    subject_stats = build_subject_summary(scope_df)
    department_summary = build_department_summary(scope_df)

    render_metric_row(
        [
            {"label": "Departments", "value": str(department_summary['Department'].nunique()), "caption": "Historical departments"},
            {"label": "Tracked Subjects", "value": str(subject_stats['Subject Label'].nunique()), "caption": "Across institution"},
            {"label": "Average GPA", "value": f"{scope_df['gp'].mean():.2f}", "caption": "Institution average"},
            {"label": "Risk Hotspots", "value": str(int((subject_stats['Risk Level'] == 'High').sum())), "caption": "Subjects with high risk"},
        ]
    )

    compare_col, table_col = st.columns([1.05, 1.15], gap="large")

    with compare_col:
        render_section_heading("Department summary", "Pass rate and GPA comparison by department.")
        st.dataframe(department_summary, use_container_width=True, hide_index=True)

    with table_col:
        render_section_heading("Top subject hotspots", "High-failure subjects requiring leadership attention.")
        st.dataframe(
            subject_stats[
                [
                    "Department",
                    "Subject Label",
                    "Fail Rate %",
                    "High Risk Students",
                    "Risk Level",
                ]
            ].head(12),
            use_container_width=True,
            hide_index=True,
        )

    render_ai_panel(
        title="AI subject insight",
        description="Generate an executive subject analytics summary.",
        report_key="principal_subject_ai",
        button_label="Generate subject analytics insight",
        generator=lambda: generate_subject_analytics_report(
            {
                "role": "Principal",
                "scope": "Institution subject analytics",
                "summary_points": [
                    f"Overall pass rate is {scope_df['Result_Binary'].mean() * 100:.1f}%.",
                    f"Average GPA is {scope_df['gp'].mean():.2f}.",
                    f"High-risk subject count is {int((subject_stats['Risk Level'] == 'High').sum())}.",
                ],
                "priority_subjects": subject_stats["Course Name"].head(6).tolist(),
                "priority_students": [],
            }
        ),
    )


def render_projection_workspace() -> None:
    render_page_header(
        "New Student Projection",
        "Academic Projection Workspace",
        "Upload a new admission dataset to run the existing projection models without changing the underlying ML pipeline.",
    )

    uploaded_file = st.file_uploader(
        "Upload new student dataset (Excel)",
        type=["xlsx"],
        key="projection_uploader",
    )

    uploaded_df: pd.DataFrame | None = None
    if uploaded_file is not None:
        try:
            uploaded_df = pd.read_excel(uploaded_file)
            uploaded_df.columns = uploaded_df.columns.str.strip()
        except Exception as error:
            st.error(f"Unable to read the uploaded Excel file: {error}")
            uploaded_df = None

    if uploaded_df is not None:
        missing_columns = find_missing_columns(uploaded_df, REQUIRED_PROJECTION_COLUMNS)
        if missing_columns:
            st.error(
                "The uploaded dataset is missing required columns: "
                + ", ".join(missing_columns)
            )
        else:
            render_section_heading("Uploaded dataset preview", "Minimal preview before prediction.")
            st.dataframe(uploaded_df, use_container_width=True, hide_index=True)

            if st.button("Generate academic projection", key="projection_generate_button", use_container_width=True):
                try:
                    from core.projection_predictor import predict_new_students

                    subject_template = pd.read_csv("models/subject_template.csv")
                    with st.spinner("Running projection models..."):
                        projected_df = predict_new_students(uploaded_df, subject_template)

                    st.session_state["projection_results"] = projected_df
                    st.session_state.pop("projection_ai_summary", None)
                except FileNotFoundError as error:
                    st.error(f"Projection model asset is missing: {error}")
                except Exception as error:
                    st.error(f"Projection failed: {error}")
    else:
        render_html_panel(
            "Projection ready",
            [
                "Upload an Excel dataset for new student projection.",
                "The workspace preserves the existing internal, external, GPA, and result prediction pipeline.",
                "AI projection summary can be generated after successful prediction.",
            ],
        )

    projected_df = st.session_state.get("projection_results")
    if not isinstance(projected_df, pd.DataFrame) or projected_df.empty:
        return

    render_metric_row(
        [
            {"label": "Projected Pass Rate", "value": f"{projected_df['Result_Binary'].mean() * 100:.1f}%", "caption": "Predicted cohort success"},
            {"label": "Average Internal", "value": f"{projected_df['Internal Mark'].mean():.1f}", "caption": "Projected internal mark"},
            {"label": "Average External", "value": f"{projected_df['External Mark'].mean():.1f}", "caption": "Projected external mark"},
            {"label": "Projected GPA", "value": f"{projected_df['gp'].mean():.2f}", "caption": "Predicted GPA"},
        ]
    )

    render_ai_panel(
        title="AI projection summary",
        description="Generate a short planning summary for the projected cohort.",
        report_key="projection_ai_summary",
        button_label="Generate AI projection summary",
        generator=lambda: generate_projection_summary(projected_df),
    )

    render_section_heading("Projected dataset", "Predicted output from the existing projection pipeline.")
    st.dataframe(projected_df, use_container_width=True, hide_index=True)

    st.download_button(
        "Download projected dataset",
        data=projected_df.to_csv(index=False).encode("utf-8"),
        file_name="projected_academic_results.csv",
        mime="text/csv",
        key="projection_download",
        use_container_width=True,
    )


def render_dataset_preview(
    enriched_df: pd.DataFrame,
    role: str,
    context: dict[str, Any],
) -> None:
    scope_df = context.get("scope_df", enriched_df).copy()

    render_page_header(
        "Dataset Preview",
        "Minimal Dataset Explorer",
        "A trimmed preview section with lightweight filters and role-aware data scope.",
    )

    if scope_df.empty:
        st.error("No data is available for dataset preview in this role scope.")
        return

    semesters = sorted(scope_df["Sem No"].astype(str).unique().tolist())
    selected_semesters = st.multiselect(
        "Semester filter",
        semesters,
        default=semesters,
        key=f"{role.lower()}_dataset_semesters",
    )
    search_text = st.text_input(
        "Search by student, subject, or register number",
        key=f"{role.lower()}_dataset_search",
    ).strip().lower()

    filtered_df = scope_df[scope_df["Sem No"].astype(str).isin(selected_semesters)].copy()
    if search_text:
        filtered_df = filtered_df[
            filtered_df["Student Name"].astype(str).str.lower().str.contains(search_text, regex=False)
            | filtered_df["Course Name"].astype(str).str.lower().str.contains(search_text, regex=False)
            | filtered_df["Course Code"].astype(str).str.lower().str.contains(search_text, regex=False)
            | filtered_df["Register Number"].astype(str).str.lower().str.contains(search_text, regex=False)
        ]

    render_metric_row(
        [
            {"label": "Records", "value": str(len(filtered_df)), "caption": "Filtered rows"},
            {"label": "Students", "value": str(filtered_df["Register Number"].nunique()), "caption": "Visible students"},
            {"label": "Subjects", "value": str(filtered_df["Course Code"].nunique()), "caption": "Visible subjects"},
            {"label": "Pass Rate", "value": f"{filtered_df['Result_Binary'].mean() * 100:.1f}%" if not filtered_df.empty else "0.0%", "caption": "Within current filters"},
        ]
    )

    preview_columns = [
        "Department",
        "Register Number",
        "Student Name",
        "Sem No",
        "Course Code",
        "Course Name",
        "Internal Mark",
        "External Mark",
        "gp",
        "Pass Probability %",
        "Risk Category",
    ]
    st.dataframe(filtered_df[preview_columns], use_container_width=True, hide_index=True)


@st.cache_data(show_spinner=False)
def enrich_dataset(df: pd.DataFrame) -> pd.DataFrame:
    missing_columns = find_missing_columns(df, REQUIRED_DATA_COLUMNS)
    if missing_columns:
        raise ValueError("Academic dataset is missing required columns: " + ", ".join(missing_columns))

    enriched_df = df.copy()
    enriched_df["Internal-External Gap"] = enriched_df["Internal-External Gap"].fillna(
        enriched_df["Internal Mark"] - enriched_df["External Mark"]
    )

    fallback_probabilities = (
        enriched_df["Result_Binary"].astype(float).clip(lower=0.0, upper=1.0)
    )
    fallback_predictions = fallback_probabilities.round().astype(int)

    enriched_df["Pass Probability"] = fallback_probabilities
    enriched_df["Predicted Result"] = fallback_predictions

    try:
        import core.predictor as predictor_module

        known_course_codes = set(map(str, predictor_module.encoder.classes_))
        valid_mask = enriched_df["Course Code"].astype(str).isin(known_course_codes)

        if valid_mask.any():
            feature_df = enriched_df.loc[
                valid_mask,
                [
                    "Sem No",
                    "Course Code",
                    "Internal Mark",
                    "Internal-External Gap",
                    "Credit Points",
                ],
            ].copy()
            feature_df["Course_Code_Enc"] = predictor_module.encoder.transform(
                feature_df["Course Code"].astype(str)
            )

            model_input = feature_df[
                [
                    "Sem No",
                    "Course_Code_Enc",
                    "Internal Mark",
                    "Internal-External Gap",
                    "Credit Points",
                ]
            ]
            enriched_df.loc[valid_mask, "Pass Probability"] = predictor_module.model.predict_proba(model_input)[:, 1]
            enriched_df.loc[valid_mask, "Predicted Result"] = predictor_module.model.predict(model_input)
    except Exception:
        pass

    enriched_df["Pass Probability %"] = (enriched_df["Pass Probability"] * 100).round(1)
    enriched_df["Weak Internal"] = enriched_df["Internal Mark"] < WEAK_MARK_THRESHOLD
    enriched_df["High Gap"] = enriched_df["Internal-External Gap"] > HIGH_GAP_THRESHOLD
    enriched_df["Failed"] = enriched_df["Result_Binary"] == 0
    enriched_df["Risk Category"] = enriched_df["Pass Probability"].apply(probability_to_band)
    return enriched_df


@st.cache_data(show_spinner=False)
def build_subject_summary(enriched_df: pd.DataFrame) -> pd.DataFrame:
    if enriched_df.empty:
        return pd.DataFrame(
            columns=[
                "Department",
                "Sem No",
                "Course Code",
                "Course Name",
                "Subject Label",
                "Students",
                "Pass Rate %",
                "Fail Rate %",
                "Average Internal",
                "Average External",
                "Average Gap",
                "Average GP",
                "High Risk Students",
                "Weak Internal Students",
                "Risk Level",
            ]
        )

    subject_stats = (
        enriched_df.groupby(["Department", "Sem No", "Course Code", "Course Name"], as_index=False)
        .agg(
            Students=("Register Number", "nunique"),
            Pass_Rate=("Result_Binary", "mean"),
            Average_Internal=("Internal Mark", "mean"),
            Average_External=("External Mark", "mean"),
            Average_Gap=("Internal-External Gap", "mean"),
            Average_GP=("gp", "mean"),
            High_Risk_Students=("Pass Probability", lambda values: int((values < LOW_PASS_PROBABILITY).sum())),
            Weak_Internal_Students=("Weak Internal", "sum"),
        )
        .sort_values(["Pass_Rate", "High_Risk_Students", "Average_Gap"], ascending=[True, False, False])
        .reset_index(drop=True)
    )

    subject_stats["Fail Rate"] = 1 - subject_stats["Pass_Rate"]
    subject_stats["Pass Rate %"] = (subject_stats["Pass_Rate"] * 100).round(1)
    subject_stats["Fail Rate %"] = (subject_stats["Fail Rate"] * 100).round(1)
    subject_stats["Average Internal"] = subject_stats["Average_Internal"].round(1)
    subject_stats["Average External"] = subject_stats["Average_External"].round(1)
    subject_stats["Average Gap"] = subject_stats["Average_Gap"].round(1)
    subject_stats["Average GP"] = subject_stats["Average_GP"].round(2)
    subject_stats["High Risk Students"] = subject_stats["High_Risk_Students"].astype(int)
    subject_stats["Weak Internal Students"] = subject_stats["Weak_Internal_Students"].astype(int)
    subject_stats["Risk Level"] = subject_stats["Pass_Rate"].apply(pass_rate_to_level)
    subject_stats["Subject Label"] = (
        subject_stats["Course Code"].astype(str) + " | " + subject_stats["Course Name"].astype(str)
    )

    return subject_stats[
        [
            "Department",
            "Sem No",
            "Course Code",
            "Course Name",
            "Subject Label",
            "Students",
            "Pass Rate %",
            "Fail Rate %",
            "Average Internal",
            "Average External",
            "Average Gap",
            "Average GP",
            "High Risk Students",
            "Weak Internal Students",
            "Risk Level",
        ]
    ]


@st.cache_data(show_spinner=False)
def build_semester_summary(enriched_df: pd.DataFrame) -> pd.DataFrame:
    if enriched_df.empty:
        return pd.DataFrame(
            columns=[
                "Sem No",
                "Students",
                "Pass Rate %",
                "Average GP",
                "Average Internal",
                "Average External",
                "Average Gap",
            ]
        )

    semester_summary = (
        enriched_df.groupby("Sem No", as_index=False)
        .agg(
            Students=("Register Number", "nunique"),
            Pass_Rate=("Result_Binary", "mean"),
            Average_GP=("gp", "mean"),
            Average_Internal=("Internal Mark", "mean"),
            Average_External=("External Mark", "mean"),
            Average_Gap=("Internal-External Gap", "mean"),
        )
        .sort_values("Sem No")
        .reset_index(drop=True)
    )

    semester_summary["Pass Rate %"] = (semester_summary["Pass_Rate"] * 100).round(1)
    semester_summary["Average GP"] = semester_summary["Average_GP"].round(2)
    semester_summary["Average Internal"] = semester_summary["Average_Internal"].round(1)
    semester_summary["Average External"] = semester_summary["Average_External"].round(1)
    semester_summary["Average Gap"] = semester_summary["Average_Gap"].round(1)

    return semester_summary[
        [
            "Sem No",
            "Students",
            "Pass Rate %",
            "Average GP",
            "Average Internal",
            "Average External",
            "Average Gap",
        ]
    ]


@st.cache_data(show_spinner=False)
def build_department_summary(enriched_df: pd.DataFrame) -> pd.DataFrame:
    if enriched_df.empty:
        return pd.DataFrame(
            columns=[
                "Department",
                "Students",
                "Pass Rate %",
                "Average GP",
                "Average Internal",
                "Average External",
                "High-Risk Share %",
            ]
        )

    summary = (
        enriched_df.groupby("Department", as_index=False)
        .agg(
            Students=("Register Number", "nunique"),
            Pass_Rate=("Result_Binary", "mean"),
            Average_GP=("gp", "mean"),
            Average_Internal=("Internal Mark", "mean"),
            Average_External=("External Mark", "mean"),
            High_Risk_Share=("Pass Probability", lambda values: float((values < LOW_PASS_PROBABILITY).mean())),
        )
        .sort_values(["Pass_Rate", "Average_GP"], ascending=[False, False])
        .reset_index(drop=True)
    )

    summary["Pass Rate %"] = (summary["Pass_Rate"] * 100).round(1)
    summary["Average GP"] = summary["Average_GP"].round(2)
    summary["Average Internal"] = summary["Average_Internal"].round(1)
    summary["Average External"] = summary["Average_External"].round(1)
    summary["High-Risk Share %"] = (summary["High_Risk_Share"] * 100).round(1)

    return summary[
        [
            "Department",
            "Students",
            "Pass Rate %",
            "Average GP",
            "Average Internal",
            "Average External",
            "High-Risk Share %",
        ]
    ]


def build_projected_department_summary(projected_df: Any) -> pd.DataFrame:
    if not isinstance(projected_df, pd.DataFrame) or projected_df.empty or "Department" not in projected_df.columns:
        return pd.DataFrame(columns=["Department", "Projected Pass Rate %", "Projected GPA"])

    summary = (
        projected_df.groupby("Department", as_index=False)
        .agg(
            Projected_Pass_Rate=("Result_Binary", "mean"),
            Projected_GPA=("gp", "mean"),
        )
        .reset_index(drop=True)
    )
    summary["Projected Pass Rate %"] = (summary["Projected_Pass_Rate"] * 100).round(1)
    summary["Projected GPA"] = summary["Projected_GPA"].round(2)
    return summary[["Department", "Projected Pass Rate %", "Projected GPA"]]


def merge_department_comparison(
    department_summary: pd.DataFrame,
    projected_department_summary: pd.DataFrame,
) -> pd.DataFrame:
    if department_summary.empty and projected_department_summary.empty:
        return pd.DataFrame()
    if department_summary.empty:
        return projected_department_summary.copy()

    return department_summary.merge(
        projected_department_summary,
        on="Department",
        how="left",
    )


@st.cache_data(show_spinner=False)
def build_student_priority_table(enriched_df: pd.DataFrame) -> pd.DataFrame:
    if enriched_df.empty:
        return pd.DataFrame(
            columns=[
                "Register Number",
                "Student Name",
                "Average GP",
                "Pass Rate %",
                "Weak Subjects",
                "High Gap Subjects",
                "Predicted Risk Subjects",
                "Risk Score",
                "Risk Band",
            ]
        )

    priority_table = (
        enriched_df.groupby(["Register Number", "Student Name"], as_index=False)
        .agg(
            Average_GP=("gp", "mean"),
            Pass_Rate=("Result_Binary", "mean"),
            Weak_Subjects=("Weak Internal", "sum"),
            High_Gap_Subjects=("High Gap", "sum"),
            Failed_Subjects=("Failed", "sum"),
            Predicted_Risk_Subjects=("Pass Probability", lambda values: int((values < LOW_PASS_PROBABILITY).sum())),
        )
        .reset_index(drop=True)
    )

    priority_table["Average GP"] = priority_table["Average_GP"].round(2)
    priority_table["Pass Rate %"] = (priority_table["Pass_Rate"] * 100).round(1)
    priority_table["Weak Subjects"] = priority_table["Weak_Subjects"].astype(int)
    priority_table["High Gap Subjects"] = priority_table["High_Gap_Subjects"].astype(int)
    priority_table["Predicted Risk Subjects"] = priority_table["Predicted_Risk_Subjects"].astype(int)
    priority_table["Risk Score"] = (
        priority_table["Failed_Subjects"] * 35
        + priority_table["Weak_Subjects"] * 16
        + priority_table["High_Gap_Subjects"] * 10
        + priority_table["Predicted_Risk_Subjects"] * 18
        + (100 - priority_table["Pass Rate %"]) * 0.35
    ).round(1)
    priority_table["Risk Band"] = priority_table["Risk Score"].apply(score_to_band)

    return priority_table[
        [
            "Register Number",
            "Student Name",
            "Average GP",
            "Pass Rate %",
            "Weak Subjects",
            "High Gap Subjects",
            "Predicted Risk Subjects",
            "Risk Score",
            "Risk Band",
        ]
    ].sort_values(["Risk Score", "Pass Rate %", "Average GP"], ascending=[False, True, True])


@st.cache_data(show_spinner=False)
def build_subject_heatmap(subject_stats: pd.DataFrame) -> pd.DataFrame:
    if subject_stats.empty:
        return pd.DataFrame()

    heatmap = subject_stats.pivot_table(
        index="Sem No",
        columns="Course Name",
        values="Fail Rate %",
        aggfunc="mean",
        fill_value=0,
    )
    return heatmap.sort_index(axis=0).sort_index(axis=1)


def build_student_profile(enriched_df: pd.DataFrame, reg_no: str | None) -> dict[str, Any] | None:
    if reg_no is None:
        return None

    summary = student_summary(enriched_df, reg_no)
    if summary is None:
        return None

    student_df = enriched_df[
        enriched_df["Register Number"].astype(str) == str(reg_no)
    ].copy().sort_values(["Sem No", "Course Name"])

    risk_subjects = (
        student_df[student_df["Pass Probability"] < LOW_PASS_PROBABILITY][
            ["Course Code", "Course Name", "Pass Probability %", "Internal Mark", "External Mark"]
        ]
        .sort_values(["Pass Probability %", "Internal Mark"])
        .reset_index(drop=True)
    )

    semester_trend = (
        student_df.groupby("Sem No", as_index=False)
        .agg(
            Average_Internal=("Internal Mark", "mean"),
            Average_External=("External Mark", "mean"),
            Average_GP=("gp", "mean"),
            Pass_Rate=("Result_Binary", "mean"),
        )
        .sort_values("Sem No")
        .reset_index(drop=True)
    )
    semester_trend["Pass Rate %"] = (semester_trend["Pass_Rate"] * 100).round(1)
    semester_trend["Average Internal"] = semester_trend["Average_Internal"].round(1)
    semester_trend["Average External"] = semester_trend["Average_External"].round(1)
    semester_trend["Average GP"] = semester_trend["Average_GP"].round(2)

    weak_count = len(summary["weak_subjects"])
    gap_count = len(summary["gap_subjects"])
    fail_count = int((student_df["Result_Binary"] == 0).sum())
    predicted_risk_count = len(risk_subjects)
    risk_score = round(
        fail_count * 30
        + weak_count * 14
        + gap_count * 10
        + predicted_risk_count * 18,
        1,
    )

    return {
        "summary": summary,
        "student_name": summary["student_name"],
        "avg_internal": summary["avg_internal"],
        "avg_external": summary["avg_external"],
        "avg_gp": summary["avg_gp"],
        "weak_subjects": summary["weak_subjects"].reset_index(drop=True),
        "gap_subjects": summary["gap_subjects"].reset_index(drop=True),
        "raw": student_df.reset_index(drop=True),
        "risk_subjects": risk_subjects,
        "semester_trend": semester_trend,
        "pass_rate": round(float(student_df["Result_Binary"].mean() * 100), 1),
        "credits": float(student_df["Credit Points"].sum()),
        "risk_score": risk_score,
        "risk_band": score_to_band(risk_score),
        "weak_count": weak_count,
        "gap_count": gap_count,
        "fail_count": fail_count,
    }


def calculate_health_score(enriched_df: pd.DataFrame) -> float:
    if enriched_df.empty:
        return 0.0

    pass_rate = safe_float(enriched_df["Result_Binary"].mean(), 0.0)
    avg_gap = safe_float(enriched_df["Internal-External Gap"].mean(), 0.0)
    high_risk_share = safe_float((enriched_df["Pass Probability"] < LOW_PASS_PROBABILITY).mean(), 0.0)

    score = 100 - ((1 - pass_rate) * 65) - (avg_gap * 0.65) - (high_risk_share * 35)
    return round(max(0.0, min(100.0, score)), 1)


def get_role_context(
    enriched_df: pd.DataFrame,
    role: str,
    profile: dict[str, Any],
) -> dict[str, Any]:
    context = dict(profile or {})

    if role == "Student":
        register_number = resolve_student_register_number(enriched_df, context.get("register_number"))
        scope_df = filter_by_register_number(enriched_df, register_number)
        student_name = scope_df["Student Name"].iloc[0].strip() if not scope_df.empty else "Student"
        context.update(
            {
                "register_number": register_number,
                "student_name": student_name,
                "scope_df": scope_df,
            }
        )
        return context

    if role == "Faculty":
        subject_stats = build_subject_summary(enriched_df)
        subject_meta = resolve_subject_meta(subject_stats, context.get("course_code"))
        if subject_meta is None:
            context["scope_df"] = pd.DataFrame()
            context["subject_meta"] = None
            return context

        scope_df = enriched_df[
            (enriched_df["Course Code"].astype(str) == str(subject_meta["Course Code"]))
            & (enriched_df["Course Name"].astype(str) == str(subject_meta["Course Name"]))
        ].copy()
        context.update(
            {
                "course_code": str(subject_meta["Course Code"]),
                "course_name": str(subject_meta["Course Name"]),
                "subject_meta": subject_meta,
                "scope_df": scope_df,
            }
        )
        return context

    if role == "Mentor":
        mentee_ids = resolve_mentee_ids(enriched_df, context.get("mentee_ids", []))
        scope_df = enriched_df[enriched_df["Register Number"].astype(str).isin(mentee_ids)].copy()
        context.update(
            {
                "mentee_ids": mentee_ids,
                "scope_df": scope_df,
            }
        )
        return context

    if role == "HOD":
        department = resolve_department(enriched_df, context.get("department"))
        scope_df = enriched_df[enriched_df["Department"].astype(str) == str(department)].copy()
        context.update(
            {
                "department": department,
                "scope_df": scope_df,
            }
        )
        return context

    context["scope_df"] = enriched_df.copy()
    return context


def resolve_student_register_number(enriched_df: pd.DataFrame, configured_register: Any) -> str | None:
    available = sorted(enriched_df["Register Number"].astype(str).unique().tolist())
    if not available:
        return None

    configured_value = str(configured_register).strip() if configured_register is not None else ""
    return configured_value if configured_value in available else available[0]


def resolve_subject_meta(
    subject_stats: pd.DataFrame,
    configured_course_code: Any,
) -> pd.Series | None:
    if subject_stats.empty:
        return None

    if configured_course_code is not None:
        matches = subject_stats[
            subject_stats["Course Code"].astype(str) == str(configured_course_code).strip()
        ]
        if not matches.empty:
            return matches.iloc[0]

    return subject_stats.iloc[0]


def resolve_mentee_ids(enriched_df: pd.DataFrame, configured_ids: Iterable[Any]) -> list[str]:
    available = set(enriched_df["Register Number"].astype(str).unique().tolist())
    configured = [str(value).strip() for value in configured_ids if str(value).strip() in available]
    if configured:
        return configured
    return sorted(available)[:6]


def resolve_department(enriched_df: pd.DataFrame, configured_department: Any) -> str:
    available = enriched_df["Department"].dropna().astype(str).unique().tolist()
    if configured_department is not None and str(configured_department).strip() in available:
        return str(configured_department).strip()
    return available[0] if available else "Department"


def filter_by_register_number(enriched_df: pd.DataFrame, register_number: str | None) -> pd.DataFrame:
    if register_number is None:
        return enriched_df.iloc[0:0].copy()
    return enriched_df[enriched_df["Register Number"].astype(str) == str(register_number)].copy()


def get_high_risk_students(subject_df: pd.DataFrame) -> pd.DataFrame:
    if subject_df.empty:
        return subject_df

    return subject_df[
        (subject_df["Pass Probability"] < LOW_PASS_PROBABILITY)
        | (subject_df["Result_Binary"] == 0)
        | (subject_df["Internal Mark"] < WEAK_MARK_THRESHOLD)
    ].sort_values(["Pass Probability", "Internal Mark"])


def build_mentor_subject_pressure(scope_df: pd.DataFrame) -> pd.DataFrame:
    if scope_df.empty:
        return pd.DataFrame(columns=["Course Code", "Course Name", "Students"])

    return (
        scope_df[
            scope_df["Weak Internal"] | (scope_df["Pass Probability"] < LOW_PASS_PROBABILITY)
        ]
        .groupby(["Course Code", "Course Name"], as_index=False)
        .agg(Students=("Register Number", "nunique"))
        .sort_values(["Students", "Course Name"], ascending=[False, True])
        .reset_index(drop=True)
    )


def build_scope_label(role: str, context: dict[str, Any]) -> str:
    if role == "Student":
        student_name = str(context.get("student_name", "Student")).strip()
        register_number = context.get("register_number", "")
        return f"{student_name} | {register_number}"

    if role == "Faculty":
        course_code = context.get("course_code", "")
        course_name = context.get("course_name", "Assigned subject")
        return f"{course_code} | {course_name}"

    if role == "Mentor":
        mentee_ids = context.get("mentee_ids", [])
        return f"{len(mentee_ids)} assigned mentees"

    if role == "HOD":
        return str(context.get("department", "Department"))

    return "Institution-wide access"


def find_missing_columns(df: pd.DataFrame, required_columns: Iterable[str]) -> list[str]:
    return [column for column in required_columns if column not in df.columns]


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if pd.isna(value):
            return default
        return float(value)
    except Exception:
        return default


def probability_to_band(probability: float) -> str:
    if probability < LOW_PASS_PROBABILITY:
        return "High"
    if probability < 0.80:
        return "Moderate"
    return "Low"


def pass_rate_to_level(pass_rate: float) -> str:
    if pass_rate >= 0.90:
        return "Low"
    if pass_rate >= 0.75:
        return "Moderate"
    return "High"


def score_to_band(score: float) -> str:
    if score >= 55:
        return "High"
    if score >= 25:
        return "Moderate"
    return "Low"
