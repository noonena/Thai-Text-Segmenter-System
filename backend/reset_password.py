"""
Reset a user's password from the command line.

Usage:
    python reset_password.py <username> <new_password>
"""

import sys
import os
import sqlite3

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils.database import DB_PATH, hash_password

def reset_password(username: str, new_password: str):
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute("SELECT id FROM users WHERE username = ?", (username,))
        row = cur.fetchone()
        if not row:
            print(f"User '{username}' not found.")
            sys.exit(1)
        conn.execute(
            "UPDATE users SET password_hash = ? WHERE username = ?",
            (hash_password(new_password), username)
        )
        conn.commit()
    print(f"Password for '{username}' updated.")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python reset_password.py <username> <new_password>")
        sys.exit(1)
    reset_password(sys.argv[1], sys.argv[2])
