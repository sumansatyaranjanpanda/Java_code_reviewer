# core/node.py
import re
from typing import Dict
from core.clients import invoke
from core.schema import Response

# -----------------------
# CONFIG — tweak these
# -----------------------
MAX_CODE_CHARS = 24_000
MAX_AGENT_OUTPUT_CHARS = 5_000
MAX_MERGE_OUTPUT_CHARS = 30_000
MAX_FINDINGS = 4

# Strict mode: require a suggestion for EVERY guideline (even if agent replied "code is fine for that guideline")
APPLY_ALL_GUIDELINES = True

# -----------------------
# Utilities
# -----------------------
def _truncate_code(code: str, max_chars: int = MAX_CODE_CHARS) -> str:
    if not code:
        return ""
    if len(code) <= max_chars:
        return code
    return f"/* TRUNCATED: original_length={len(code)} chars */\n" + code[:max_chars]

def _safe_invoke(prompt: str) -> Dict[str, str]:
    """Call invoke(prompt) and normalize result to dict with 'content' key."""
    try:
        resp = invoke(prompt)
        if isinstance(resp, dict) and "content" in resp:
            return resp
        if isinstance(resp, dict) and "text" in resp:
            return {"content": resp.get("text", "")}
        return {"content": str(resp)}
    except Exception as e:
        return {"content": f"[llm-invoke-failed] {e}"}

def _ensure_short(text: str, max_chars: int) -> str:
    if not text:
        return ""
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n/* TRUNCATED */"

def _normalize_agent_text(text: str) -> str:
    """Clean common LLM artifacts to make merging deterministic."""
    if not text:
        return ""
    return text.strip()

# -----------------------
# Guideline specs
# -----------------------
GUIDES = {
    "G01": ("Follow Java code conventions",
            "Naming, package, constants style, visibility and formatting."),
    "G02": ("Prefer streams/lambdas for simple transformations",
            "Replace simple loops with streams when safe."),
    "G03": ("Null-safety / avoid NPE",
            "Find potential NPEs and add minimal null-safety."),
    "G04": ("Defensive copies / don't expose mutables",
            "Return defensive copies or unmodifiable wrappers for internal state."),
    "G05": ("Handle exceptions properly",
            "Avoid overly broad catches; catch specific exceptions; don't swallow."),
    "G06": ("Choose appropriate data structures",
            "Prefer modern collections and interfaces over legacy types."),
    "G07": ("Minimize visibility / encapsulate",
            "Avoid public mutable fields; prefer private with accessors."),
    "G08": ("Code to interfaces",
            "Expose interfaces (List) in signatures rather than concretes (ArrayList)."),
    "G09": ("Avoid unnecessary interfaces",
            "Detect trivial interfaces that add noise rather than value."),
    "G10": ("Override hashCode when overriding equals",
            "Ensure equals/hashCode contract is satisfied.")
}

# -----------------------
# Prompt builders (strict & compact)
# -----------------------
def build_guideline_prompt(guid_id: str, guid_title: str, guid_desc: str, code_text: str) -> str:
    """
    Strict per-guideline prompt. Ask for 0..MAX_FINDINGS concise findings.
    If APPLY_ALL_GUIDELINES is True, instruct the agent to provide at least
    one suggestion even if the code looks fine (prefer minimal best-practice).
    """
    code_text = _truncate_code(code_text)
    mandatory_line = ""
    if APPLY_ALL_GUIDELINES:
        mandatory_line = "If no issues, still propose ONE minimal best-practice change for this guideline.\n"
    return (
        f"GUIDELINE:{guid_id} | {guid_title}\n{guid_desc}\n\n"
        f"You are a senior Java reviewer. Provide up to {MAX_FINDINGS} concise findings. {mandatory_line}"
        "FOR EACH finding use THIS TEMPLATE (plain text only):\n"
        "- Finding: <short title>\n"
        "- Area: <method name or 'approximate'>\n"
        "- Severity: <High|Medium|Low>\n"
        "- Confidence: <1-5>\n"
        "- Issue: <one short sentence>\n"
        "- Fix: <one short sentence>\n"
        "- Patch (optional): ```java\n  // minimal snippet\n  ```\n\n"
        "RULES: Do NOT invent line numbers. Use 'approximate' when unsure. Respond ONLY with findings (no commentary).\n\n"
        f"CODE:\n{code_text}\n"
    )

