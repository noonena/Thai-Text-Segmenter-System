from fastapi import APIRouter, HTTPException, Depends
import sqlite3
from schemas.user import UserCreate, UserUpdate
from utils.database import user_db, require_auth, require_admin, unlock_account, DB_PATH

router = APIRouter()

# ======================
# GET all users (admin only)
# ======================
@router.get("")
def get_users(_user: dict = Depends(require_admin)):
    try:
        users = user_db.get_all_users()

        formatted = []
        for u in users:
            formatted.append({
                "id": u["id"],
                "username": u["username"],
                "name": u["name"],
                "role": u["role"],
                "createdAt": u["created_at"],
                "lastLogin": u["last_login"],
            })

        return {
            "success": True,
            "users": formatted,
        }

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to retrieve users")


# ======================
# CREATE user (admin only)
# ======================
@router.post("")
def create_user(data: UserCreate, _user: dict = Depends(require_admin)):
    try:
        user_db.create_user(data.dict())
        return {"success": True}

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to create user")


# ======================
# UPDATE user (admin only)
# ======================
@router.put("/{user_id}")
def update_user(user_id: str, data: UserUpdate, current_user: dict = Depends(require_admin)):
    try:
        user_db.update_user(
            user_id,
            data.dict(exclude_none=True)
        )
        return {"success": True}

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to update user")


# ======================
# UNLOCK user (admin only)
# ======================
@router.post("/{user_id}/unlock")
def unlock_user(user_id: str, _user: dict = Depends(require_admin)):
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cur = conn.execute("SELECT username FROM users WHERE id = ?", (user_id,))
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="User not found")
            username = row[0]

        if not unlock_account(username):
            raise HTTPException(status_code=404, detail="User not found")
        return {"success": True}
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to unlock user")


# ======================
# DELETE user (admin only, cannot delete self)
# ======================
@router.delete("/{user_id}")
def delete_user(user_id: str, current_user: dict = Depends(require_admin)):
    if current_user["id"] == user_id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")

    try:
        user_db.delete_user(user_id)
        return {"success": True}

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to delete user")
