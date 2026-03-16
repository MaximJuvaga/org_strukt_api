from sqlalchemy.ext.asyncio import AsyncSession
from app.models.employee import Employee
from app.models.department import Department
from app.schemas.employee import EmployeeCreate
from fastapi import HTTPException

class EmployeeService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, dept_id: int, data: EmployeeCreate) -> Employee:
        dept = await self.db.get(Department, dept_id)
        if not dept:
            raise HTTPException(status_code=404, detail="Department not found")
        emp = Employee(department_id=dept_id, full_name=data.full_name, position=data.position, hired_at=data.hired_at)
        self.db.add(emp)
        await self.db.commit()
        await self.db.refresh(emp)
        return emp