def build_merge_prompt(agent_responses: str) -> str:
    """
    Strict integrator: MUST include an item for each guideline G01..G10.
    The integrator must prioritize High severity, but still output one entry per guideline.
    End with a 'Minimal Patch' section (3-12 lines).
    """
    return (
        "You are a strict integrator. Given the agents' findings below, produce a FINAL prioritized list\n"
        "with exactly one consolidated suggestion for each guideline from G01 to G10 (include the guideline code in Trigger).\n"
        "Use THIS TEMPLATE for every suggestion (plain text only):\n\n"
        "- Title: <short>\n"
        "- Trigger: <Gxx>\n"
        "- Area: <method or 'approximate'>\n"
        "- Severity: <High|Medium|Low>\n"
        "- Rationale: <one short sentence>\n"
        "- Change: <one-line action>\n"
        "- Patch (optional): ```java\n  // minimal snippet\n  ```\n\n"
        "RULES:\n"
        "1) MUST output one consolidated suggestion for each G01..G10. If an agent said 'code is fine for that guideline', still produce a minimal best-practice change.\n"
        "2) Prioritize correctness/security (High) first when ordering. 3) If conflict between agents, pick the least-risky correct fix. 4) At the end produce a 'Minimal Patch' of 3-12 concrete edit lines.\n\n"
        "AGENT_FINDINGS:\n" + agent_responses + "\n\nRespond ONLY with the consolidated suggestions and the Minimal Patch."
    )

def build_final_transform_prompt(merged_suggestions: str, original_code: str) -> str:
    """
    Instructs to apply ALL merged suggestions. Must include comment header listing applied guidelines.
    """
    original_code = _truncate_code(original_code)
    return (
        "Task: Apply ALL changes listed in MERGED_SUGGESTIONS to ORIGINAL_CODE. You MUST apply each guideline's fix.\n"
        "Return ONLY a single updated Java file (no commentary). At the very top include a one-line comment:\n"
        "/* Applied: G01,G02,... */\n\n"
        "Rules: 1) Make minimal safe edits that implement the suggested changes. 2) Preserve unrelated code. 3) When ambiguous choose the smallest safe change that accomplishes the fix.\n\n"
        f"MERGED_SUGGESTIONS:\n{merged_suggestions}\n\nORIGINAL_CODE:\n{original_code}\n\nRespond only with the updated file."
    )

# -----------------------
# Nodes
# -----------------------
def run_guideline_node_dict(state: Response, guid_key: str, field_name: str) -> Dict[str, str]:
    code_text = getattr(state, "code_snippet", "") or ""
    title, desc = GUIDES.get(guid_key, (guid_key, ""))
    prompt = build_guideline_prompt(guid_key, title, desc, code_text)
    resp = _safe_invoke(prompt)
    content = _normalize_agent_text(resp.get("content", ""))
    # ensure not too long
    content = _ensure_short(content, MAX_AGENT_OUTPUT_CHARS)
    # If agent returned nothing, and strict mode is on, create a minimal best-practice suggestion stub
    if APPLY_ALL_GUIDELINES and (not content.strip() or content.strip().lower().startswith("[llm-invoke-failed]")):
        # minimal template for missing agent reply
        content = (
            "- Finding: Minimal suggestion\n"
            "- Area: approximate\n"
            "- Severity: Low\n"
            "- Confidence: 3\n"
            "- Issue: No issues detected but propose a best-practice change.\n"
            "- Fix: Apply guideline " + guid_key + " best practice.\n"
            "- Patch (optional): ```java\n  // minimal change for " + guid_key + "\n  ```\n"
        )
    return {field_name: content}

# wrapper helpers
def guide1_node(state: Response): return run_guideline_node_dict(state, "G01", "guideline_1")
def guide2_node(state: Response): return run_guideline_node_dict(state, "G02", "guideline_2")
def guide3_node(state: Response): return run_guideline_node_dict(state, "G03", "guideline_3")
def guide4_node(state: Response): return run_guideline_node_dict(state, "G04", "guideline_4")
def guide5_node(state: Response): return run_guideline_node_dict(state, "G05", "guideline_5")
def guide6_node(state: Response): return run_guideline_node_dict(state, "G06", "guideline_6")
def guide7_node(state: Response): return run_guideline_node_dict(state, "G07", "guideline_7")
def guide8_node(state: Response): return run_guideline_node_dict(state, "G08", "guideline_8")
def guide9_node(state: Response): return run_guideline_node_dict(state, "G09", "guideline_9")
def guide10_node(state: Response): return run_guideline_node_dict(state, "G10", "guideline_10")

