from pydantic import BaseModel
from typing import Optional


class LoginResultDTO(BaseModel):
    success: bool
    user: Optional[object] = None
    error_code: Optional[str] = None
