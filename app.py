"""Ticket Readiness Checker — single-page Streamlit app."""

import streamlit as st

from groq_client import ScoringServiceError
from parsing import ParsingError
from scoring import RubricConfigError, load_rubric, score_ticket

st.set_page_config(page_title="Ticket Readiness Checker")
st.title("Ticket Readiness Checker")
st.write(
    "Ticket Readiness Checker scores a pasted ticket 0–100 across six readiness criteria "
    "(goal, acceptance criteria, scope, dependencies, test plan, constraints) and flags "
    "what's missing before it gets handed to a coding agent. I built it end-to-end using "
    "GitHub Spec Kit's spec-driven development process — constitution, spec, plan, tasks, "
    "implement — to experience firsthand what a single-player version of the workflow "
    "Command is building for teams actually feels like, including where it breaks."
)
st.write(
    "Paste a software ticket below to see how ready it is to hand off to an AI coding "
    "agent."
)

try:
    rubric = load_rubric()
except RubricConfigError as exc:
    st.error(f"Rubric configuration error: {exc}")
    st.stop()

labels_by_key = {c.key: c.label for c in rubric}

ticket_text = st.text_area("Ticket text", height=250)

if st.button("Check ticket"):
    if not ticket_text or not ticket_text.strip():
        st.warning("Please paste some ticket text before running a check.")
    else:
        with st.spinner("Evaluating ticket..."):
            try:
                st.session_state["result"] = score_ticket(ticket_text, rubric)
            except (RubricConfigError, ScoringServiceError, ParsingError) as exc:
                st.session_state["result"] = None
                st.error(str(exc))

result = st.session_state.get("result")

if result is not None:
    if result.status == "ok":
        st.subheader(f"Overall readiness score: {result.assessment.overall_score}/100")
        for cs in result.assessment.criterion_scores:
            label = labels_by_key.get(cs.key, cs.key)
            st.markdown(f"**{label}: {cs.score}/100**")
            if cs.score < 50 and cs.missing_items:
                for item in cs.missing_items:
                    st.markdown(f"- {item}")

    elif result.status == "too_short":
        st.info(result.guidance_message)

    elif result.status == "too_long":
        st.info(result.guidance_message)
        st.write("Proposed split:")
        for i, part in enumerate(result.proposed_split, start=1):
            st.markdown(f"**Ticket {i}:**")
            st.code(part)
