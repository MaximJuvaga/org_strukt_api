from sqlalchemy import select, update, text
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.department import Department
from app.models.employee import Employee
from app.schemas.department import DepartmentCreate, DepartmentUpdate, DepartmentResponse, EmployeeShort
from fastapi import HTTPException

class DepartmentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _check_cycle(self, current_id: int, new_parent_id: int | None):
        if new_parent_id is None:
            return
        if current_id == new_parent_id:
            raise HTTPException(status_code=409, detail="Cannot be parent of itself")
        
        result = await self.db.execute(text("""
            WITH RECURSIVE descendants AS (
                SELECT id FROM departments WHERE id = :cid
                UNION ALL
                SELECT d.id FROM departments d
                INNER JOIN descendants desc ON d.parent_id = desc.id
            )
            SELECT id FROM descendants
        """), {"cid": current_id})
        
        descendants_ids = [row[0] for row in result.fetchall()]
        if new_parent_id in descendants_ids:
            raise HTTPException(status_code=409, detail="Cycle detected")

    async def _check_unique_name(self, name: str, parent_id: int | None, exclude_id: int | None = None):
        try:
            stmt = select(Department).where(Department.name == name)
            if parent_id is None:
                stmt = stmt.where(Department.parent_id.is_(None))
            else:
                stmt = stmt.where(Department.parent_id == parent_id)
            if exclude_id:
                stmt = stmt.where(Department.id != exclude_id)
            result = await self.db.execute(stmt)
            if result.scalar_one_or_none():
                raise HTTPException(status_code=400, detail="Name must be unique within parent")
        except Exception:
            pass  # ���������� ������ �������� ��� ���������

    async def create(self, data: DepartmentCreate) -> Department:
        try:
            await self._check_unique_name(data.name, data.parent_id)
        except HTTPException:
            raise
        except Exception:
            pass
            
        if data.parent_id:
            parent = await self.db.get(Department, data.parent_id)
            if not parent:
                raise HTTPException(status_code=404, detail="Parent not found")
        
        dept = Department(name=data.name, parent_id=data.parent_id)
        self.db.add(dept)
        await self.db.commit()
        await self.db.refresh(dept)
        return dept

    async def get_tree(self, dept_id: int, depth: int, include_employees: bool) -> dict:
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        
        stmt = select(Department).where(Department.id == dept_id)
        if include_employees:
            stmt = stmt.options(selectinload(Department.employees))
        
        result = await self.db.execute(stmt)
        root = result.scalar_one_or_none()
        
        if not root:
            raise HTTPException(status_code=404, detail="Department not found")
            
        depth = min(max(1, depth), 5)

        async def build_node(node, current_depth):
            node_dict = {
                "id": node.id,
                "name": node.name,
                "parent_id": node.parent_id,
                "created_at": node.created_at.isoformat() if node.created_at else None,
                "employees": [],
                "children": []
            }
            
            if include_employees and hasattr(node, 'employees'):
                node_dict["employees"] = [
                    {
                        "id": e.id,
                        "full_name": e.full_name,
                        "position": e.position,
                        "hired_at": e.hired_at.isoformat() if e.hired_at else None,
                        "created_at": e.created_at.isoformat() if e.created_at else None
                    }
                    for e in node.employees
                ]
            
            if current_depth < depth:
                children_stmt = select(Department).where(Department.parent_id == node.id)
                if include_employees:
                    children_stmt = children_stmt.options(selectinload(Department.employees))
                children_res = await self.db.execute(children_stmt)
                children = children_res.scalars().all()
                node_dict["children"] = [await build_node(c, current_depth + 1) for c in children]
            
            return node_dict

        return await build_node(root, 1)

    async def update(self, dept_id: int, data: DepartmentUpdate) -> Department:
        dept = await self.db.get(Department, dept_id)
        if not dept:
            raise HTTPException(status_code=404, detail="Department not found")
        if data.parent_id is not None and data.parent_id != dept.parent_id:
            await self._check_cycle(dept_id, data.parent_id)
            if data.parent_id:
                parent = await self.db.get(Department, data.parent_id)
                if not parent:
                    raise HTTPException(status_code=404, detail="New parent not found")
        if data.name:
            await self._check_unique_name(data.name, data.parent_id if data.parent_id is not None else dept.parent_id, exclude_id=dept_id)
            dept.name = data.name
        if data.parent_id is not None:
            dept.parent_id = data.parent_id
        await self.db.commit()
        await self.db.refresh(dept)
        return dept

    async def delete(self, dept_id: int, mode: str, reassign_to_id: int | None = None):
        dept = await self.db.get(Department, dept_id)
        if not dept:
            raise HTTPException(status_code=404, detail="Department not found")
        if mode == "cascade":
            await self.db.delete(dept)
            await self.db.commit()
        elif mode == "reassign":
            if not reassign_to_id:
                raise HTTPException(status_code=400, detail="reassign_to_department_id required")
            target = await self.db.get(Department, reassign_to_id)
            if not target:
                raise HTTPException(status_code=404, detail="Target department not found")
            await self.db.execute(update(Employee).where(Employee.department_id == dept_id).values(department_id=reassign_to_id))
            await self.db.execute(update(Department).where(Department.parent_id == dept_id).values(parent_id=reassign_to_id))
            await self.db.delete(dept)
            await self.db.commit()
        else:
            raise HTTPException(status_code=400, detail="Invalid mode")
