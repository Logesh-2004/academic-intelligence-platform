from __future__ import annotations

import os
from functools import lru_cache
from typing import Any, Iterable

import requests

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
OLLAMA_URL = f"{OLLAMA_BASE_URL}/api/generate"
OLLAMA_TAGS_URL = f"{OLLAMA_BASE_URL}/api/tags"
MODEL_NAME = os.getenv("OLLAMA_MODEL", "mistral")
DEFAULT_AI_FALLBACK = (
    "AI insights are temporarily unavailable. Please check the local Ollama service and try again."
)
PREFERRED_MODEL_NAMES = (
    "mistral",
    "llama3.2",
    "llama3",
    "phi3",
    "gemma2",
    "qwen2.5",
)


def _read_int_env(name: str, default: int, minimum: int = 1) -> int:
    raw_value = str(os.getenv(name, "")).strip()
    if not raw_value:
        return default

    try:
        return max(minimum, int(raw_value))
    except ValueError:
        return default


REQUEST_TIMEOUT_SECONDS = _read_int_env("OLLAMA_TIMEOUT_SECONDS", 120, minimum=30)
CONNECT_TIMEOUT_SECONDS = _read_int_env("OLLAMA_CONNECT_TIMEOUT_SECONDS", 5, minimum=1)
DISCOVERY_TIMEOUT_SECONDS = _read_int_env("OLLAMA_DISCOVERY_TIMEOUT_SECONDS", 5, minimum=1)
GENERATION_OPTIONS = {
    "temperature": 0.2,
    "num_predict": 180,
}


def _normalize_model_name(model_name: Any) -> str:
    return str(model_name or "").strip()


def _model_base_name(model_name: Any) -> str:
    return _normalize_model_name(model_name).split(":", 1)[0]


@lru_cache(maxsize=1)
def _get_available_models() -> tuple[str, ...]:
    try:
        response = requests.get(
            OLLAMA_TAGS_URL,
            timeout=(CONNECT_TIMEOUT_SECONDS, DISCOVERY_TIMEOUT_SECONDS),
        )
        response.raise_for_status()
        data = response.json()
    except (requests.exceptions.RequestException, ValueError):
        return tuple()

    discovered: list[str] = []
    for model_info in data.get("models", []):
        model_name = _normalize_model_name(
            model_info.get("name") or model_info.get("model") or model_info.get("digest")
        )
        if model_name and model_name not in discovered:
            discovered.append(model_name)

    return tuple(discovered)


def _build_model_candidates(requested_model: str) -> list[str]:
    requested_name = _normalize_model_name(requested_model) or MODEL_NAME
    discovered_models = list(_get_available_models())
    candidates: list[str] = []

    def add_candidate(model_name: Any) -> None:
        normalized = _normalize_model_name(model_name)
        if normalized and normalized not in candidates:
            candidates.append(normalized)

    add_candidate(requested_name)

    if not discovered_models:
        return candidates

    discovered_by_base: dict[str, str] = {}
    for discovered_model in discovered_models:
        discovered_by_base.setdefault(_model_base_name(discovered_model), discovered_model)

    requested_base_name = _model_base_name(requested_name)
    if requested_base_name in discovered_by_base:
        add_candidate(discovered_by_base[requested_base_name])

    for base_name in PREFERRED_MODEL_NAMES:
        if base_name in discovered_by_base:
            add_candidate(discovered_by_base[base_name])

    for discovered_model in discovered_models:
        add_candidate(discovered_model)

    return candidates


