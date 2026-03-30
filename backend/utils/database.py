# backend/utils/database.py
import sqlite3
import os
import uuid
import bcrypt
from datetime import datetime
from typing import Optional, Dict, Any, List
from fastapi import Depends, HTTPException, status, Cookie

# Ensure database directory exists
DB_DIR = os.path.join(os.path.dirname(__file__), "..", "database")
DB_PATH = os.path.join(DB_DIR, "users.db")


# ======================
# Helpers
# ======================

def hash_password(password: str) -> str:
    """Hash a password using bcrypt with automatic salt generation."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against its bcrypt hash. Also handles legacy SHA-256 hashes (64 hex chars)."""
    # Detect legacy SHA-256 hash (64-char hex string)
    if len(password_hash) == 64 and all(c in '0123456789abcdef' for c in password_hash):
        import hashlib
        return hashlib.sha256(password.encode()).hexdigest() == password_hash
    try:
        return bcrypt.checkpw(password.encode(), password_hash.encode())
    except Exception:
        return False


_ALLOWED_ID_TABLES = {"users", "roles"}

def generate_daily_id(conn: sqlite3.Connection, table: str) -> str:
    if table not in _ALLOWED_ID_TABLES:
        raise ValueError(f"Invalid table name: {table}")
    cur = conn.cursor()

    cur.execute(
        f"SELECT id FROM {table} ORDER BY id DESC LIMIT 1"
    )

    row = cur.fetchone()
    if row:
        # Extract the numeric part and increment
        last_id = row[0]
        if last_id.isdigit():
            seq = int(last_id) + 1
        else:
            # If ID format is different, extract numeric part
            numeric_part = ''.join(filter(str.isdigit, last_id))
            seq = int(numeric_part) + 1 if numeric_part else 1
    else:
        seq = 1
    
    return f"{seq:03d}"


# ======================
# USER DATABASE
# ======================

class UserDatabase:
    def __init__(self):
        self.db_path = DB_PATH

    def get_all_users(self) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()

            cur.execute("""
                SELECT
                    u.id,
                    u.username,
                    u.name,
                    r.name AS role,
                    u.created_at,
                    u.last_login
                FROM users u
                JOIN roles r ON u.role_id = r.id
                ORDER BY u.created_at DESC
            """)

            return [dict(row) for row in cur.fetchall()]

    def create_user(self, data: Dict[str, Any]) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            user_id = generate_daily_id(conn, "users")
            conn.execute("""
                INSERT INTO users (id, username, password_hash, role_id, name)
                VALUES (?, ?, ?, ?, ?)
            """, (
                user_id,
                data["username"],
                hash_password(data["password"]),
                data["role_id"],
                data["name"],
            ))
            conn.commit()
        return True

    def update_user(self, user_id: str, data: Dict[str, Any]) -> bool:
        fields = []
        values = []

        if "username" in data:
            fields.append("username = ?")
            values.append(data["username"])
        if "name" in data:
            fields.append("name = ?")
            values.append(data["name"])
        if "role_id" in data:
            fields.append("role_id = ?")
            values.append(data["role_id"])
        if "password" in data:
            fields.append("password_hash = ?")
            values.append(hash_password(data["password"]))

        if not fields:
            return False

        values.append(user_id)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                f"UPDATE users SET {', '.join(fields)} WHERE id = ?",
                values,
            )
            conn.commit()

        return True

    def delete_user(self, user_id: str) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
            conn.commit()
        return True


# ======================
# ROLE DATABASE (CRUD)
# ======================

