import streamlit as st

from core.dashboard_views import (
    apply_theme,
    enrich_dataset,
    initialize_session_state,
    render_authenticated_app,
    render_intro_screen,
    render_login_screen,
)
from core.preprocess import load_subject_data


st.set_page_config(
    page_title="Academic Intelligence Platform",
    layout="wide",
)


@st.cache_data(show_spinner=False)
def load_data():
    df = load_subject_data()
    df.columns = df.columns.str.strip()
    if "Register Number" in df.columns:
        df["Register Number"] = (
            df["Register Number"]
            .astype(str)
            .str.upper()
            .str.strip()
            .str.replace(r"\s+", "", regex=True)
        )
    return df


def main() -> None:
    apply_theme()
    initialize_session_state()

    if not st.session_state.get("authenticated"):
        if not st.session_state.get("intro_seen"):
            render_intro_screen()
            return
        render_login_screen()
        return

    try:
        df = load_data()
        if df.empty:
            st.error("The academic dataset is empty. Please verify the source file and try again.")
            return

        enriched_df = enrich_dataset(df)
    except FileNotFoundError as error:
        st.error(f"Required dataset or model file is missing: {error}")
        return
    except Exception as error:
        st.error(f"Unable to initialize the dashboard: {error}")
        return

    render_authenticated_app(df, enriched_df)


if __name__ == "__main__":
    main()
