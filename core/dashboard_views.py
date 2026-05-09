from __future__ import annotations

import base64
from html import escape
from pathlib import Path
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

FACULTY_USERS: dict[str, dict[str, Any]] = {
    "faculty_aero_1": {
        "password": "123",
        "department": "AERONAUTICAL",
        "subjects": [
            "Engineering Mechanics",
            "Materials Science for Aeronautical Engineering",
        ],
    },
    "faculty_ece_1": {
        "password": "123",
        "department": "ECE",
        "subjects": [
            "Digital Electronics",
            "Signals and Systems",
        ],
    },
    "faculty_cse_1": {
        "password": "123",
        "department": "CSE",
        "subjects": [
            "Data Structures",
            "DBMS",
        ],
    },
}

MENTOR_USERS: dict[str, dict[str, Any]] = {
    "mentor_aero_1": {
        "password": "123",
        "department": "AERONAUTICAL",
        "mentees": [
            "24BAE001",
            "24BAE002",
            "24BAE003",
            "24BAE004",
            "24BAE005",
            "24BAE006",
        ],
    }
}

HOD_USERS: dict[str, dict[str, Any]] = {
    "hod_aero": {
        "password": "123",
        "department": "AERONAUTICAL",
    },
    "hod_ece": {
        "password": "123",
        "department": "ECE",
    },
    "hod_cse": {
        "password": "123",
        "department": "CSE",
    },
    "hod_mech": {
        "password": "123",
        "department": "MECH",
    },
    "hod_civil": {
        "password": "123",
        "department": "CIVIL",
    },
}

PRINCIPAL_USERS: dict[str, dict[str, Any]] = {
    "principal1": {
        "password": "123",
    }
}

ROLE_USERS: dict[str, dict[str, dict[str, Any]]] = {
    "Faculty": FACULTY_USERS,
    "Mentor": MENTOR_USERS,
    "HOD": HOD_USERS,
    "Principal": PRINCIPAL_USERS,
}

ROLE_OPTIONS = ["Student", "Faculty", "Mentor", "HOD", "Principal"]

ROLE_SECTIONS: dict[str, list[str]] = {
    "Student": ["Dashboard", "Subject Analytics"],
    "Faculty": ["Dashboard", "Subject Analytics"],
    "Mentor": ["Dashboard", "Subject Analytics"],
    "HOD": ["Dashboard", "Subject Analytics", "Dataset Preview"],
    "Principal": ["Dashboard", "Subject Analytics", "New Student Projection", "Dataset Preview"],
}

DEPARTMENT_LABELS = {
    "AERONAUTICAL": "Aeronautical Engineering",
    "ECE": "ECE",
    "CSE": "CSE",
    "MECH": "MECH",
    "CIVIL": "CIVIL",
}

DEPARTMENT_ALIASES = {
    "AERONAUTICAL": {"AERONAUTICAL", "AERONAUTICAL ENGINEERING", "AERO"},
    "ECE": {"ECE", "ELECTRONICS AND COMMUNICATION", "ELECTRONICS AND COMMUNICATION ENGINEERING"},
    "CSE": {"CSE", "COMPUTER SCIENCE", "COMPUTER SCIENCE ENGINEERING"},
    "MECH": {"MECH", "MECHANICAL", "MECHANICAL ENGINEERING"},
    "CIVIL": {"CIVIL", "CIVIL ENGINEERING"},
}

ACADEMIC_FEEDBACK_PATH = "data/academic_feedback.csv"
CAREER_FEEDBACK_PATH = "data/career_support.csv"
ASSET_DIR = Path(__file__).resolve().parent.parent / "assets"
LOGIN_BACKGROUND_PATH = ASSET_DIR / "login_bg.png"
DASHBOARD_BACKGROUND_PATH = ASSET_DIR / "dashboard_bg.png"

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


@st.cache_data(show_spinner=False)
def load_image_data_uri(path: str) -> str:
    image_path = Path(path)
    if not image_path.exists():
        return ""

    encoded = base64.b64encode(image_path.read_bytes()).decode("ascii")
    suffix = image_path.suffix.lower().lstrip(".") or "png"
    return f"data:image/{suffix};base64,{encoded}"


