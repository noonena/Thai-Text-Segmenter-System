# # Global instance
# user_db = UserDatabase()
# backend/utils/database.py
# dont forget to pip install fastapi uvicorn pydantic
import sqlite3
import hashlib
import os
from datetime import datetime
from typing import Optional, Dict, Any, List

# Ensure database directory exists
DB_DIR = os.path.join(os.path.dirname(__file__), "..", "database")
DB_PATH = os.path.join(DB_DIR, "users.db")


# ======================
# Helpers
# ======================

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def generate_daily_id(conn: sqlite3.Connection, table: str) -> str:
    cur = conn.cursor()

    cur.execute(
        f"""
        SELECT id FROM {table}
        ORDER BY id DESC
        LIMIT 1
        """
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

    def create_role(self, name: str, description: str):
        with sqlite3.connect(self.db_path) as conn:
            role_id = generate_daily_id(conn, "roles")
            conn.execute(
                "INSERT INTO roles (id, name, description) VALUES (?, ?, ?)",
                (role_id, name, description),
            )
            conn.commit()

    def update_role(self, role_id: str, name: str, description: str):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE roles SET name = ?, description = ? WHERE id = ?",
                (name, description, role_id),
            )
            conn.commit()

    def delete_role(self, role_id: str):
        with sqlite3.connect(self.db_path) as conn:
            # safety: block delete if users exist
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM users WHERE role_id = ?", (role_id,))
            if cur.fetchone()[0] > 0:
                raise Exception("Role is in use")

            conn.execute("DELETE FROM roles WHERE id = ?", (role_id,))
            conn.commit()


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
                description TEXT
            )
        ''')
        
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
        
        # Create default roles if they don't exist
        cursor.execute("SELECT COUNT(*) FROM roles")
        role_count = cursor.fetchone()[0]
        
        if role_count == 0:
            # Create default roles
            cursor.execute("INSERT INTO roles (id, name, description) VALUES (?, ?, ?)", 
                         ("001", "admin", "System administrator with full access"))
            cursor.execute("INSERT INTO roles (id, name, description) VALUES (?, ?, ?)", 
                         ("002", "user", "Regular user with limited access"))
            
            # Create default admin user
            admin_password_hash = hash_password("admin123")
            cursor.execute('''
                INSERT INTO users (id, username, password_hash, role_id, name)
                VALUES (?, ?, ?, ?, ?)
            ''', ("001", "admin", admin_password_hash, "001", "System Administrator"))
            
            print("✅ Default roles and admin user created (admin/admin123)")
        
        conn.commit()

# Initialize database on import
init_database()

user_db = UserDatabase()
role_db = RoleDatabase()
