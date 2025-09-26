# core/schema.py
from typing import Optional
from pydantic import BaseModel

class Response(BaseModel):
    # original input
    code_snippet: Optional[str] = None

    # guideline outputs: plain strings (chat-like)
    guideline_1: Optional[str] = None
    guideline_2: Optional[str] = None
    guideline_3: Optional[str] = None
    guideline_4: Optional[str] = None
    guideline_5: Optional[str] = None
    guideline_6: Optional[str] = None
    guideline_7: Optional[str] = None
    guideline_8: Optional[str] = None
    guideline_9: Optional[str] = None
    guideline_10: Optional[str] = None

    # merger and final outputs (plain strings)
    merge_guide_res: Optional[str] = None
    final_updated_code: Optional[str] = None