def apply_login_background() -> None:
    image_uri = load_image_data_uri(str(LOGIN_BACKGROUND_PATH))
    if not image_uri:
        return

    st.markdown(
        f"""
        <style>
        .stApp {{
            position: relative;
            background: #07111d !important;
            overflow-x: hidden;
        }}

        .stApp::before {{
            content: "";
            position: fixed;
            inset: 0;
            background-image:
                linear-gradient(135deg, rgba(4, 11, 22, 0.74) 0%, rgba(9, 22, 35, 0.58) 46%, rgba(12, 31, 38, 0.54) 100%),
                url("{image_uri}");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            filter: blur(1.4px) brightness(0.84) saturate(0.98);
            opacity: 0.98;
            transform: scale(1.015);
            pointer-events: none;
            z-index: 0;
        }}

        .stApp::after {{
            content: "";
            position: fixed;
            inset: 0;
            background:
                radial-gradient(circle at 16% 18%, rgba(255, 255, 255, 0.16), transparent 24%),
                radial-gradient(circle at 82% 12%, rgba(47, 143, 104, 0.2), transparent 28%),
                linear-gradient(180deg, rgba(5, 12, 24, 0.18), rgba(5, 12, 24, 0.42));
            pointer-events: none;
            z-index: 0;
        }}

        [data-testid="stAppViewContainer"],
        [data-testid="stSidebar"],
        header[data-testid="stHeader"] {{
            position: relative;
            z-index: 1;
        }}

        header[data-testid="stHeader"] {{
            background: transparent;
        }}

        .block-container {{
            padding-top: 2.6rem;
        }}

        .login-shell {{
            background:
                linear-gradient(145deg, rgba(255, 255, 255, 0.82), rgba(235, 244, 246, 0.68));
            border: 1px solid rgba(255, 255, 255, 0.34);
            box-shadow:
                0 32px 80px rgba(0, 0, 0, 0.34),
                0 2px 0 rgba(255, 255, 255, 0.58) inset,
                0 -18px 34px rgba(14, 54, 70, 0.1) inset;
            backdrop-filter: blur(20px);
        }}

        .login-brand {{
            background:
                linear-gradient(145deg, rgba(8, 22, 37, 0.84), rgba(24, 98, 128, 0.74) 58%, rgba(41, 118, 86, 0.76));
            border-color: rgba(255, 255, 255, 0.26);
            box-shadow:
                0 36px 90px rgba(0, 0, 0, 0.38),
                0 2px 0 rgba(255, 255, 255, 0.2) inset;
        }}

        .login-access {{
            background:
                linear-gradient(145deg, rgba(255, 255, 255, 0.9), rgba(238, 246, 247, 0.78));
            border-top-color: rgba(30, 111, 143, 0.82);
        }}

        div[data-testid="stForm"] {{
            background:
                linear-gradient(145deg, rgba(255, 255, 255, 0.94), rgba(241, 247, 248, 0.86));
            border: 1px solid rgba(255, 255, 255, 0.42);
            box-shadow:
                0 30px 72px rgba(0, 0, 0, 0.28),
                0 2px 0 rgba(255, 255, 255, 0.82) inset;
            backdrop-filter: blur(18px);
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def apply_intro_background() -> None:
    image_uri = load_image_data_uri(str(LOGIN_BACKGROUND_PATH))
    if not image_uri:
        return

    st.markdown(
        f"""
        <style>
        .stApp {{
            position: relative;
            background: #07111d !important;
            overflow-x: hidden;
        }}

        .stApp::before {{
            content: "";
            position: fixed;
            inset: 0;
            background-image:
                linear-gradient(180deg, rgba(4, 11, 22, 0.18) 0%, rgba(4, 11, 22, 0.18) 48%, rgba(4, 11, 22, 0.5) 100%),
                url("{image_uri}");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            filter: brightness(0.9) saturate(1.02);
            pointer-events: none;
            z-index: 0;
        }}

        .stApp::after {{
            content: "";
            position: fixed;
            inset: 0;
            background:
                linear-gradient(90deg, rgba(5, 12, 24, 0.52) 0%, rgba(5, 12, 24, 0.18) 44%, rgba(5, 12, 24, 0.2) 100%);
            pointer-events: none;
            z-index: 0;
        }}

        [data-testid="stAppViewContainer"],
        header[data-testid="stHeader"] {{
            position: relative;
            z-index: 1;
        }}

        header[data-testid="stHeader"] {{
            background: transparent;
        }}

        .block-container {{
            max-width: 1180px;
            padding-top: 17vh;
            padding-bottom: 4rem;
        }}

        .intro-cover {{
            min-height: 68vh;
            display: flex;
            flex-direction: column;
            justify-content: flex-end;
            align-items: flex-start;
        }}

        .intro-copy {{
            max-width: 720px;
            color: #ffffff;
            text-shadow: 0 14px 32px rgba(0, 0, 0, 0.36);
        }}

        .intro-kicker {{
            display: inline-flex;
            align-items: center;
            padding: 0.38rem 0.82rem;
            border-radius: 999px;
            background: rgba(255, 255, 255, 0.16);
            border: 1px solid rgba(255, 255, 255, 0.26);
            color: #f2fbff;
            font-size: 0.78rem;
            font-weight: 850;
            text-transform: uppercase;
            letter-spacing: 0;
            backdrop-filter: blur(12px);
        }}

        .intro-title {{
            margin: 1rem 0 0.65rem 0;
            font-size: clamp(2.2rem, 5vw, 4.8rem);
            line-height: 1;
            font-weight: 880;
        }}

        .intro-subtitle {{
            max-width: 610px;
            margin: 0;
            color: rgba(244, 250, 252, 0.9);
            font-size: clamp(1rem, 1.5vw, 1.24rem);
            line-height: 1.6;
        }}

        .intro-prompt {{
            margin-top: 1.35rem;
            color: rgba(244, 250, 252, 0.84);
            font-size: 0.92rem;
            font-weight: 720;
        }}

        div[data-testid="stButton"] > button {{
            width: 220px;
            min-height: 3.1rem;
            margin-top: 1.1rem;
            border-radius: 999px;
            border: 1px solid rgba(255, 255, 255, 0.36);
            background:
                linear-gradient(145deg, rgba(255, 255, 255, 0.98), rgba(221, 240, 245, 0.9));
            color: #102438;
            font-weight: 850;
            box-shadow:
                0 24px 50px rgba(0, 0, 0, 0.28),
                0 2px 0 rgba(255, 255, 255, 0.95) inset;
            transition: transform 160ms ease, box-shadow 160ms ease;
        }}

        div[data-testid="stButton"] > button:hover {{
            transform: translateY(-2px);
            box-shadow:
                0 30px 64px rgba(0, 0, 0, 0.34),
                0 2px 0 rgba(255, 255, 255, 0.95) inset;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def apply_dashboard_background() -> None:
    image_uri = load_image_data_uri(str(DASHBOARD_BACKGROUND_PATH))
    if not image_uri:
        return

    st.markdown(
        f"""
        <style>
        .stApp {{
            position: relative;
            overflow-x: hidden;
        }}

        .stApp::after {{
            content: "";
            position: fixed;
            top: 1.5rem;
            right: -7vw;
            width: min(860px, 62vw);
            height: min(700px, 74vh);
            background-image: url("{image_uri}");
            background-size: contain;
            background-position: top right;
            background-repeat: no-repeat;
            opacity: 0.078;
            filter: grayscale(4%) saturate(0.98);
            pointer-events: none;
            z-index: 0;
        }}

        [data-testid="stAppViewContainer"],
        [data-testid="stSidebar"],
        header[data-testid="stHeader"] {{
            position: relative;
            z-index: 1;
        }}

        header[data-testid="stHeader"] {{
            background: rgba(245, 247, 251, 0.78);
            backdrop-filter: blur(10px);
        }}

        .hero-panel,
        .panel,
        .feedback-section,
        div[data-testid="stMetric"],
        div[data-testid="stDataFrame"] {{
            position: relative;
            z-index: 2;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def apply_theme() -> None:
    st.markdown(
        """
        <style>
        :root {
            --bg: #f5f7fb;
            --card: rgba(255, 255, 255, 0.84);
            --card-strong: rgba(255, 255, 255, 0.94);
            --border: rgba(35, 55, 85, 0.14);
            --text: #162033;
            --muted: #607089;
            --accent: #1e6f8f;
            --accent-2: #5b7c3b;
            --accent-3: #a46a1f;
            --accent-soft: rgba(30, 111, 143, 0.1);
            --success: #2f8f68;
            --shadow: 0 18px 42px rgba(36, 51, 77, 0.14);
            --shadow-soft: 0 8px 24px rgba(36, 51, 77, 0.1);
        }

        .stApp {
            background:
                linear-gradient(135deg, rgba(218, 229, 235, 0.98) 0%, rgba(250, 247, 240, 0.96) 44%, rgba(228, 238, 229, 0.98) 100%);
            background-color: #e8eef1;
            color: var(--text);
            font-family: "Inter", "Segoe UI", "Trebuchet MS", sans-serif;
        }

        .block-container {
            padding-top: 1.3rem;
            padding-bottom: 2.2rem;
            max-width: 1440px;
        }

        [data-testid="stSidebar"] {
            background:
                linear-gradient(180deg, rgba(255, 255, 255, 0.96) 0%, rgba(239, 246, 244, 0.94) 100%);
            border-right: 1px solid var(--border);
            box-shadow: 12px 0 30px rgba(36, 51, 77, 0.08);
        }

        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] div {
            color: var(--text);
        }

        h1, h2, h3, h4 {
            color: var(--text);
            letter-spacing: 0;
        }

        p, li, label, span {
            letter-spacing: 0;
        }

        div[data-baseweb="select"] > div,
        div[data-baseweb="input"] > div,
        div[data-testid="stTextInput"] input,
        div[data-testid="stNumberInput"] input {
            background: rgba(255, 255, 255, 0.98);
            color: var(--text);
            border: 1px solid rgba(22, 32, 51, 0.18);
            border-radius: 12px;
            box-shadow:
                inset 0 1px 0 rgba(255, 255, 255, 0.9),
                0 8px 18px rgba(36, 51, 77, 0.08);
        }

        div[data-baseweb="select"] > div:focus-within,
        div[data-testid="stTextInput"] input:focus,
        div[data-testid="stNumberInput"] input:focus {
            border-color: rgba(30, 111, 143, 0.46);
            box-shadow:
                0 0 0 3px rgba(30, 111, 143, 0.12),
                0 10px 22px rgba(36, 51, 77, 0.1);
        }

        div[data-testid="stFileUploader"] {
            background: rgba(255, 255, 255, 0.76);
            border: 1px dashed rgba(30, 111, 143, 0.34);
            border-radius: 14px;
            padding: 0.6rem;
        }

        div[data-testid="stMetric"] {
            background:
                linear-gradient(145deg, rgba(255, 255, 255, 0.96), rgba(246, 250, 248, 0.9));
            border: 1px solid var(--border);
            border-radius: 14px;
            padding: 0.85rem 0.95rem;
            box-shadow: var(--shadow-soft);
            transition: transform 160ms ease, box-shadow 160ms ease, border-color 160ms ease;
        }

        div[data-testid="stMetric"]:hover {
            border-color: rgba(30, 111, 143, 0.28);
            box-shadow: var(--shadow);
            transform: translateY(-2px);
        }

        div[data-testid="stMetricLabel"] {
            color: var(--muted);
            font-weight: 750;
        }

        div[data-testid="stMetricValue"] {
            color: var(--text);
        }

        div[data-testid="stDataFrame"] {
            border: 1px solid var(--border);
            border-radius: 14px;
            overflow: hidden;
            background: rgba(255, 255, 255, 0.86);
            box-shadow: var(--shadow-soft);
        }

        button[kind="primary"] {
            background: linear-gradient(135deg, #1e6f8f 0%, #2f8f68 100%);
            border: none;
            color: #ffffff;
            border-radius: 12px;
            box-shadow: 0 10px 22px rgba(30, 111, 143, 0.2);
        }

        button[kind="secondary"] {
            background: rgba(255, 255, 255, 0.9);
            border: 1px solid var(--border);
            color: var(--text);
            border-radius: 12px;
            transition: transform 140ms ease, border-color 140ms ease, box-shadow 140ms ease;
        }

        button[kind="secondary"]:hover {
            border-color: rgba(30, 111, 143, 0.32);
            box-shadow: 0 8px 20px rgba(36, 51, 77, 0.12);
            transform: translateY(-1px);
        }

        .hero-panel {
            background:
                linear-gradient(135deg, rgba(255, 255, 255, 0.96) 0%, rgba(239, 247, 247, 0.88) 58%, rgba(250, 245, 235, 0.86) 100%);
            border: 1px solid var(--border);
            border-radius: 18px;
            padding: 1.35rem 1.5rem;
            box-shadow: var(--shadow);
            margin-bottom: 1rem;
            backdrop-filter: blur(14px);
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
            letter-spacing: 0;
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
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 1rem 1.05rem;
            box-shadow: var(--shadow-soft);
            margin-bottom: 1rem;
            backdrop-filter: blur(14px);
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
            background: rgba(47, 143, 104, 0.12);
            color: var(--success);
            font-size: 0.82rem;
            font-weight: 700;
        }

        .login-shell {
            background:
                linear-gradient(145deg, rgba(255, 255, 255, 0.98), rgba(236, 244, 245, 0.94));
            border: 1px solid rgba(22, 32, 51, 0.12);
            border-radius: 20px;
            padding: 1.25rem;
            box-shadow:
                0 28px 60px rgba(36, 51, 77, 0.18),
                0 2px 0 rgba(255, 255, 255, 0.92) inset,
                0 -16px 32px rgba(30, 111, 143, 0.05) inset;
            backdrop-filter: blur(16px);
            position: relative;
            overflow: hidden;
        }

        .login-brand {
            min-height: 100%;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            gap: 1rem;
            background:
                linear-gradient(145deg, #102438 0%, #1f6f8f 56%, #2f8f68 100%);
            border-color: rgba(255, 255, 255, 0.28);
            box-shadow:
                0 32px 70px rgba(16, 36, 56, 0.3),
                0 2px 0 rgba(255, 255, 255, 0.22) inset;
        }

        .login-brand::after {
            content: "";
            position: absolute;
            right: -48px;
            bottom: -54px;
            width: 220px;
            height: 150px;
            border: 1px solid rgba(255, 255, 255, 0.18);
            background:
                linear-gradient(145deg, rgba(255, 255, 255, 0.18), rgba(255, 255, 255, 0.04));
            transform: rotate(-12deg);
            pointer-events: none;
        }

        .login-brand .hero-kicker {
            background: rgba(255, 255, 255, 0.16);
            color: #e9fbff;
            border: 1px solid rgba(255, 255, 255, 0.24);
        }

        .login-brand .hero-title {
            color: #ffffff;
            text-shadow: 0 8px 24px rgba(0, 0, 0, 0.22);
        }

        .login-brand .hero-copy {
            color: rgba(244, 250, 252, 0.9);
        }

        .login-access {
            border-top: 4px solid #1e6f8f;
        }

        .login-access .hero-title {
            color: #102438;
        }

        div[data-testid="stForm"] {
            background:
                linear-gradient(145deg, rgba(255, 255, 255, 0.99), rgba(241, 246, 247, 0.96));
            border: 1px solid rgba(22, 32, 51, 0.12);
            border-radius: 18px;
            padding: 1rem 1rem 1.15rem 1rem;
            box-shadow:
                0 24px 52px rgba(36, 51, 77, 0.15),
                0 2px 0 rgba(255, 255, 255, 0.95) inset;
            margin-top: 0.9rem;
        }

        div[data-testid="stForm"] label {
            color: #162033;
            font-weight: 760;
        }

        .login-badge-row {
            display: flex;
            flex-wrap: wrap;
            gap: 0.55rem;
            margin-top: 1rem;
        }

        .mini-badge {
            border: 1px solid rgba(255, 255, 255, 0.22);
            background: rgba(255, 255, 255, 0.14);
            border-radius: 999px;
            color: #f4fafc;
            font-size: 0.82rem;
            font-weight: 700;
            padding: 0.35rem 0.7rem;
            box-shadow: 0 10px 22px rgba(0, 0, 0, 0.12);
        }

        .credential-note {
            color: #4f6077;
            font-size: 0.9rem;
            line-height: 1.55;
            margin: 0.35rem 0 0.85rem 0;
        }

        div[data-testid="stExpander"] details {
            background: rgba(255, 255, 255, 0.86);
            border: 1px solid rgba(22, 32, 51, 0.12);
            border-radius: 14px;
            box-shadow: 0 16px 34px rgba(36, 51, 77, 0.1);
        }

        .feedback-section {
            border: 1px solid rgba(30, 111, 143, 0.18);
            background:
                linear-gradient(145deg, rgba(255, 255, 255, 0.82), rgba(243, 249, 247, 0.72));
            border-radius: 18px;
            box-shadow: var(--shadow-soft);
            padding: 1rem;
            margin: 1rem 0;
            backdrop-filter: blur(16px);
        }

        .feedback-header {
            display: flex;
            justify-content: space-between;
            gap: 1rem;
            align-items: flex-start;
            margin-bottom: 0.85rem;
        }

        .feedback-title {
            color: var(--text);
            font-size: 1.08rem;
            font-weight: 850;
            margin: 0;
        }

        .feedback-subtitle {
            color: var(--muted);
            font-size: 0.9rem;
            margin: 0.2rem 0 0 0;
            line-height: 1.45;
        }

        .feedback-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
            gap: 0.8rem;
        }

        .feedback-card {
            min-height: 118px;
            border: 1px solid rgba(35, 55, 85, 0.12);
            border-radius: 14px;
            padding: 0.85rem;
            background:
                linear-gradient(150deg, rgba(255, 255, 255, 0.96), rgba(248, 246, 239, 0.78));
            box-shadow: 0 10px 24px rgba(36, 51, 77, 0.08);
            transition: transform 160ms ease, box-shadow 160ms ease, border-color 160ms ease;
        }

        .feedback-card:hover {
            transform: translateY(-2px);
            border-color: rgba(30, 111, 143, 0.26);
            box-shadow: 0 16px 32px rgba(36, 51, 77, 0.14);
        }

        .feedback-label {
            color: var(--accent);
            font-size: 0.78rem;
            font-weight: 850;
            text-transform: uppercase;
            letter-spacing: 0;
            margin-bottom: 0.45rem;
        }

        .feedback-value {
            color: var(--text);
            font-size: 0.96rem;
            line-height: 1.45;
            word-break: break-word;
        }

        .feedback-empty {
            color: var(--muted);
            font-style: italic;
        }

        @media (max-width: 768px) {
            .hero-title {
                font-size: 1.55rem;
            }

            .feedback-header {
                display: block;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def initialize_session_state() -> None:
    defaults = {
        "authenticated": False,
        "intro_seen": False,
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


def normalize_roll_number(value: Any) -> str:
    return "".join(str(value or "").upper().strip().split())


@st.cache_data(show_spinner=False)
def load_student_login_registers() -> list[str]:
    from core.preprocess import load_subject_data

    df = load_subject_data()
    df.columns = df.columns.str.strip()
    if "Register Number" not in df.columns:
        return []

    register_numbers = (
        df["Register Number"]
        .dropna()
        .map(normalize_roll_number)
    )
    return sorted({register_number for register_number in register_numbers if register_number})


def authenticate_user(
    role: str,
    username: str,
    password: str,
    student_registers: Iterable[str],
) -> tuple[bool, dict[str, Any], str]:
    clean_username = str(username or "").strip()

    if role == "Student":
        register_number = normalize_roll_number(clean_username)
        password_roll = normalize_roll_number(password)
        valid_registers = set(student_registers)
        if register_number and password_roll == register_number and register_number in valid_registers:
            return True, {"register_number": register_number}, register_number
        return False, {}, clean_username

    account = ROLE_USERS.get(role, {}).get(clean_username)
    if account and str(password or "") == str(account.get("password", "")):
        profile = {key: value for key, value in account.items() if key != "password"}
        profile["account_id"] = clean_username
        return True, profile, clean_username

    return False, {}, clean_username


def build_credential_table(student_registers: Iterable[str]) -> pd.DataFrame:
    rows: list[dict[str, str]] = []
    examples = list(student_registers)[:3]
    if examples:
        for register_number in examples:
            rows.append(
                {
                    "Role": "Student",
                    "Username": register_number,
                    "Password": register_number,
                    "Scope": "Own student dashboard",
                }
            )
    else:
        rows.append(
            {
                "Role": "Student",
                "Username": "Any valid roll number",
                "Password": "Same roll number",
                "Scope": "Own student dashboard",
            }
        )

    for role, users in ROLE_USERS.items():
        for username, details in users.items():
            scope_parts = []
            if details.get("department"):
                scope_parts.append(str(details["department"]))
            if details.get("subjects"):
                scope_parts.append(", ".join(map(str, details["subjects"])))
            if details.get("mentees"):
                scope_parts.append(f"{len(details['mentees'])} mentees")
            rows.append(
                {
                    "Role": role,
                    "Username": username,
                    "Password": str(details.get("password", "")),
                    "Scope": " | ".join(scope_parts) if scope_parts else "Institution",
                }
            )

    return pd.DataFrame(rows)


def render_intro_screen() -> None:
    apply_intro_background()

    st.markdown(
        """
        <div class="intro-cover">
            <div class="intro-copy">
                <div class="intro-kicker">Academic Intelligence Platform</div>
                <div class="intro-title">Institutional Academic Intelligence</div>
                <p class="intro-subtitle">
                    A premium analytics workspace for student performance, mentoring, subject risk,
                    and department-level academic decisions.
                </p>
                <div class="intro-prompt">Swipe up visually, or click to continue to secure login.</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("Enter Login", key="intro_enter_login"):
        st.session_state["intro_seen"] = True
        _rerun()


def render_login_screen() -> None:
    apply_login_background()

    try:
        student_registers = load_student_login_registers()
        login_data_error = ""
    except Exception as error:
        student_registers = []
        login_data_error = str(error)

    left_col, right_col = st.columns([1.1, 0.9], gap="large")

    with left_col:
        st.markdown(
            """
            <div class="login-shell login-brand">
                <div>
                    <div class="hero-kicker">Academic Intelligence Platform</div>
                    <div class="hero-title">Institutional Performance Workspace</div>
                    <p class="hero-copy">
                        Role-scoped academic intelligence for students, mentors, faculty, HODs, and leadership.
                        The core prediction and analytics workflows stay intact while access is cleaner and safer.
                    </p>
                    <div class="login-badge-row">
                        <span class="mini-badge">Student roll login</span>
                        <span class="mini-badge">Scoped dashboards</span>
                        <span class="mini-badge">Feedback insights</span>
                        <span class="mini-badge">Protected AI calls</span>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with right_col:
        st.markdown(
            """
            <div class="login-shell login-access">
                <div class="hero-kicker">Secure Prototype Access</div>
                <div class="hero-title" style="font-size:1.55rem;">Sign in</div>
                <p class="credential-note">
                    Students use their register number as both username and password. Staff users use the
                    prototype role accounts listed below.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if login_data_error:
            st.warning(f"Student register lookup is unavailable: {login_data_error}")

        with st.form("login_form", clear_on_submit=False):
            role = st.selectbox("Role", ROLE_OPTIONS, key="login_role")
            username = st.text_input("Username", key="login_username")
            password = st.text_input("Password", type="password", key="login_password")
            submitted = st.form_submit_button("Log in", use_container_width=True)

        if submitted:
            is_authenticated, profile, display_username = authenticate_user(
                role,
                username,
                password,
                student_registers,
            )
            if is_authenticated:
                st.session_state["authenticated"] = True
                st.session_state["user_role"] = role
                st.session_state["username"] = display_username
                st.session_state["user_profile"] = profile
                st.session_state["nav_section"] = ROLE_SECTIONS[role][0]
                _rerun()
            else:
                st.error("Invalid username or password for the selected role.")

        with st.expander("View prototype credentials"):
            st.dataframe(
                build_credential_table(student_registers),
                use_container_width=True,
                hide_index=True,
            )


def render_authenticated_app(df: pd.DataFrame, enriched_df: pd.DataFrame) -> None:
    apply_dashboard_background()

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
    health_score = calculate_health_score(scope_df) if not scope_df.empty else 0.0

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

        if role == "Principal":
            st.caption(
                f"Institution dataset: {int(df['Register Number'].nunique())} students and {int(df['Course Code'].nunique())} subjects."
            )
        else:
            st.caption("Access is limited to the current role scope.")
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


def clean_feedback_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["Roll Number"])

    cleaned_df = df.copy()
    cleaned_df.columns = [" ".join(str(column).strip().split()) for column in cleaned_df.columns]

    roll_column = next(
        (
            column
            for column in cleaned_df.columns
            if " ".join(str(column).lower().split()) == "roll number"
        ),
        None,
    )
    if roll_column is None:
        return pd.DataFrame(columns=["Roll Number"])

    if roll_column != "Roll Number":
        cleaned_df = cleaned_df.rename(columns={roll_column: "Roll Number"})

    object_columns = cleaned_df.select_dtypes(include=["object"]).columns
    for column in object_columns:
        cleaned_df[column] = (
            cleaned_df[column]
            .astype(str)
            .str.replace(r"\s+", " ", regex=True)
            .str.strip()
        )
        cleaned_df.loc[
            cleaned_df[column].str.lower().isin({"nan", "none", "nat"}),
            column,
        ] = ""

    cleaned_df["Roll Number"] = cleaned_df["Roll Number"].map(normalize_roll_number)
    cleaned_df = cleaned_df[cleaned_df["Roll Number"].astype(bool)].drop_duplicates(
        subset=["Roll Number"],
        keep="last",
    )
    return cleaned_df.reset_index(drop=True)


@st.cache_data(show_spinner=False)
def load_feedback_datasets() -> tuple[pd.DataFrame, pd.DataFrame]:
    def read_feedback_csv(path: str) -> pd.DataFrame:
        try:
            return clean_feedback_dataframe(pd.read_csv(path))
        except FileNotFoundError:
            return pd.DataFrame(columns=["Roll Number"])
        except Exception:
            return pd.DataFrame(columns=["Roll Number"])

    return read_feedback_csv(ACADEMIC_FEEDBACK_PATH), read_feedback_csv(CAREER_FEEDBACK_PATH)


def get_feedback_record(feedback_df: pd.DataFrame, register_number: Any) -> dict[str, Any]:
    if feedback_df.empty or "Roll Number" not in feedback_df.columns:
        return {}

    key = normalize_roll_number(register_number)
    matches = feedback_df[feedback_df["Roll Number"] == key]
    if matches.empty:
        return {}
    return matches.iloc[0].to_dict()


def normalize_feedback_key(value: Any) -> str:
    return " ".join(str(value or "").lower().split())


def feedback_value_by_tokens(record: dict[str, Any], token_groups: Iterable[Iterable[str]]) -> str:
    if not record:
        return ""

    normalized_keys = {
        key: normalize_feedback_key(key)
        for key in record.keys()
    }
    for tokens in token_groups:
        normalized_tokens = [normalize_feedback_key(token) for token in tokens]
        for key, normalized_key in normalized_keys.items():
            if all(token in normalized_key for token in normalized_tokens):
                value = str(record.get(key, "")).strip()
                if value:
                    return value
    return ""


def render_feedback_cards(
    title: str,
    subtitle: str,
    record: dict[str, Any],
    fields: list[tuple[str, list[tuple[str, ...]]]],
) -> None:
    cards = []
    for label, token_groups in fields:
        value = feedback_value_by_tokens(record, token_groups)
        value_class = "feedback-value" if value else "feedback-value feedback-empty"
        cards.append(
            '<div class="feedback-card">'
            f'<div class="feedback-label">{escape(label)}</div>'
            f'<div class="{value_class}">{escape(value or "Not provided")}</div>'
            "</div>"
        )

    feedback_html = "".join(
        [
            '<div class="feedback-section">',
            '<div class="feedback-header"><div>',
            f'<div class="feedback-title">{escape(title)}</div>',
            f'<p class="feedback-subtitle">{escape(subtitle)}</p>',
            "</div></div>",
            f'<div class="feedback-grid">{"".join(cards)}</div>',
            "</div>",
        ]
    )
    st.markdown(feedback_html, unsafe_allow_html=True)


def render_student_feedback_sections(register_number: Any) -> None:
    academic_feedback_df, career_feedback_df = load_feedback_datasets()
    academic_record = get_feedback_record(academic_feedback_df, register_number)
    career_record = get_feedback_record(career_feedback_df, register_number)

    render_feedback_cards(
        "Academic Feedback Insights",
        "Student-submitted academic signals joined by roll number.",
        academic_record,
        [
            ("Subjects Struggled With", [("subjects", "struggle")]),
            ("Learning Difficulties", [("specifically", "difficult"), ("makes", "difficult")]),
            ("Learning Style", [("learn better",), ("learning style",)]),
            ("Class Participation", [("participate", "class")]),
            ("Comfort Asking Doubts", [("comfortable", "doubts")]),
            ("Biggest Challenges", [("biggest challenges",)]),
            ("Department Improvements", [("department", "improvement"), ("learning experience",)]),
        ],
    )

    render_feedback_cards(
        "Career & Future Support",
        "Career readiness and placement-support needs joined by roll number.",
        career_record,
        [
            ("Technical Skills", [("technical skills",)]),
            ("Hackathon Participation", [("hackathons",), ("workshops", "competitions")]),
            ("Career Interests", [("career path",), ("interested",)]),
            ("Confidence Level", [("confident", "career choice")]),
            ("Guidance Needs", [("guidance", "need"), ("internships", "placements")]),
            ("Expected Department Support", [("expect", "department"), ("placement training",)]),
        ],
    )


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

    render_student_feedback_sections(register_number)

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
    scope_df = context.get("scope_df", pd.DataFrame())
    department = context.get("department", "Department")
    handled_subjects = context.get("subjects", [])

    render_page_header(
        "Faculty Dashboard",
        f"{department} Handled Subjects",
        "Faculty access is scoped to the assigned department and handled subjects, with weak students and subject failure analytics only.",
    )

    render_html_panel(
        "Handled subjects",
        handled_subjects or ["No handled subjects configured for this faculty account."],
    )

    if scope_df.empty:
        st.error("No subject data is available for this faculty profile and handled-subject scope.")
        return

    high_risk_students = get_high_risk_students(scope_df)
    subject_stats = build_subject_summary(scope_df)
    weak_student_count = (
        int(high_risk_students["Register Number"].nunique())
        if not high_risk_students.empty
        else 0
    )

    render_metric_row(
        [
            {"label": "Department", "value": str(department), "caption": "Role scope"},
            {"label": "Handled Subjects", "value": str(scope_df["Course Name"].nunique()), "caption": "Matched in dataset"},
            {"label": "Failure Rate", "value": f"{(1 - scope_df['Result_Binary'].mean()) * 100:.1f}%", "caption": "Handled-subject records"},
            {"label": "Weak Students", "value": str(weak_student_count), "caption": "Failed, weak internal, or low confidence"},
        ]
    )

    chart_col, table_col = st.columns([1.2, 1], gap="large")

    with chart_col:
        render_section_heading("Subject failure analytics", "Fail-rate pressure across handled subjects.")
        subject_chart = subject_stats.set_index("Course Name")["Fail Rate %"]
        st.bar_chart(subject_chart, use_container_width=True)

    with table_col:
        render_section_heading("Weak students", "Students who need follow-up in the handled subjects.")
        if high_risk_students.empty:
            st.success("No weak students are currently flagged for this faculty scope.")
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

    render_section_heading("Handled subject summary", "Failure analytics limited to this faculty account.")
    st.dataframe(
        subject_stats[
            [
                "Subject Label",
                "Students",
                "Fail Rate %",
                "High Risk Students",
                "Weak Internal Students",
                "Risk Level",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )


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
    priority_table = build_student_priority_table(scope_df)
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

    risk_col, students_col = st.columns([0.95, 1.25], gap="large")

    with risk_col:
        render_section_heading("Department risk distribution", "Student count by blended academic risk band.")
        band_counts = (
            priority_table["Risk Band"].value_counts().reindex(["High", "Moderate", "Low"], fill_value=0)
            if not priority_table.empty
            else pd.Series([0, 0, 0], index=["High", "Moderate", "Low"])
        )
        st.bar_chart(band_counts, use_container_width=True)

    with students_col:
        render_section_heading("Department students", "Students visible to this HOD account only.")
        display_columns = ["Register Number", "Student Name", "Average GP", "Pass Rate %", "Risk Band"]
        st.dataframe(priority_table[display_columns], use_container_width=True, hide_index=True)

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
    scope_df = context.get("scope_df", pd.DataFrame())
    department = context.get("department", "Department")

    render_page_header(
        "Subject Analytics",
        f"{department} Faculty Subject Risk Analytics",
        "Subject analytics are limited to the faculty account's department and handled subjects.",
    )

    if scope_df.empty:
        st.error("Faculty subject analytics are unavailable for this profile.")
        return

    high_risk_students = get_high_risk_students(scope_df)
    subject_stats = build_subject_summary(scope_df)
    weakest_subject = subject_stats.iloc[0] if not subject_stats.empty else None

    render_metric_row(
        [
            {"label": "Students", "value": str(scope_df["Register Number"].nunique()), "caption": "Learners in subject"},
            {"label": "Subjects", "value": str(scope_df["Course Name"].nunique()), "caption": "Handled subjects"},
            {"label": "Pass Rate", "value": f"{scope_df['Result_Binary'].mean() * 100:.1f}%", "caption": "Historical success rate"},
            {"label": "Weak Internals", "value": str(int(scope_df["Weak Internal"].sum())), "caption": "Below threshold internally"},
        ]
    )

    chart_col, table_col = st.columns([1.2, 1], gap="large")

    with chart_col:
        render_section_heading("Subject failure spread", "Fail rate by handled subject.")
        st.bar_chart(subject_stats.set_index("Course Name")["Fail Rate %"], use_container_width=True)

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

    render_section_heading("Handled subject analytics", "Subject failure analytics for this faculty account.")
    st.dataframe(
        subject_stats[
            [
                "Subject Label",
                "Students",
                "Pass Rate %",
                "Fail Rate %",
                "Average Gap",
                "High Risk Students",
                "Risk Level",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )

    render_ai_panel(
        title="AI subject insight",
        description="Generate a short intervention plan for this subject.",
        report_key=f"faculty_subject_ai_{department}_{context.get('account_id', 'faculty')}",
        button_label="Generate subject analytics insight",
        generator=lambda: generate_subject_report(
            {
                "course_code": "Multiple",
                "course_name": (
                    "Multiple handled subjects"
                    if weakest_subject is None
                    else str(weakest_subject["Course Name"])
                ),
                "semester": (
                    "Multiple"
                    if weakest_subject is None
                    else int(weakest_subject["Sem No"])
                ),
                "pass_rate": round(float(scope_df["Result_Binary"].mean() * 100), 1),
                "fail_rate": round(float((1 - scope_df["Result_Binary"].mean()) * 100), 1),
                "avg_internal": round(float(scope_df["Internal Mark"].mean()), 1),
                "avg_external": round(float(scope_df["External Mark"].mean()), 1),
                "avg_gap": round(float(scope_df["Internal-External Gap"].mean()), 1),
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
    enriched_df["Register Number"] = enriched_df["Register Number"].map(normalize_roll_number)
    for text_column in ["Department", "Student Name", "Course Code", "Course Name"]:
        enriched_df[text_column] = (
            enriched_df[text_column]
            .astype(str)
            .str.replace(r"\s+", " ", regex=True)
            .str.strip()
        )
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
        enriched_df["Register Number"].map(normalize_roll_number) == normalize_roll_number(reg_no)
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
        department = resolve_department(enriched_df, context.get("department"))
        handled_subjects = [
            str(subject).strip()
            for subject in context.get("subjects", [])
            if str(subject).strip()
        ]
        department_scope = filter_by_department(enriched_df, department)
        scope_df = filter_by_subject_names(department_scope, handled_subjects)
        subject_stats = build_subject_summary(scope_df)
        subject_meta = None if subject_stats.empty else subject_stats.iloc[0]
        context.update(
            {
                "department": department,
                "subjects": handled_subjects,
                "subject_meta": subject_meta,
                "subject_stats": subject_stats,
                "scope_df": scope_df,
            }
        )
        return context

    if role == "Mentor":
        mentee_ids = resolve_mentee_ids(enriched_df, context.get("mentees", context.get("mentee_ids", [])))
        scope_df = enriched_df[
            enriched_df["Register Number"].map(normalize_roll_number).isin(mentee_ids)
        ].copy()
        context.update(
            {
                "mentee_ids": mentee_ids,
                "scope_df": scope_df,
            }
        )
        return context

    if role == "HOD":
        department = resolve_department(enriched_df, context.get("department"))
        scope_df = filter_by_department(enriched_df, department)
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
    available = sorted(enriched_df["Register Number"].map(normalize_roll_number).unique().tolist())
    if not available:
        return None

    configured_value = normalize_roll_number(configured_register)
    return configured_value if configured_value in available else None


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
    available = set(enriched_df["Register Number"].map(normalize_roll_number).unique().tolist())
    configured = [
        normalize_roll_number(value)
        for value in configured_ids
        if normalize_roll_number(value) in available
    ]
    return configured


def resolve_department(enriched_df: pd.DataFrame, configured_department: Any) -> str:
    configured_key = normalize_department_key(configured_department)
    available = enriched_df["Department"].dropna().astype(str).unique().tolist()
    for department in available:
        if normalize_department_key(department) == configured_key:
            return str(department).strip()
    return DEPARTMENT_LABELS.get(configured_key, str(configured_department or "Department").strip())


def filter_by_register_number(enriched_df: pd.DataFrame, register_number: str | None) -> pd.DataFrame:
    if register_number is None:
        return enriched_df.iloc[0:0].copy()
    key = normalize_roll_number(register_number)
    return enriched_df[enriched_df["Register Number"].map(normalize_roll_number) == key].copy()


def normalize_department_key(value: Any) -> str:
    normalized = " ".join(str(value or "").upper().strip().split())
    for key, aliases in DEPARTMENT_ALIASES.items():
        if normalized in aliases:
            return key
    return normalized


def filter_by_department(enriched_df: pd.DataFrame, department: Any) -> pd.DataFrame:
    if enriched_df.empty or "Department" not in enriched_df.columns:
        return enriched_df.iloc[0:0].copy()

    department_key = normalize_department_key(department)
    return enriched_df[
        enriched_df["Department"].map(normalize_department_key) == department_key
    ].copy()


def filter_by_subject_names(enriched_df: pd.DataFrame, subjects: Iterable[Any]) -> pd.DataFrame:
    subject_keys = {
        " ".join(str(subject).upper().strip().split())
        for subject in subjects
        if str(subject).strip()
    }
    if not subject_keys:
        return enriched_df.iloc[0:0].copy()

    course_name_keys = enriched_df["Course Name"].astype(str).map(
        lambda value: " ".join(value.upper().strip().split())
    )
    course_code_keys = enriched_df["Course Code"].astype(str).map(
        lambda value: " ".join(value.upper().strip().split())
    )
    return enriched_df[
        course_name_keys.isin(subject_keys) | course_code_keys.isin(subject_keys)
    ].copy()


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
        subjects = context.get("subjects", [])
        subject_label = ", ".join(map(str, subjects[:2])) if subjects else "Handled subjects"
        if len(subjects) > 2:
            subject_label += f" +{len(subjects) - 2}"
        return f"{context.get('department', 'Department')} | {subject_label}"

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
