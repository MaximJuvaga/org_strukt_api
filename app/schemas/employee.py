from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import date

class EmployeeCreate(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=200)
    position: str = Field(..., min_length=1, max_length=200)
    hired_at: Optional[date] = None

    @field_validator('full_name', 'position')
    @classmethod
    def trim_fields(cls, v):
        return v.strip() if v else v
