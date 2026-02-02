import requests
import streamlit as st

OLLAMA_URL = "http://localhost:11434/api/generate"

# Use mistral for speed (llama3 if GPU exists)
MODEL_NAME = "mistral"


# -------------------------------------------------
# Cached Ollama Request
# -------------------------------------------------

@st.cache_data(show_spinner=False)
def generate_report_cached(prompt):

    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False
    }

    try:

        response = requests.post(
            OLLAMA_URL,
            json=payload,
            timeout=180
        )

        if response.status_code == 200:
            data = response.json()
            return data.get("response", "⚠️ AI returned empty response")

        return "⚠️ AI Server Error"

    except requests.exceptions.ReadTimeout:
        return "⚠️ AI Timeout. Reduce prompt size or retry."

    except requests.exceptions.ConnectionError:
        return "⚠️ Ollama not running. Start with: ollama serve"

    except Exception as e:
        return f"⚠️ AI Error: {str(e)}"


# -------------------------------------------------
# Student Report Generator
# -------------------------------------------------

def generate_student_report(summary):

    weak_subjects = summary.get("weak_subjects", [])
    gap_subjects = summary.get("gap_subjects", [])

    # ---- Safety Conversion ----

    if hasattr(weak_subjects, "to_dict"):
        weak_subjects = weak_subjects.to_dict(orient="records")

    if hasattr(gap_subjects, "to_dict"):
        gap_subjects = gap_subjects.to_dict(orient="records")

    weak_names = [x.get("Course Name", "") for x in weak_subjects]
    gap_names = [x.get("Course Name", "") for x in gap_subjects]

    prompt = f"""
You are an academic performance advisor.

Student Summary:
Average Internal: {summary['avg_internal']}
Average External: {summary['avg_external']}
Average GP: {summary['avg_gp']}

Weak Subjects:
{weak_names}

High Gap Subjects:
{gap_names}

Generate:
1. Academic weaknesses
2. Failure reasons
3. Improvement strategy
4. Faculty intervention advice

Use bullet points. Keep concise.
"""

    return generate_report_cached(prompt)

def generate_projection_summary(projected_df):

    # Subject-wise pass rate
    subject_stats = projected_df.groupby("Course Code")["Result_Binary"].mean()

    low_subjects = subject_stats[subject_stats < 0.75].sort_values()

    weak_subjects = [f"Course Code {x}" for x in low_subjects.index.tolist()[:5]]

    avg_internal = projected_df["Internal Mark"].mean()
    avg_external = projected_df["External Mark"].mean()

    pass_rate = projected_df["Result_Binary"].mean() * 100

    prompt = f"""
You are an academic planning advisor.

Batch Projection Summary:

Average Internal Mark: {round(avg_internal,2)}
Average External Mark: {round(avg_external,2)}
Overall Pass Percentage: {round(pass_rate,2)}%

High Risk Subjects:
{weak_subjects}

Provide:
1. Subjects needing extra teaching focus
2. Faculty workload planning advice
3. Student support strategies
4. Academic intervention plan

Keep output short and actionable.
"""

    return generate_report_cached(prompt)
