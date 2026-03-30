from fastapi import APIRouter, HTTPException, Depends
from schemas.role import RoleCreate, RoleUpdate
from utils.database import role_db, require_admin

router = APIRouter()

# ======================
# GET all roles (admin only)
# ======================
@router.get("")
def get_roles(_user: dict = Depends(require_admin)):
    try:
        roles = role_db.get_all_roles()
        return {
            "success": True,
            "roles": roles,
        }
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to retrieve roles")


# ======================
# CREATE role (admin only)
# ======================
@router.post("")
def create_role(data: RoleCreate, _user: dict = Depends(require_admin)):
    try:
        role_db.create_role(
            data.name,
            data.description or ""
        )
        return {"success": True}
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to create role")


# ======================
# UPDATE role (admin only)
# ======================
@router.put("/{role_id}")
def update_role(role_id: str, data: RoleUpdate, _user: dict = Depends(require_admin)):
    try:
        role_db.update_role(
            role_id,
            data.name,
            data.description or ""
        )
        return {"success": True}
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to update role")


# ======================
# DELETE role (admin only)
# ======================
@router.delete("/{role_id}")
def delete_role(role_id: str, _user: dict = Depends(require_admin)):
    try:
        role_db.delete_role(role_id)
        return {"success": True}
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to delete role")