class RoleDatabase:
    def __init__(self):
        self.db_path = DB_PATH

    def get_all_roles(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("SELECT * FROM roles ORDER BY name")
            return [dict(r) for r in cur.fetchall()]

    def _is_system_role(self, conn: sqlite3.Connection, role_id: str) -> bool:
        cur = conn.cursor()
        cur.execute("SELECT is_system FROM roles WHERE id = ?", (role_id,))
        row = cur.fetchone()
        return bool(row and row[0])

    def create_role(self, name: str, description: str):
        with sqlite3.connect(self.db_path) as conn:
            # Block names that conflict with existing system roles
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM roles WHERE name = ? AND is_system = 1", (name,))
            if cur.fetchone()[0] > 0:
                raise ValueError(f"'{name}' is a reserved system role name")
            role_id = generate_daily_id(conn, "roles")
            conn.execute(
                "INSERT INTO roles (id, name, description, is_system) VALUES (?, ?, ?, 0)",
                (role_id, name, description),
            )
            conn.commit()

    def update_role(self, role_id: str, name: str, description: str):
        with sqlite3.connect(self.db_path) as conn:
            if self._is_system_role(conn, role_id):
                raise ValueError("System roles cannot be renamed")
            conn.execute(
                "UPDATE roles SET name = ?, description = ? WHERE id = ?",
                (name, description, role_id),
            )
            conn.commit()

    def delete_role(self, role_id: str):
        with sqlite3.connect(self.db_path) as conn:
            if self._is_system_role(conn, role_id):
                raise ValueError("System roles cannot be deleted")
            # safety: block delete if users exist
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM users WHERE role_id = ?", (role_id,))
            if cur.fetchone()[0] > 0:
                raise ValueError("Role is in use by existing users")

            conn.execute("DELETE FROM roles WHERE id = ?", (role_id,))
            conn.commit()



# ======================
# LOGIN ATTEMPT HELPERS
# ======================

MAX_LOGIN_ATTEMPTS = 3

def record_failed_attempt(username: str) -> int:
    """Increment failed attempts. Lock account if limit reached. Returns attempts count."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "UPDATE users SET login_attempts = login_attempts + 1 WHERE username = ?",
            (username,)
        )
        cur = conn.execute(
            "SELECT login_attempts FROM users WHERE username = ?", (username,)
        )
        row = cur.fetchone()
        attempts = row[0] if row else 0
        if attempts >= MAX_LOGIN_ATTEMPTS:
            conn.execute("UPDATE users SET is_locked = 1 WHERE username = ?", (username,))
        conn.commit()
    return attempts

def clear_failed_attempts(username: str) -> None:
    """Reset attempt counter on successful login."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "UPDATE users SET login_attempts = 0 WHERE username = ?", (username,)
        )
        conn.commit()

def is_account_locked(username: str) -> bool:
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute(
            "SELECT is_locked FROM users WHERE username = ?", (username,)
        )
        row = cur.fetchone()
        return bool(row and row[0])

def unlock_account(username: str) -> bool:
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute("SELECT id FROM users WHERE username = ?", (username,))
        if not cur.fetchone():
            return False
        conn.execute(
            "UPDATE users SET is_locked = 0, login_attempts = 0 WHERE username = ?",
            (username,)
        )
        conn.commit()
    return True


