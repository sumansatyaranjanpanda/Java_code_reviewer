# core/clients.py
import os
import time
import traceback
from typing import Any, Dict, Optional

from config.settings import GROQ_API_KEY

USE_STUB = os.getenv("USE_STUB", "false").lower() in ("1", "true", "yes")
RETRY_ATTEMPTS = int(os.getenv("LLM_RETRIES", "3"))
RETRY_BACKOFF = float(os.getenv("LLM_BACKOFF", "1.0"))

def invoke_stub(prompt: str, max_tokens: int = 1500, temperature: float = 0.0) -> Dict[str, Any]:
    return {"content": f"[stub] preview: {prompt[:200]}"}

_llm_client = None
if not USE_STUB:
    try:
        from langchain_groq import ChatGroq
        
        GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        try:
            _llm_client = ChatGroq(model=GROQ_MODEL, api_key=GROQ_API_KEY)
        except Exception:
            try:
                _llm_client = ChatGroq(model=GROQ_MODEL)
            except Exception as e:
                print("ChatGroq constructor failed:", e)
                _llm_client = None
    except Exception as e:
        print("langchain_groq import failed:", e)
        _llm_client = None

def _extract_text(resp: Any) -> Optional[str]:
    """
    Normalize common LangChain/Groq response shapes to a plain string.
    """
    if resp is None:
        return None

    # direct string
    if isinstance(resp, str):
        return resp

    # dict-like
    if isinstance(resp, dict):
        for k in ("content", "text", "output", "result"):
            v = resp.get(k)
            if isinstance(v, str) and v.strip():
                return v
        # choices/generations
        if "choices" in resp and resp["choices"]:
            ch = resp["choices"][0]
            if isinstance(ch, dict):
                for k in ("text", "content"):
                    v = ch.get(k)
                    if isinstance(v, str) and v.strip():
                        return v

    # LangChain: .generations
    if hasattr(resp, "generations"):
        gens = getattr(resp, "generations")
        try:
            first = gens[0][0] if isinstance(gens[0], (list, tuple)) else gens[0]
            if hasattr(first, "text") and isinstance(first.text, str) and first.text.strip():
                return first.text
            # message.content pattern
            if hasattr(first, "message") and hasattr(first.message, "content"):
                c = getattr(first.message, "content")
                if isinstance(c, str) and c.strip():
                    return c
        except Exception:
            pass

    # fallback attributes
    if hasattr(resp, "text") and isinstance(getattr(resp, "text"), str):
        return getattr(resp, "text")
    if hasattr(resp, "content") and isinstance(getattr(resp, "content"), str):
        return getattr(resp, "content")

    # final fallback to stringifying the object
    try:
        s = str(resp)
        return s
    except Exception:
        return None
    


def invoke(prompt: str, max_tokens: int = 1500, temperature: float = 0.0) -> Dict[str, Any]:
    """
    Simple, single-pattern LLM invoke using ChatGroq.invoke(input=...).
    Returns: {"content": "<string reply>"}
    """
    if USE_STUB:
        return invoke_stub(prompt, max_tokens=max_tokens, temperature=temperature)

    if _llm_client is None:
        msg = "LLM client not initialized. Set USE_STUB=true or configure GROQ_API_KEY/GROQ_MODEL."
        print(msg)
        return {"content": f"[llm-invoke-failed] {msg}"}

    attempt = 0
    last_exc = None
    while attempt < RETRY_ATTEMPTS:
        try:
            # IMPORTANT: call the single method pattern your ChatGroq supports
            resp = _llm_client.invoke(input=prompt, max_tokens=max_tokens, temperature=temperature)
            text = _extract_text(resp)
            
            if text is None:
                # if extraction failed, at least return stringified resp
                return {"content": f"[llm-invoke-failed] Could not extract text. raw: {str(resp)[:1000]}"}
            return {"content": text}
        except Exception as e:
            last_exc = e
            wait = RETRY_BACKOFF * (2 ** attempt)
            print(f"Invoke attempt {attempt+1} failed: {e}. Retrying in {wait}s")
            traceback.print_exc()
            time.sleep(wait)
            attempt += 1

    return {"content": f"[llm-invoke-failed] All retries failed. Last error: {last_exc}"}
