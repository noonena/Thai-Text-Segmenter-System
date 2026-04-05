from fastapi import APIRouter, HTTPException, Cookie, Response
from schemas.user import UserLogin
import sqlite3
from typing import Optional
from utils.database import (
    DB_PATH, verify_password, create_session, delete_session, get_session_user,
    is_account_locked, record_failed_attempt, clear_failed_attempts, MAX_LOGIN_ATTEMPTS,
)

router = APIRouter()


@router.post("/login")
def login_user(data: UserLogin, response: Response):
    if is_account_locked(data.username):
        return {"success": False, "message": "Account is locked. Please contact an administrator."}

    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()

            cur.execute("""
                SELECT u.id, u.username, u.name, r.name as role, u.password_hash
                FROM users u
                JOIN roles r ON u.role_id = r.id
                WHERE u.username = ?
            """, (data.username,))

            row = cur.fetchone()
            user = row if (row and verify_password(data.password, row["password_hash"])) else None

            if not user:
                attempts = record_failed_attempt(data.username)
                remaining = MAX_LOGIN_ATTEMPTS - attempts
                if remaining <= 0:
                    return {"success": False, "message": "Account is locked. Please contact an administrator."}
                return {"success": False, "message": f"Invalid username or password. {remaining} attempt(s) remaining."}

            clear_failed_attempts(data.username)
            user_dict = {k: v for k, v in dict(user).items() if k != "password_hash"}
            token = create_session(user_dict["id"])

            response.set_cookie(
                key="session",
                value=token,
                httponly=True,
                samesite="lax",
                max_age=3600,
                secure=False,
            )

            return {"success": True, "user": user_dict}

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Authentication error")


@router.post("/logout")
def logout_user(response: Response, session: Optional[str] = Cookie(None)):
    if session:
        delete_session(session)
    response.delete_cookie(key="session")
    return {"success": True, "message": "Logged out"}


@router.get("/verify")
def verify_token(session: Optional[str] = Cookie(None)):
    if not session:
        return {"success": False}
    user = get_session_user(session)
    if not user:
        return {"success": False}
    return {"success": True, "user": user}
