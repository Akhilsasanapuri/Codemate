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