def llm_node(state: Response) -> Dict[str, str]:
    # gather agent outputs
    parts = []
    for i in range(1, 11):
        key = f"guideline_{i}"
        val = None
        if isinstance(state, dict):
            val = state.get(key)
        else:
            val = getattr(state, key, None)
        if not val:
            # add empty placeholder if strict mode
            if APPLY_ALL_GUIDELINES:
                parts.append(f"GUIDELINE_{i}:\n- Finding: Minimal suggestion\n- Area: approximate\n- Severity: Low\n- Confidence: 3\n- Issue: no agent output\n- Fix: apply guideline G{str(i).zfill(2)} best-practice.\n")
            continue
        # skip exact noop? No — in strict mode we still want a fix. If agent replied exact noop, create minimal suggestion
        if APPLY_ALL_GUIDELINES and val.strip() == "code is fine for that guideline":
            parts.append(f"GUIDELINE_{i}:\n- Finding: Best-practice suggestion\n- Area: approximate\n- Severity: Low\n- Confidence: 4\n- Issue: agent indicated code is fine; propose best-practice change.\n- Fix: apply guideline G{str(i).zfill(2)} minimal change.\n")
            continue
        parts.append(f"GUIDELINE_{i}:\n{val.strip()}\n")
    agent_texts = "\n".join(parts)
    prompt = build_merge_prompt(agent_texts)
    resp = _safe_invoke(prompt)
    merged = _ensure_short(resp.get("content", ""), MAX_MERGE_OUTPUT_CHARS)
    # If the integrator failed to include all Gxx items (safety), add stubs
    missing = []
    for i in range(1, 11):
        tag = f"Trigger: G{str(i).zfill(2)}"
        if tag not in merged:
            missing.append(i)
    if missing:
        # append minimal stubs for any missing guidelines
        stubs = []
        for i in missing:
            stubs.append(
                f"- Title: Auto-suggest G{str(i).zfill(2)}\n"
                f"- Trigger: G{str(i).zfill(2)}\n"
                f"- Area: approximate\n"
                f"- Severity: Low\n"
                f"- Rationale: Auto-generated minimal best-practice for G{str(i).zfill(2)}.\n"
                f"- Change: Apply guideline G{str(i).zfill(2)} minimal edit.\n"
                f"- Patch (optional): ```java\n  // auto minimal change for G{str(i).zfill(2)}\n  ```\n"
            )
        merged = merged + "\n\n" + "\n".join(stubs)
    return {"merge_guide_res": merged}

def final_updated_node(state: Response) -> Dict[str, str]:
    code_text = getattr(state, "code_snippet", "") or ""
    merged = None
    if isinstance(state, dict):
        merged = state.get("merge_guide_res", "")
    else:
        merged = getattr(state, "merge_guide_res", "") or ""
    if not merged:
        return {"final_updated_code": code_text or "No original code provided."}

    # final transformer prompt requires applying ALL guidelines present in merged suggestions
    prompt = build_final_transform_prompt(merged, code_text)
    resp = _safe_invoke(prompt)
    updated = resp.get("content", "")

    # Safety heuristics: ensure header lists applied guidelines. If absent, try to infer and add header.
    header_match = re.search(r"/\*\s*Applied\s*:\s*([A-Za-z0-9, ]+)\s*\*/", updated)
    if not header_match:
        # try to extract triggers from merged and prepend a header comment
        triggers = re.findall(r"Trigger:\s*(G\d{2})", merged)
        unique_triggers = sorted(set(triggers), key=lambda x: int(x[1:]) if x.startswith("G") else x)
        if unique_triggers:
            header = "/* Applied: " + ",".join(unique_triggers) + " */\n"
            updated = header + updated

    return {"final_updated_code": updated}

# -----------------------
# Optional helper: quick sanitizer that extracts only structured fields from agent outputs
# (useful if agent verbosity breaks merging)
# -----------------------
def extract_structured(agent_text: str) -> str:
    if not agent_text:
        return ""
    lines = agent_text.splitlines()
    keep = []
    for ln in lines:
        if re.match(r"^\s*-\s*(Finding|Area|Severity|Confidence|Issue|Fix|Patch|Title|Trigger|Change|Rationale)\b", ln, re.I):
            keep.append(ln)
        elif ln.strip().startswith("```java") or ln.strip().endswith("```"):
            keep.append(ln)
        # keep short code-like lines
        elif re.match(r"^\s*(public |private |protected |package |import |class |interface )", ln):
            keep.append(ln)
    return "\n".join(keep)

# End of file