def _request_ollama(
    prompt: str,
    model: str = MODEL_NAME,
    timeout_seconds: int = REQUEST_TIMEOUT_SECONDS,
) -> tuple[bool, str]:
    if not prompt or not prompt.strip():
        return False, "The AI prompt was empty."

    attempted_models: list[str] = []
    timeout_models: list[str] = []
    missing_models: list[str] = []
    last_error_message = "Ollama did not return a usable response."

    for candidate_model in _build_model_candidates(model):
        attempted_models.append(candidate_model)
        payload = {
            "model": candidate_model,
            "prompt": prompt.strip(),
            "stream": False,
            "options": GENERATION_OPTIONS,
        }

        try:
            response = requests.post(
                OLLAMA_URL,
                json=payload,
                timeout=(CONNECT_TIMEOUT_SECONDS, timeout_seconds),
            )
            response.raise_for_status()
            data = response.json()
            message = str(data.get("response", "")).strip()

            if not message:
                last_error_message = f'Ollama returned an empty response for model "{candidate_model}".'
                continue

            return True, message
        except requests.exceptions.Timeout:
            timeout_models.append(candidate_model)
            last_error_message = (
                f'The Ollama request timed out for model "{candidate_model}". '
                "A first model load on CPU can take longer than expected."
            )
        except requests.exceptions.ConnectionError:
            return False, f"Ollama is not reachable at {OLLAMA_BASE_URL}."
        except requests.exceptions.HTTPError as error:
            status_code = error.response.status_code if error.response is not None else "unknown"
            if status_code == 404:
                missing_models.append(candidate_model)
                last_error_message = f'Model "{candidate_model}" is not installed in Ollama.'
                continue
            return False, f"Ollama returned HTTP {status_code}."
        except ValueError:
            return False, "Ollama returned unreadable JSON."
        except requests.exceptions.RequestException as error:
            return False, f"Request failed: {error}"
        except Exception as error:
            return False, f"Unexpected AI error: {error}"

    if timeout_models:
        attempted_label = ", ".join(attempted_models)
        return (
            False,
            f"{last_error_message} Tried models: {attempted_label}. "
            f"Increase OLLAMA_TIMEOUT_SECONDS above {timeout_seconds} or use a lighter installed model.",
        )

    available_models = list(_get_available_models())
    if missing_models and available_models:
        return (
            False,
            f'{last_error_message} Available local models: {", ".join(available_models[:6])}. '
            "Set OLLAMA_MODEL to one of the installed model names if needed.",
        )

    return False, last_error_message


def safe_generate_report(
    prompt: str,
    fallback_message: str = DEFAULT_AI_FALLBACK,
    model: str = MODEL_NAME,
    timeout_seconds: int = REQUEST_TIMEOUT_SECONDS,
) -> str:
    success, message = _request_ollama(
        prompt=prompt,
        model=model,
        timeout_seconds=timeout_seconds,
    )

    if success:
        return message

    return f"{fallback_message}\n\nReason: {message}"


def _to_name_list(values: Any, field_name: str = "Course Name") -> list[str]:
    if values is None:
        return []

    if hasattr(values, "to_dict"):
        values = values.to_dict(orient="records")

    if isinstance(values, dict):
        values = [values]

    if not isinstance(values, list):
        return [str(values).strip()] if str(values).strip() else []

    extracted: list[str] = []
    for item in values:
        if isinstance(item, dict):
            value = str(item.get(field_name, "")).strip()
        else:
            value = str(item).strip()

        if value:
            extracted.append(value)

    return extracted


def _list_to_lines(values: Iterable[Any]) -> str:
    items = [str(value).strip() for value in values if str(value).strip()]
    if not items:
        return "- None identified"
    return "\n".join(f"- {item}" for item in items)


def generate_student_report(summary: dict) -> str:
    weak_subjects = _to_name_list(summary.get("weak_subjects"))
    gap_subjects = _to_name_list(summary.get("gap_subjects"))

    prompt = f"""
You are an academic performance advisor.

Student Summary:
- Average Internal: {summary.get("avg_internal", "N/A")}
- Average External: {summary.get("avg_external", "N/A")}
- Average GPA: {summary.get("avg_gp", "N/A")}
- Student Name: {summary.get("student_name", "Unknown")}

Weak Subjects:
{_list_to_lines(weak_subjects)}

High Gap Subjects:
{_list_to_lines(gap_subjects)}

Generate:
1. Academic weaknesses
2. Risk interpretation
3. Improvement strategy
4. Faculty support suggestions

Keep the response concise and actionable.
"""

    return safe_generate_report(prompt)


def generate_projection_summary(projected_df) -> str:
    subject_stats = projected_df.groupby("Course Name")["Result_Binary"].mean()
    low_subjects = subject_stats[subject_stats < 0.75].sort_values()

    prompt = f"""
You are an academic planning advisor.

Projected Cohort Summary:
- Average Internal Mark: {round(float(projected_df["Internal Mark"].mean()), 2)}
- Average External Mark: {round(float(projected_df["External Mark"].mean()), 2)}
- Average GPA: {round(float(projected_df["gp"].mean()), 2)}
- Overall Pass Percentage: {round(float(projected_df["Result_Binary"].mean() * 100), 2)}%

High-Risk Subjects:
{_list_to_lines(low_subjects.index.tolist()[:5])}

Provide:
1. Subjects needing extra teaching focus
2. Faculty workload planning advice
3. Student support strategies
4. A short intervention plan

Keep the output short and practical.
"""

    return safe_generate_report(prompt)


