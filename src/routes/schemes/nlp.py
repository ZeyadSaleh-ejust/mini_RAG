from pydantic import BaseModel # pydantic is responsible for data Validation
from typing import Optional, List

class PushRequest(BaseModel):
    do_reset: Optional[int] = 0

class SearchRequest(BaseModel):
    text: str
    limit: Optional[int] = 5
    chat_history: Optional[List[dict]] = []