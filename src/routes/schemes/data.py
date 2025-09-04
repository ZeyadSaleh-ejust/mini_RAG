from pydantic import BaseModel # pydantic is responsible for data Validation
from typing import Optional

class ProcessRequest(BaseModel):  # as type json
    file_id: str = None # as optional for field_id if there is not value then it will be None
    chunk_size: Optional[int] = 100
    overlap_size: Optional[int] = 20
    do_reset: Optional[int] = 0
    