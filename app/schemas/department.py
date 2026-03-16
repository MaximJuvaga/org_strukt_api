from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional, List, Any
from datetime import datetime

class DepartmentBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    parent_id: Optional[int] = None

    @field_validator('name')
    @classmethod
    def trim_name(cls, v):
        return v.strip() if v else v

class DepartmentCreate(DepartmentBase):
    pass

class DepartmentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    parent_id: Optional[int] = None

    @field_validator('name')
    @classmethod
    def trim_name(cls, v):
        return v.strip() if v else v

class EmployeeShort(BaseModel):
    id: int
    full_name: str
    position: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class DepartmentResponse(BaseModel):
    id: int
    name: str
    parent_id: Optional[int]
    created_at: datetime
    employees: Optional[List[EmployeeShort]] = None
    children: Optional[List[Any]] = None
    model_config = ConfigDict(from_attributes=True)
