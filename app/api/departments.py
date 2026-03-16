from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services.department_service import DepartmentService
from app.services.employee_service import EmployeeService
from app.schemas.department import DepartmentCreate, DepartmentUpdate
from app.schemas.employee import EmployeeCreate
from typing import Optional

router = APIRouter(prefix="/departments", tags=["Departments"])

@router.post("/", status_code=201)
async def create_department(
    data: DepartmentCreate,  # ?? Имя параметра + тип
    db: AsyncSession = Depends(get_db)
):
    service = DepartmentService(db)
    dept = await service.create(data)
    return {
        "id": dept.id,
        "name": dept.name,
        "parent_id": dept.parent_id,
        "created_at": dept.created_at.isoformat() if dept.created_at else None
    }

@router.get("/{dept_id}")
async def get_department(
    dept_id: int,
    depth: int = Query(1, ge=1, le=5),
    include_employees: bool = Query(True),
    db: AsyncSession = Depends(get_db)
):
    service = DepartmentService(db)
    return await service.get_tree(dept_id, depth, include_employees)

@router.patch("/{dept_id}")
async def update_department(
    dept_id: int,
    data: DepartmentUpdate,  # ?? Имя параметра + тип
    db: AsyncSession = Depends(get_db)
):
    service = DepartmentService(db)
    dept = await service.update(dept_id, data)
    return {
        "id": dept.id,
        "name": dept.name,
        "parent_id": dept.parent_id,
        "created_at": dept.created_at.isoformat() if dept.created_at else None
    }

@router.delete("/{dept_id}", status_code=204)
async def delete_department(
    dept_id: int,
    mode: str = Query(..., pattern="^(cascade|reassign)$"),
    reassign_to_department_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    service = DepartmentService(db)
    await service.delete(dept_id, mode, reassign_to_department_id)
    return None

@router.post("/{dept_id}/employees/", status_code=201)
async def create_employee(
    dept_id: int,
    data: EmployeeCreate,  # ?? Имя параметра + тип
    db: AsyncSession = Depends(get_db)
):
    service = EmployeeService(db)
    emp = await service.create(dept_id, data)
    return {
        "id": emp.id,
        "full_name": emp.full_name,
        "position": emp.position,
        "hired_at": emp.hired_at.isoformat() if emp.hired_at else None,
        "created_at": emp.created_at.isoformat() if emp.created_at else None
    }