def generate_subject_report(context: dict) -> str:
    prompt = f"""
You are an academic teaching advisor helping a faculty member.

Subject Summary:
- Course Code: {context.get("course_code", "N/A")}
- Course Name: {context.get("course_name", "N/A")}
- Semester: {context.get("semester", "N/A")}
- Pass Rate: {context.get("pass_rate", "N/A")}%
- Fail Rate: {context.get("fail_rate", "N/A")}%
- Average Internal: {context.get("avg_internal", "N/A")}
- Average External: {context.get("avg_external", "N/A")}
- Average Internal-External Gap: {context.get("avg_gap", "N/A")}

High-Risk Students:
{_list_to_lines(context.get("high_risk_students", []))}

Generate:
1. Root-cause interpretation of the subject risk
2. Immediate intervention priorities
3. Assessment and teaching adjustments
4. A short action plan for the next review cycle

Use concise bullet points.
"""

    return safe_generate_report(prompt)


def generate_subject_analytics_report(context: dict) -> str:
    prompt = f"""
You are an academic analytics advisor.

Audience Role: {context.get("role", "Academic User")}
Analytics Scope: {context.get("scope", "Subject Analytics")}
Performance Summary:
{_list_to_lines(context.get("summary_points", []))}

Priority Subjects:
{_list_to_lines(context.get("priority_subjects", []))}

Students Needing Attention:
{_list_to_lines(context.get("priority_students", []))}

Generate:
1. The most important academic pattern in this subject view
2. What should be acted on first
3. One short, role-appropriate recommendation

Keep it brief and presentation-ready.
"""

    return safe_generate_report(prompt)


def generate_mentor_report(context: dict) -> str:
    prompt = f"""
You are an academic mentor advisor.

Mentor Cohort Summary:
- Mentee Count: {context.get("mentee_count", "N/A")}
- High Risk Count: {context.get("high_risk_count", "N/A")}
- Moderate Risk Count: {context.get("moderate_risk_count", "N/A")}
- Average GPA: {context.get("average_gp", "N/A")}

Priority Students:
{_list_to_lines(context.get("priority_students", []))}

Repeated Weak Subjects:
{_list_to_lines(context.get("weak_subjects", []))}

Generate:
1. Mentor outreach priorities
2. Conversation focus for one-to-one mentoring
3. Escalation advice for academic risk
4. A short weekly intervention plan

Keep it practical and concise.
"""

    return safe_generate_report(prompt)


def generate_department_report(context: dict) -> str:
    prompt = f"""
You are an academic department advisor supporting a Head of Department.

Department Summary:
- Department: {context.get("department", "N/A")}
- Health Score: {context.get("health_score", "N/A")}
- Pass Rate: {context.get("pass_rate", "N/A")}%
- Average GPA: {context.get("avg_gp", "N/A")}

Top Weak Subjects:
{_list_to_lines(context.get("top_weak_subjects", []))}

Semester Summary:
{_list_to_lines(context.get("semester_summary", []))}

Generate:
1. Department-level risk interpretation
2. Subject bottleneck priorities
3. Faculty allocation or intervention suggestions
4. A concise HOD action plan

Use brief bullet points with a management tone.
"""

    return safe_generate_report(prompt)


def generate_principal_report(context: dict) -> str:
    prompt = f"""
You are an executive academic strategy advisor supporting a college principal.

Executive Summary:
- Overall Health Score: {context.get("health_score", "N/A")}
- Pass Rate: {context.get("pass_rate", "N/A")}%
- Average GPA: {context.get("avg_gp", "N/A")}
- Projected Pass Rate: {context.get("projected_pass_rate", "N/A")}

Top Weak Subjects:
{_list_to_lines(context.get("top_weak_subjects", []))}

Department Comparison:
{_list_to_lines(context.get("department_summary", []))}

Generate:
1. Executive interpretation of current academic health
2. Leadership priorities for risk containment
3. What to monitor next at the department level
4. A short premium-style principal briefing

Keep the output short, strategic, and actionable.
"""

    return safe_generate_report(prompt)
