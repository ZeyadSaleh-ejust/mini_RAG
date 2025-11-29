from pydantic import BaseModel # pydantic is responsible for data Validation
from typing import Optional

class PushRequest(BaseModel):
    do_reset: Optional[int] = 0