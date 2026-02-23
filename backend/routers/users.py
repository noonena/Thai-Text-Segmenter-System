from fastapi import APIRouter, HTTPException
from schemas.user import UserCreate, UserUpdate
from utils.database import user_db

router = APIRouter()

# ======================
# GET all users
# ======================
@router.get("")
def get_users():
    try:
        users = user_db.get_all_users()

        # Normalize DB → frontend format
        formatted = []
        for u in users:
            formatted.append({
                "id": u["id"],
                "username": u["username"],
                "name": u["name"],
                "role": u["role"],              # from JOIN
                "createdAt": u["created_at"],
                "lastLogin": u["last_login"],
            })

        return {
            "success": True,
            "users": formatted,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ======================
# CREATE user
# ======================
@router.post("")
def create_user(data: UserCreate):
    try:
        user_db.create_user(data.dict())
        return {"success": True}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ======================
# UPDATE user
# ======================
@router.put("/{user_id}")
def update_user(user_id: str, data: UserUpdate):
    try:
        user_db.update_user(
            user_id,
            data.dict(exclude_none=True)
        )
        return {"success": True}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ======================
# DELETE user
# ======================
@router.delete("/{user_id}")
def delete_user(user_id: str):
    try:
        user_db.delete_user(user_id)
        return {"success": True}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