# Initialize database
def init_database():
    """Initialize database tables and default data"""
    os.makedirs(DB_DIR, exist_ok=True)
    
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        
        # Create roles table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS roles (
                id TEXT PRIMARY KEY,
                name TEXT UNIQUE NOT NULL,
                description TEXT,
                is_system INTEGER NOT NULL DEFAULT 0
            )
        ''')

        # Add is_system column to existing databases that predate this schema
        try:
            cursor.execute("ALTER TABLE roles ADD COLUMN is_system INTEGER NOT NULL DEFAULT 0")
        except sqlite3.OperationalError:
            pass  # Column already exists

        # Add login attempt tracking columns
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN login_attempts INTEGER NOT NULL DEFAULT 0")
        except sqlite3.OperationalError:
            pass
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN is_locked INTEGER NOT NULL DEFAULT 0")
        except sqlite3.OperationalError:
            pass
        
        # Create users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role_id TEXT NOT NULL,
                name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                FOREIGN KEY (role_id) REFERENCES roles (id)
            )
        ''')

        # Create sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                token TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')

        # Clear all sessions on startup so old tokens are invalidated on restart
        cursor.execute("DELETE FROM sessions")

        # Create default roles if they don't exist
        cursor.execute("SELECT COUNT(*) FROM roles")
        role_count = cursor.fetchone()[0]
        
        if role_count == 0:
            # Create default roles
            cursor.execute("INSERT INTO roles (id, name, description, is_system) VALUES (?, ?, ?, 1)",
                         ("001", "admin", "System administrator with full access"))
            cursor.execute("INSERT INTO roles (id, name, description, is_system) VALUES (?, ?, ?, 0)",
                         ("002", "user", "Regular user with limited access"))
            
            # Create default admin user
            admin_password_hash = hash_password("admin123")
            cursor.execute('''
                INSERT INTO users (id, username, password_hash, role_id, name)
                VALUES (?, ?, ?, ?, ?)
            ''', ("001", "admin", admin_password_hash, "001", "System Administrator"))

            print("[WARNING] Default admin user created with password 'admin123'. Change this immediately!")
        # Ensure existing system roles are flagged (migration for pre-existing DBs)
        cursor.execute("UPDATE roles SET is_system = 1 WHERE name = 'admin' AND is_system = 0")
        cursor.execute("UPDATE roles SET is_system = 0 WHERE name = 'user' AND is_system = 1")

        # Migrate any legacy SHA-256 password hashes to bcrypt
        # Since we cannot recover plaintext from SHA-256, reset to "changeme" and warn the admin.
        RESET_PASSWORD = "changeme"
        cursor.execute("SELECT id, username, password_hash FROM users")
        for row_id, username, pw_hash in cursor.fetchall():
            if len(pw_hash) == 64 and all(c in '0123456789abcdef' for c in pw_hash):
                new_hash = hash_password(RESET_PASSWORD)
                cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?", (new_hash, row_id))
                print(f"[SECURITY] Migrated legacy SHA-256 hash for '{username}'. Temporary password set to: '{RESET_PASSWORD}'. Please change it immediately!")

        conn.commit()

# ======================
# SESSION HELPERS
# ======================

SESSION_DURATION = 1800  # 1 hour in seconds


def create_session(user_id: str) -> str:
    """Create a new session token for a user and return the token."""
    from datetime import timedelta
    token = str(uuid.uuid4())
    expires_at = datetime.utcnow() + timedelta(seconds=SESSION_DURATION)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT INTO sessions (token, user_id, expires_at) VALUES (?, ?, ?)",
            (token, user_id, expires_at.isoformat()),
        )
        conn.commit()
    return token


def get_session_user(token: str) -> Optional[Dict[str, Any]]:
    """Return user dict for a valid token, or None if expired/not found."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        # Delete expired sessions first
        cur.execute(
            "DELETE FROM sessions WHERE expires_at <= ?",
            (datetime.utcnow().isoformat(),),
        )
        conn.commit()

        cur.execute(
            """
            SELECT u.id, u.username, u.name, r.name as role
            FROM sessions s
            JOIN users u ON s.user_id = u.id
            JOIN roles r ON u.role_id = r.id
            WHERE s.token = ?
            """,
            (token,),
        )
        row = cur.fetchone()
        return dict(row) if row else None


def delete_session(token: str) -> None:
    """Invalidate a session token."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
        conn.commit()


def require_auth(session: Optional[str] = Cookie(None)) -> dict:
    """FastAPI dependency — validate session cookie and return the authenticated user dict."""
    if session is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    user = get_session_user(session)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired session")
    return user


def require_admin(user: dict = Depends(require_auth)) -> dict:
    """FastAPI dependency — require the authenticated user to have the admin role."""
    if user.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return user


# Initialize database on import
init_database()

user_db = UserDatabase()
role_db = RoleDatabase()
