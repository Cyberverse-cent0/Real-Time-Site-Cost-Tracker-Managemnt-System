# sesion.py
import os
import time
from dataclasses import dataclass

import jwt
import bcrypt

try:
    from . import app_db, user_setup
except ImportError:  # pragma: no cover - support direct script execution
    import app_db
    import user_setup

SECRET_KEY = os.environ.get("SITE_COST_SECRET_KEY", "DEWGEsvs2wfDQWR@FWas<WA!rfw")  # move to env var in production
ALGORITHM = "HS256"
TOKEN_LIFETIME_SECONDS = 12 * 60 * 60  # 12 hours


@dataclass
class Token:
    token: str
    status: bool
    message: str
    return_code: int


# ---------- JWT ----------
def generate_jwt_token(username: str) -> Token:
    now = int(time.time())
    payload = {
        "username": username,
        "iat": now,
        "exp": now + TOKEN_LIFETIME_SECONDS,
    }
    tok = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return Token(token=tok, status=True, message="Token generated successfully", return_code=200)


def verify_jwt_token(token_str: str) -> Token:
    try:
        jwt.decode(token_str, SECRET_KEY, algorithms=[ALGORITHM])
        return Token(token=token_str, status=True, message="Token is valid", return_code=200)
    except jwt.ExpiredSignatureError:
        return Token(token="", status=False, message="Token has expired", return_code=401)
    except jwt.InvalidTokenError:
        return Token(token="", status=False, message="Invalid token", return_code=401)


# ---------- Authentication ----------
def authenticate_user(username: str, password: str) -> Token:
    conn = None
    try:
        conn = app_db.get_database_connection()
        cur = conn.cursor()
        cur.execute(app_db.q("SELECT password FROM users WHERE username = ?;"), (username,))
        result = cur.fetchone()
        cur.close()

        if result is None:
            return Token(token="", status=False, message="User not found", return_code=404)

        stored_password = result[0]
        if bcrypt.checkpw(password.encode("utf-8"), stored_password.encode("utf-8")):
            return generate_jwt_token(username)
        return Token(token="", status=False, message="Incorrect password", return_code=401)
    except Exception as e:
        error_msg = str(e).lower()
        if "connection" in error_msg or "database" in error_msg:
            print(f"Database connection error during authentication: {e}")
            return Token(token="", status=False, message="Database connection error. Please try again.", return_code=503)
        else:
            print(f"Error authenticating user: {e}")
            return Token(token="", status=False, message="Authentication failed. Please try again.", return_code=500)
    finally:
        if conn is not None:
            conn.close()
