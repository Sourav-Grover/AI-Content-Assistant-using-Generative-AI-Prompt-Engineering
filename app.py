"""
app.py
-------
Streamlit UI for the Content Assistant.

This file is intentionally "thin": it collects user input, delegates prompt
construction to prompts.py, delegates the actual LLM call to llm_client.py,
and uses utils.py for validation/export. No prompt text or API logic lives here.
"""

from __future__ import annotations

import streamlit as st

from llm_client import get_default_client
from prompts import (
    FORMAT_GUIDANCE,
    LENGTH_GUIDANCE,
    TONE_GUIDANCE,
    get_template,
)
from utils import (
    build_filename,
    estimate_max_output_tokens,
    prepare_download_bytes,
    validate_generate_input,
    validate_text_input,
)

st.set_page_config(page_title="Content Assistant", page_icon="✍️", layout="wide")

# ---------------------------------------------------------------------------
# Cached client so we don't re-instantiate the API client on every rerun
# ---------------------------------------------------------------------------


@st.cache_resource
def load_client():
    return get_default_client()


def get_client_safely():
    """Load the LLM client, surfacing a friendly error if the API key is missing."""
    try:
        return load_client()
    except ValueError as e:
        st.error(str(e))
        st.stop()


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------

st.title("✍️ Content Assistant")
st.caption("Generate, summarize, and rewrite content using customizable, parameterized prompt templates.")

task = st.sidebar.radio("Choose a task", ["Generate", "Summarize", "Rewrite"])

st.sidebar.markdown("---")
st.sidebar.subheader("Content Controls")

tone = st.sidebar.selectbox("Tone", list(TONE_GUIDANCE.keys()), index=4)
output_format = st.sidebar.selectbox("Style / Format", list(FORMAT_GUIDANCE.keys()))
length = st.sidebar.selectbox("Length", list(LENGTH_GUIDANCE.keys()), index=1)

audience = None
if task == "Rewrite":
    audience = st.sidebar.text_input("Target audience", value="general readers")

st.sidebar.markdown("---")
st.sidebar.caption("Model: `claude-sonnet-4-5`")

# ---------------------------------------------------------------------------
# Task-specific input area
# ---------------------------------------------------------------------------

if task == "Generate":
    st.subheader("Generate new content")
    user_input = st.text_area(
        "Topic / brief",
        placeholder="e.g. A product launch announcement for a new eco-friendly water bottle",
        height=120,
    )
else:
    label = "Text to summarize" if task == "Summarize" else "Text to rewrite"
    st.subheader(f"{task} existing text")
    user_input = st.text_area(label, placeholder="Paste your text here...", height=220)

run_button = st.button("🚀 Run", type="primary")

# ---------------------------------------------------------------------------
# Build the prompt (always shown/available for transparency, even before running)
# ---------------------------------------------------------------------------


def build_prompts():
    """Construct the system + user prompt for the current task and UI selections."""
    template = get_template(task)

    format_instruction = FORMAT_GUIDANCE[output_format]
    length_instruction = LENGTH_GUIDANCE[length]
    tone_instruction = TONE_GUIDANCE[tone]

    if task == "Generate":
        user_prompt = template.build_user_prompt(
            topic=user_input.strip(),
            tone=tone_instruction,
            format_instruction=format_instruction,
            length_instruction=length_instruction,
        )
    elif task == "Summarize":
        user_prompt = template.build_user_prompt(
            source_text=user_input.strip(),
            format_instruction=format_instruction,
            length_instruction=length_instruction,
        )
    else:  # Rewrite
        user_prompt = template.build_user_prompt(
            source_text=user_input.strip(),
            tone=tone_instruction,
            audience=audience or "general readers",
            format_instruction=format_instruction,
            length_instruction=length_instruction,
        )

    return template.system_instruction, user_prompt


# ---------------------------------------------------------------------------
# Run the task
# ---------------------------------------------------------------------------

if run_button:
    # Step 1: Validate input
    if task == "Generate":
        validation = validate_generate_input(user_input)
    else:
        validation = validate_text_input(user_input, task_name=task)

    if not validation.is_valid:
        st.warning(validation.error_message)
        st.stop()

    # Step 2: Build prompts
    system_prompt, user_prompt = build_prompts()

    # Step 3: Call the LLM
    client = get_client_safely()
    with st.spinner("Generating..."):
        response = client.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=estimate_max_output_tokens(length),
            temperature=0.7,
        )

    # Step 4: Handle result
    if not response.success:
        st.error(f"⚠️ {response.error_message}")
    else:
        st.session_state["last_output"] = response.text
        st.session_state["last_system_prompt"] = system_prompt
        st.session_state["last_user_prompt"] = user_prompt
        st.session_state["last_tokens"] = (response.input_tokens, response.output_tokens)

# ---------------------------------------------------------------------------
# Display output
# ---------------------------------------------------------------------------

if "last_output" in st.session_state:
    st.markdown("---")
    st.subheader("Output")
    st.text_area("Result", value=st.session_state["last_output"], height=300, label_visibility="collapsed")

    col1, col2 = st.columns([1, 3])
    with col1:
        st.download_button(
            "⬇️ Download as .txt",
            data=prepare_download_bytes(st.session_state["last_output"]),
            file_name=build_filename(task),
            mime="text/plain",
        )
    with col2:
        st.code(st.session_state["last_output"], language=None)  # gives Streamlit's built-in copy icon

    in_tok, out_tok = st.session_state.get("last_tokens", (None, None))
    if in_tok is not None:
        st.caption(f"Tokens used — input: {in_tok}, output: {out_tok}")

    with st.expander("🔍 View Prompt (system + user prompt sent to the LLM)"):
        st.markdown("**System prompt:**")
        st.code(st.session_state["last_system_prompt"], language="text")
        st.markdown("**User prompt:**")
        st.code(st.session_state["last_user_prompt"], language="text")

elif not run_button:
    st.info("Fill in your content and controls, then click **Run** to generate output.")
