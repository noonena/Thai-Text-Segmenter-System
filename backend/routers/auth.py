from fastapi import APIRouter, HTTPException
from schemas.user import UserLogin
import sqlite3
from utils.database import DB_PATH, hash_password

router = APIRouter()

@router.post("/login")
def login_user(data: UserLogin):
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()

            cur.execute("""
                SELECT u.id, u.username, u.name, r.name as role
                FROM users u
                JOIN roles r ON u.role_id = r.id
                WHERE u.username = ? AND u.password_hash = ?
            """, (data.username, hash_password(data.password)))

            user = cur.fetchone()
            if not user:
                return {"success": False, "message": "Invalid username or password"}

            return {
                "success": True,
                "user": dict(user),
                "message": "Login successful"
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
