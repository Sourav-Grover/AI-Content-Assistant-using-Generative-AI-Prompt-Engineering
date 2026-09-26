# Content Assistant

A content assistant that **generates**, **summarizes**, and **rewrites** text using
parameterized, reusable prompt templates to control tone, style, and format — built with
Streamlit and the Anthropic Claude API.

![screenshot-placeholder](docs/screenshot-main.png)
*(Add a screenshot of the running app here before publishing)*

## Features

- **Generate** — Produce new content from a short topic/brief (blog intros, emails,
  social posts, product descriptions, etc.)
- **Summarize** — Condense long text into short/medium/long summaries or bullet points
- **Rewrite** — Rephrase existing text for a different tone or audience while preserving
  meaning
- **Prompt transparency** — A "View Prompt" expander shows the exact system + user prompt
  sent to the model for every request
- **User controls** — Tone, Style/Format, and Length dropdowns dynamically fill prompt
  templates (no hardcoded prompt strings per request)
- **Export** — Download any output as a `.txt` file, or copy via the built-in code-block
  copy icon
- **Guardrails** — Input length validation, empty-input handling, and graceful API error
  handling (rate limits, connection errors, API errors)

## Tech Stack

| Layer      | Technology                                                  |
|------------|--------------------------------------------------------------|
| UI         | Streamlit                                                    |
| LLM        | Anthropic Claude (`claude-sonnet-4-5`) via the `anthropic` SDK |
| Config     | `python-dotenv`                                              |
| Language   | Python 3.10+                                                 |

## Project Structure

```
ai-content-assistant/
├── app.py            # Streamlit UI — thin layer, no business logic
├── prompts.py         # Prompt template engine (the core prompt engineering work)
├── llm_client.py       # LLM provider abstraction (Anthropic implementation + swappable interface)
├── utils.py            # Validation, guardrails, export helpers
├── requirements.txt
├── .env.example
└── README.md
```

## Setup & Run

1. **Clone and enter the project**
   ```bash
   git clone <your-repo-url>
   cd ai-content-assistant
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate   # Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure your API key**
   ```bash
   cp .env.example .env
   # then edit .env and paste your Anthropic API key
   ```

5. **Run the app**
   ```bash
   streamlit run app.py
   ```

6. Open the local URL Streamlit prints (usually `http://localhost:8501`).

## How Prompt Engineering Was Applied

The core prompt engineering work lives in `prompts.py`. Key techniques used:

- **Role / persona prompting** — Each template's `system_instruction` assigns the model
  a specific expert persona (content writer, professional editor, tone-transfer editor)
  with explicit behavioral rules, which measurably improves output quality and
  consistency versus a generic prompt.
- **Parameterized templates, not hardcoded strings** — Every template is a
  `PromptTemplate` object with `{placeholders}` (`{tone}`, `{audience}`,
  `{format_instruction}`, `{length_instruction}`) filled dynamically at request time from
  centralized mapping dictionaries (`TONE_GUIDANCE`, `FORMAT_GUIDANCE`,
  `LENGTH_GUIDANCE`). This keeps the UI controls and prompt text always in sync and
  avoids prompt duplication.
- **Explicit output constraints** — Each template has a dedicated `output_constraints`
  block (e.g. "output only the content, no preamble", "preserve only facts present in the
  source") to reduce hallucination and eliminate boilerplate model chatter like "Here is
  your content:".
- **Few-shot examples** — The rewrite template includes a worked before/after example to
  anchor exactly what a tone transformation should look like while preserving meaning.
- **Separation of prompt logic from application logic** — Prompts live entirely in
  `prompts.py`, decoupled from both the UI (`app.py`) and the API transport layer
  (`llm_client.py`), so prompts can be iterated on, tested, or compared independently.
- **Prompt transparency for the end user** — The "View Prompt" expander in the UI exposes
  the exact system and user prompt sent for every request, which is both a debugging aid
  and a way to demonstrate the underlying prompt construction.
- **Guardrails around the prompt boundary** — `utils.py` validates and bounds all input
  before it ever reaches a template (min/max length checks), preventing malformed or
  excessively large requests from being sent to the API.

## Swapping LLM Providers

`llm_client.py` defines an abstract `LLMClient` base class with a single `generate()`
method. `AnthropicClient` is the current implementation. To add a new provider, implement
a new subclass of `LLMClient` and update `get_default_client()` — no changes needed
anywhere else in the app.

## Error Handling

- Empty or missing input → inline validation warning, no API call made
- Input exceeding length limits → inline validation warning, no API call made
- Missing API key → friendly startup error with setup instructions
- Rate limit hit → automatic single retry with backoff, then a friendly error message
- Network/connection failure → friendly error message, app remains usable
- Unexpected API errors → caught and surfaced without crashing the app

## License

MIT — free to use and adapt.
