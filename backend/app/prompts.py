"""Prompt templates. Each returns (system, user) tuple of strings.

All templates instruct the model to respond with strict JSON matching the
schema described in the prompt. Pairs with response_format=json_object.
"""
from typing import Optional

from .schemas import ExplainErrorRequest, GenerateCodeRequest, ReviewCodeRequest


_JSON_RULE = (
    "Respond with ONLY a single JSON object. No prose, no markdown fences, "
    "no comments. All string fields must be plain text."
)


def explain_error_prompt(req: ExplainErrorRequest) -> tuple[str, str]:
    system = (
        "You are CodeMate, a senior engineer who explains programming errors "
        "in clear, beginner-friendly language. "
        + _JSON_RULE
        + " The JSON must have keys: explanation (string), root_cause (string), "
        "suggested_fix (string), corrected_code (string or null), language (string or null)."
    )
    lang_line = f"Language: {req.language}\n" if req.language else ""
    code_block = f"\nCode:\n```\n{req.code}\n```\n" if req.code else ""
    user = (
        f"{lang_line}"
        f"Error:\n```\n{req.error_message}\n```"
        f"{code_block}\n"
        "Explain the error, identify the root cause, suggest a fix, and if "
        "code was provided return a corrected version in corrected_code."
    )
    return system, user


def generate_code_prompt(req: GenerateCodeRequest) -> tuple[str, str]:
    system = (
        "You are CodeMate, a senior engineer who writes correct, idiomatic, "
        "well-commented code. "
        + _JSON_RULE
        + " The JSON must have keys: code (string), language (string), "
        "explanation (string), assumptions (array of strings)."
    )
    lang_line = f"Target language: {req.language}\n" if req.language else "Pick the most appropriate language.\n"
    fw_line = f"Framework: {req.framework}\n" if req.framework else ""
    user = (
        f"{lang_line}{fw_line}"
        f"Task:\n{req.prompt}\n\n"
        "Return runnable code. List any assumptions you made."
    )
    return system, user


def review_code_prompt(req: ReviewCodeRequest) -> tuple[str, str]:
    system = (
        "You are CodeMate, a meticulous senior code reviewer. Find real bugs, "
        "inefficiencies, security issues, and style problems. Be specific. "
        + _JSON_RULE
        + " The JSON must have keys: summary (string), issues (array of objects "
        "with keys: type [bug|inefficiency|style|security|other], severity "
        "[info|warning|error], description [string], line [integer or null]), "
        "improved_code (string or null), language (string or null)."
    )
    lang_line = f"Language: {req.language}\n" if req.language else ""
    user = (
        f"{lang_line}"
        f"Review the following code:\n```\n{req.code}\n```\n"
        "Return a concise summary and an issues array. Provide an improved_code "
        "version if meaningful improvements are possible."
    )
    return system, user


# -----------------------------------------------------------------------------
# Ask Codebase (RAG)
# -----------------------------------------------------------------------------
def ask_codebase_prompt(question: str, excerpts: list[dict]) -> tuple[str, str]:
    """excerpts: [{file_path, line_start, line_end, text}, ...]"""
    system = (
        "You are CodeMate, an AI assistant that answers questions about a user's codebase. "
        "You will be given a question plus a set of retrieved code/text excerpts from the project, "
        "each tagged with its file path and line range. "
        "Answer ONLY based on the provided excerpts; do not invent files, functions, or behavior. "
        "If the excerpts don't contain enough information to answer, say so honestly. "
        "Reference file paths in your answer when relevant. "
        + _JSON_RULE
        + " The JSON must have keys: answer (string, may use markdown), "
        "used_sources (array of strings — file paths from the excerpts you actually used)."
    )
    blocks = []
    for i, ex in enumerate(excerpts, start=1):
        header = f"--- Excerpt {i}: {ex['file_path']} (lines {ex['line_start']}-{ex['line_end']}) ---"
        blocks.append(f"{header}\n{ex['text']}")
    context = "\n\n".join(blocks) if blocks else "(no excerpts retrieved)"
    user = (
        f"Question:\n{question}\n\n"
        f"Retrieved excerpts from the project:\n\n{context}\n"
    )
    return system, user
