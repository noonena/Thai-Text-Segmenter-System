from fastapi import APIRouter, HTTPException
from schemas.role import RoleCreate, RoleUpdate
from utils.database import role_db

router = APIRouter()

# ======================
# GET all roles
# ======================
@router.get("")
def get_roles():
    try:
        roles = role_db.get_all_roles()
        return {
            "success": True,
            "roles": roles,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ======================
# CREATE role
# ======================
@router.post("")
def create_role(data: RoleCreate):
    try:
        role_db.create_role(
            data.name,
            data.description or ""
        )
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ======================
# UPDATE role
# ======================
@router.put("/{role_id}")
def update_role(role_id: str, data: RoleUpdate):
    try:
        role_db.update_role(
            role_id,
            data.name,
            data.description or ""
        )
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ======================
# DELETE role
# ======================
@router.delete("/{role_id}")
def delete_role(role_id: str):
    try:
        role_db.delete_role(role_id)
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
