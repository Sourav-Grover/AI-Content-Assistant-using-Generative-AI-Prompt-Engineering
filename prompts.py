"""
prompts.py
-----------
The prompt engineering core of this project.

Design principles demonstrated here:
    1. Role prompting        - every template opens with a clear system persona.
    2. Parameterization      - templates use {variables} filled dynamically, never
                                hardcoded strings per request.
    3. Output constraints    - each template explicitly constrains structure/length.
    4. Few-shot guidance     - the rewrite template includes a worked example to
                                anchor tone transformation behavior.
    5. Separation of concerns- prompt text lives here, completely decoupled from
                                UI code and API-calling code.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass
class PromptTemplate:
    """
    A structured, reusable prompt template.

    Attributes:
        name: Human-readable template name.
        system_instruction: Role + behavioral rules sent as the system prompt.
        task_template: The user-turn template string with {placeholders}.
        output_constraints: Explicit formatting/length rules injected into the task.
        few_shot_example: Optional worked example to anchor model behavior.
    """
    name: str
    system_instruction: str
    task_template: str
    output_constraints: str = ""
    few_shot_example: str = ""

    def build_user_prompt(self, **kwargs) -> str:
        """
        Fill the task template with runtime variables and append constraints
        and (if present) the few-shot example.

        Raises:
            KeyError: if a required template variable is missing from kwargs.
        """
        filled_task = self.task_template.format(**kwargs)

        parts = [filled_task]
        if self.output_constraints:
            parts.append(f"\nOutput constraints:\n{self.output_constraints}")
        if self.few_shot_example:
            parts.append(f"\nExample of the expected style:\n{self.few_shot_example}")

        return "\n".join(parts)


# ---------------------------------------------------------------------------
# LENGTH / TONE / FORMAT MAPPINGS
# Centralizing these means the UI dropdowns and the prompt text always agree.
# ---------------------------------------------------------------------------

LENGTH_GUIDANCE: Dict[str, str] = {
    "Short": "Keep it concise: roughly 50-100 words.",
    "Medium": "Aim for a moderate length: roughly 150-250 words.",
    "Long": "Provide a thorough, detailed response: roughly 350-500 words.",
}

FORMAT_GUIDANCE: Dict[str, str] = {
    "Paragraph": "Write in flowing paragraph form.",
    "Bullet points": "Structure the output as a clean bulleted list.",
    "Email": "Format as a complete email, including a subject line, greeting, body, and sign-off.",
    "Social media post": "Format as a short, scroll-stopping social media post. Include 1-3 relevant hashtags at the end.",
    "Blog": "Format with a compelling headline and short, skimmable paragraphs or subheadings.",
}

TONE_GUIDANCE: Dict[str, str] = {
    "Formal": "formal and professional, avoiding contractions and casual phrasing",
    "Casual": "casual, relaxed, and conversational, like talking to a friend",
    "Persuasive": "persuasive and compelling, using rhetorical techniques to drive action",
    "Friendly": "warm, friendly, and approachable",
    "Professional": "polished, business-appropriate, and confident",
}


# ---------------------------------------------------------------------------
# TEMPLATE 1: GENERATION
# ---------------------------------------------------------------------------

GENERATE_TEMPLATE = PromptTemplate(
    name="Content Generation",
    system_instruction=(
        "You are an expert content writer and copywriter with years of experience "
        "crafting marketing copy, blog posts, emails, and social media content. "
        "You write clear, engaging, original content tailored precisely to the "
        "requested tone, audience, and format. You never include meta-commentary "
        "like 'Here is your content:' — you output only the requested content itself."
    ),
    task_template=(
        "Write original content on the following topic/brief:\n\n"
        "\"{topic}\"\n\n"
        "Tone: the writing should be {tone}.\n"
        "Format: {format_instruction}\n"
        "Length: {length_instruction}"
    ),
    output_constraints=(
        "- Output ONLY the final content — no preamble, no explanations, no labels.\n"
        "- Do not repeat these instructions back.\n"
        "- Stay strictly on-topic and factually plausible; do not invent statistics "
        "or claims presented as verified facts.\n"
        "- Match the requested tone consistently throughout, not just in the opening line."
    ),
)


# ---------------------------------------------------------------------------
# TEMPLATE 2: SUMMARIZATION
# ---------------------------------------------------------------------------

SUMMARIZE_TEMPLATE = PromptTemplate(
    name="Text Summarization",
    system_instruction=(
        "You are a professional editor specializing in summarization. Your job is "
        "to distill long text into its most essential points without losing "
        "critical meaning, nuance, or key facts. You are precise, neutral, and "
        "never insert opinions or information that isn't present in the source text."
    ),
    task_template=(
        "Summarize the following text.\n\n"
        "Source text:\n"
        "\"\"\"\n{source_text}\n\"\"\"\n\n"
        "Summary format: {format_instruction}\n"
        "Summary length: {length_instruction}"
    ),
    output_constraints=(
        "- Preserve only information present in the source text — do not add "
        "outside facts or speculation.\n"
        "- Do not editorialize or insert personal opinions.\n"
        "- If the source text is too short or unclear to summarize meaningfully, "
        "state that plainly instead of fabricating content.\n"
        "- Output ONLY the summary — no preamble like 'Here is a summary:'."
    ),
)


# ---------------------------------------------------------------------------
# TEMPLATE 3: REWRITE / TONE TRANSFER
# ---------------------------------------------------------------------------

REWRITE_TEMPLATE = PromptTemplate(
    name="Rewrite / Tone Transfer",
    system_instruction=(
        "You are a skilled editor who rewrites text to fit a new tone, audience, "
        "or format while strictly preserving the original meaning, facts, and "
        "intent. You never add new claims, never remove essential information, "
        "and never change the message — only how it is expressed."
    ),
    task_template=(
        "Rewrite the following text so that it is {tone}, targeted at this "
        "audience: {audience}.\n\n"
        "Original text:\n"
        "\"\"\"\n{source_text}\n\"\"\"\n\n"
        "Format: {format_instruction}\n"
        "Length: {length_instruction}"
    ),
    output_constraints=(
        "- Preserve the original meaning and all key facts exactly.\n"
        "- Do not add new information or opinions not present in the original.\n"
        "- Fully commit to the new tone — don't just swap a few words.\n"
        "- Output ONLY the rewritten text — no preamble or explanation."
    ),
    few_shot_example=(
        "Original (casual): \"Hey team, quick heads up — we're gonna be late on the "
        "launch, probably a week or so. Sorry for the trouble!\"\n"
        "Rewritten (formal, for executives): \"I am writing to inform you that the "
        "product launch will be delayed by approximately one week. We apologize for "
        "any inconvenience this may cause and appreciate your understanding.\"\n"
        "(Notice: same facts and intent, fully different register.)"
    ),
)


# ---------------------------------------------------------------------------
# Registry so the UI/app layer can look templates up by task name
# ---------------------------------------------------------------------------

TEMPLATE_REGISTRY: Dict[str, PromptTemplate] = {
    "Generate": GENERATE_TEMPLATE,
    "Summarize": SUMMARIZE_TEMPLATE,
    "Rewrite": REWRITE_TEMPLATE,
}


def get_template(task: str) -> PromptTemplate:
    """Look up a PromptTemplate by task name. Raises ValueError if not found."""
    if task not in TEMPLATE_REGISTRY:
        raise ValueError(f"Unknown task '{task}'. Valid tasks: {list(TEMPLATE_REGISTRY)}")
    return TEMPLATE_REGISTRY[task]
