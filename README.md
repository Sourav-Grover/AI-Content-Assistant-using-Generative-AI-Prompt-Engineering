# 🚀 AI Content Assistant

### ✍️ A Prompt-Engineered Generative AI System for Tone-Controlled Content Generation, Summarization & Rewriting

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Anthropic Claude](https://img.shields.io/badge/Claude-Sonnet--4.5-8A63D2?style=for-the-badge&logo=anthropic&logoColor=white)](https://www.anthropic.com/)
[![Prompt Engineering](https://img.shields.io/badge/Prompt-Engineering-orange?style=for-the-badge)](#-prompt-engineering-deep-dive)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](#-license)
[![Status](https://img.shields.io/badge/Status-Complete-brightgreen?style=for-the-badge)](#-testing--evaluation)

---

## 📌 Overview

Writers, marketers, and founders lose hours re-explaining tone, audience, and format to generic AI chatbots — and get back inconsistent text with zero visibility into what the model was actually told to do.

**AI Content Assistant** solves this with a single Streamlit application that **generates**, **summarizes**, and **rewrites** content on demand, driven entirely by a **parameterized prompt template engine** rather than hardcoded strings. Every request is assembled at runtime from reusable `PromptTemplate` objects, and the exact system + user prompt sent to Claude is exposed to the user for full transparency — turning prompt engineering from a black box into a visible, explainable part of the product.

This project was built to demonstrate applied, production-grade **Generative AI** and **Prompt Engineering** skills — not a notebook demo, but a fully working, modular application.

---

## ✨ Key Features

✅ **Generate** — original content from a short topic/brief (blog intros, emails, social posts, product descriptions)

✅ **Summarize** — condense long text into short / medium / long summaries or bullet points

✅ **Rewrite** — change tone or audience while strictly preserving meaning and facts

✅ **Parameterized Prompt Engine** — `{tone}`, `{audience}`, `{format_instruction}`, `{length_instruction}` placeholders filled dynamically, never one-off strings

✅ **Full Prompt Transparency** — a "View Prompt" expander shows the exact system + user prompt sent to the model, every single run

✅ **Role / Persona Prompting** — every template gives Claude a specific expert persona with explicit behavioral rules

✅ **Few-Shot Anchoring** — the rewrite template ships a worked before/after example to lock in correct tone-transfer behavior

✅ **Explicit Output Constraints** — every template forbids preamble, meta-commentary, and fact invention

✅ **Guardrails** — input length & emptiness validated *before* any API call is made

✅ **Graceful Error Handling** — automatic retry on rate limits, friendly messages on connection/API failures

✅ **Export** — download any output as `.txt`, or copy instantly via the built-in code-block copy icon

✅ **Swappable LLM Layer** — an abstract `LLMClient` interface means a new provider can be added without touching the UI or the prompts

---

## 🛠️ Tech Stack

### Core

- Python 3.10+
- Streamlit — full interactive UI in pure Python, no separate frontend
- Anthropic Claude API (`claude-sonnet-4-5`) via the official `anthropic` SDK

### Supporting Libraries

- `python-dotenv` — environment/config management, keeps the API key out of source code
- `dataclasses` (stdlib) — type-safe response & validation models
- `abc.ABC` (stdlib) — the LLM provider abstraction layer

| Layer | Technology | Why it was chosen |
|---|---|---|
| UI | Streamlit | Ships a full interactive app in pure Python, ideal for fast, clean prompt-driven tools |
| LLM | Claude `claude-sonnet-4-5` | Strong instruction-following — essential for constraint-heavy, parameterized prompts |
| SDK | `anthropic` | Typed exceptions (`RateLimitError`, `APIStatusError`) enable precise, non-generic error handling |
| Config | `python-dotenv` | Keeps secrets out of source control entirely |
| Architecture | `abc.ABC` | Lets a new LLM provider be added with zero changes to the UI or prompt layer |

---

## 🏗️ System Architecture

The application is a linear, five-stage pipeline. Every request passes through validation *before* it costs a single API token.

```
 User Input (Streamlit UI)
          │
          ▼
 Input Validation           ← utils.py  (guardrails: empty / too short / too long)
          │
          ▼
 Prompt Template Engine     ← prompts.py  (role + task + constraints + few-shot)
          │
          ▼
 LLM Client (Abstraction)   ← llm_client.py  (provider-agnostic, retry logic)
          │
          ▼
 Anthropic Claude API       ← claude-sonnet-4-5
          │
          ▼
 Normalized Response  →  rendered in UI + exact prompt shown + exportable as .txt
```

<p align="center">
  <img src="docs/architecture.jpg" alt="AI Content Assistant architecture diagram" width="800">
</p>

<p align="center"><em>Figure: request/response pipeline from UI input to Claude API and back</em></p>

---

## 🧠 Prompt Engineering Deep Dive

This is the core skill this project demonstrates. All prompt logic lives in `prompts.py`, fully decoupled from the UI and the API transport layer.

| Technique | How it's implemented |
|---|---|
| **Role / Persona Prompting** | Each template's `system_instruction` assigns Claude a specific expert persona (content writer, professional editor, tone-transfer editor) with explicit behavioral rules |
| **Parameterized Templates** | Every template is a `PromptTemplate` dataclass filled via `.format(**kwargs)` at runtime — `{tone}`, `{audience}`, `{format_instruction}`, `{length_instruction}` — never duplicated per request |
| **Centralized Control Mappings** | `TONE_GUIDANCE`, `FORMAT_GUIDANCE`, `LENGTH_GUIDANCE` dictionaries are the single source of truth read by both the UI dropdowns and the prompt templates, so they can never drift out of sync |
| **Explicit Output Constraints** | Every template has a dedicated `output_constraints` block forbidding preamble, meta-commentary, and invented facts |
| **Few-Shot Examples** | The Rewrite template includes a worked before/after pair to anchor exactly what a correct tone transformation looks like |
| **Separation of Concerns** | Prompts, UI, and API transport are three independent modules — prompts can be iterated on or unit-tested without touching Streamlit or the SDK call |
| **Prompt Transparency** | The "View Prompt" expander renders the *exact* system + user prompt sent for every request — a debugging aid and a demonstration of prompt construction |
| **Guardrails at the Prompt Boundary** | `utils.py` validates and bounds all input *before* a template is ever built, so malformed or oversized requests never reach the API |

```python
def build_user_prompt(self, **kwargs) -> str:
    filled_task = self.task_template.format(**kwargs)
    parts = [filled_task]
    if self.output_constraints:
        parts.append(f"\nOutput constraints:\n{self.output_constraints}")
    if self.few_shot_example:
        parts.append(f"\nExample of the expected style:\n{self.few_shot_example}")
    return "\n".join(parts)
```

---

## 🔑 Core Functionalities

### Generation Module
- Topic/brief → original content
- Tone, Format, and Length fully configurable per request
- Zero-preamble output enforced via explicit constraints

### Summarization Module
- Condenses long text into Short / Medium / Long summaries or bullet points
- Strictly grounded — never adds facts absent from the source text

### Rewrite Module
- Tone and audience transformation with **meaning preservation guaranteed**
- Few-shot example anchors correct before/after behavior

### Transparency & Export Module
- Live "View Prompt" expander (system + user prompt, per request)
- One-click `.txt` download
- Built-in copy-from-code-block

---

## 🖼️ Screenshots

<table>
<tr>
<td width="50%">
<img src="docs/screenshots/01-generate.jpg" alt="Generate tab">
<p align="center"><b>Generate</b> — tone, format & length controls with live output</p>
</td>
<td width="50%">
<img src="docs/screenshots/02-summarize-prompt-view.jpg" alt="Summarize tab with View Prompt open">
<p align="center"><b>Summarize</b> — "View Prompt" expander showing the exact prompt sent to Claude</p>
</td>
</tr>
<tr>
<td width="50%">
<img src="docs/screenshots/03-rewrite.jpg" alt="Rewrite tab before after">
<p align="center"><b>Rewrite</b> — casual message transformed into a formal executive email</p>
</td>
<td width="50%">
<img src="docs/screenshots/04-download.jpg" alt="Download as txt in action">
<p align="center"><b>Export</b> — one-click download as <code>.txt</code> with confirmation</p>
</td>
</tr>
</table>

---

## 📊 Testing & Evaluation

### Functional Testing — 10 / 10 Passed

| # | Test Case | Type | Result |
|---|---|---|---|
| 1 | Generate a persuasive blog intro from a topic brief | Generate | ✅ PASS |
| 2 | Summarize a 600-word article to a short summary | Summarize | ✅ PASS |
| 3 | Rewrite a casual message into a formal executive email | Rewrite | ✅ PASS |
| 4 | Submit Generate with an empty topic field | Validation | ✅ PASS |
| 5 | Submit an over-length topic (500-char limit) | Validation | ✅ PASS |
| 6 | Submit under-length text to Summarize | Validation | ✅ PASS |
| 7 | Run with `ANTHROPIC_API_KEY` missing | Error Handling | ✅ PASS |
| 8 | Simulate a rate-limit response | Error Handling | ✅ PASS |
| 9 | Disconnect network mid-request | Error Handling | ✅ PASS |
| 10 | Switch Format dropdown mid-session | UI State | ✅ PASS |

### Evaluation Metrics (30 sampled requests, 10 per task)

| Metric | Result | Target |
|---|---|---|
| Output-constraint compliance | **10 / 10** | 10 / 10 |
| Tone consistency (full response) | **9 / 10** | ≥ 9 / 10 |
| Meaning preservation (Rewrite) | **10 / 10** | 10 / 10 |
| Average response latency | **3.1 s** | < 5 s |
| Validation catch rate | **100%** | 100% |

---

## 📂 Project Structure

```
ai-content-assistant/
│
├── app.py                # Streamlit UI — thin layer, zero business logic
├── prompts.py             # Prompt template engine (the core prompt engineering work)
├── llm_client.py            # LLM provider abstraction (Anthropic implementation, swappable)
├── utils.py                 # Validation, guardrails, export helpers
├── requirements.txt
├── .env.example
├── .gitignore
├── docs/
│   ├── architecture.jpg
│   └── screenshots/
│       ├── 01-generate.jpg
│       ├── 02-summarize-prompt-view.jpg
│       ├── 03-rewrite.jpg
│       └── 04-download.jpg
└── README.md
```

---

## 🚀 Installation

```bash
git clone https://github.com/Sourav-Grover/ai-content-assistant.git
cd ai-content-assistant

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

---

## ⚙️ Environment Variables

Create a `.env` file in the project root (or copy `.env.example`):

```
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

Get a key from the [Anthropic Console](https://console.anthropic.com/).

---

## ▶️ Run the App

```bash
streamlit run app.py
```

Open the local URL Streamlit prints — usually `http://localhost:8501`.

---

## 🔌 Swapping LLM Providers

`llm_client.py` defines an abstract `LLMClient` base class with a single `generate()` method. `AnthropicClient` is the current implementation. To add a new provider, implement a new subclass of `LLMClient` and update `get_default_client()` — **no changes needed anywhere else in the app.**

---

## 🛡️ Error Handling

| Scenario | Behavior |
|---|---|
| Empty or missing input | Inline validation warning, no API call made |
| Input exceeding length limits | Inline validation warning, no API call made |
| Missing API key | Friendly startup error with setup instructions |
| Rate limit hit | One automatic retry with backoff, then a friendly message |
| Network/connection failure | Friendly error shown, app remains usable |
| Unexpected API error | Caught and surfaced without crashing the app |

---

## 📈 Engineering Highlights

- Designed a fully parameterized `PromptTemplate` dataclass so prompt logic scales to new tasks without code duplication.
- Centralized all tone/format/length control text into shared dictionaries, eliminating drift between UI and prompt wording.
- Built an abstract `LLMClient` interface enabling provider swaps with zero UI changes.
- Implemented guardrails at the prompt boundary — input is validated *before* it can cost a single API token.
- Added automatic single-retry rate-limit handling with normalized error responses across every failure mode.
- Exposed full prompt transparency to the end user as a first-class UI feature, not a debug afterthought.

---

## 🔮 Future Improvements

- 🧵 Conversation memory for iterative multi-turn refinement of a single output
- 📄 Direct file upload (PDF/DOCX) as summarization input
- 🔁 Lightweight automatic self-check pass (tone/length verification before returning output)
- 🔄 Multiple LLM providers behind the existing interface for side-by-side comparison
- 🌐 Multilingual generation, summarization, and rewriting

---

## 🎯 Learning Outcomes

- Practical, production-style prompt engineering: role prompting, parameterization, output constraints, few-shot anchoring
- Designing a clean abstraction layer for swappable LLM providers
- Building guardrails and graceful error handling around a live LLM API
- Structuring a Generative AI application with proper separation of concerns
- Shipping prompt transparency as a genuine UX feature, not just a debug tool

---

## 👨‍💻 Author

**Sourav Grover**

B.Tech Computer Science & Engineering
Kalinga Institute of Industrial Technology (KIIT), Bhubaneswar

GitHub: [github.com/Sourav-Grover](https://github.com/Sourav-Grover)

---

## 📜 License

MIT — free to use, modify, and adapt.

---

⭐ If you found this project useful, consider giving it a star.
