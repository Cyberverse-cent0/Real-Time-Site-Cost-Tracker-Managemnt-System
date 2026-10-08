# user_setup.py
import bcrypt

try:
    from . import app_db
except ImportError:  # pragma: no cover - support direct script execution
    import app_db


def hash_password(plain_password: str) -> str:
    """Hash a plain password with bcrypt."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(plain_password.encode("utf-8"), salt).decode("utf-8")


def create_user(username: str, password: str, email: str) -> dict:
    """
    Insert a new user into the database.
    Returns a dict describing the result.
    """
    conn = None
    try:
        hashed = hash_password(password)
        conn = app_db.get_database_connection()
        cur = conn.cursor()
        cur.execute(
            app_db.q("""
                INSERT INTO users (username, password, email)
                VALUES (?, ?, ?)
                RETURNING id;
            """),
            (username, hashed, email),
        )
        new_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        return {"status": True, "message": "User created", "id": new_id, "return_code": 201}
    except Exception as e:
        error_msg = str(e).lower()
        if conn is not None:
            try:
                conn.rollback()
            except Exception:
                pass
        
        # Parse common database errors
        if "unique" in error_msg or "duplicate" in error_msg:
            if "username" in error_msg:
                return {"status": False, "message": "Username already exists", "id": None, "return_code": 409}
            elif "email" in error_msg:
                return {"status": False, "message": "Email already registered", "id": None, "return_code": 409}
            else:
                return {"status": False, "message": "Username or email already exists", "id": None, "return_code": 409}
        elif "connection" in error_msg or "database" in error_msg:
            return {"status": False, "message": "Database connection error. Please try again.", "id": None, "return_code": 503}
        else:
            print(f"Error creating user: {e}")
            return {"status": False, "message": f"Failed to create account: {str(e)}", "id": None, "return_code": 500}
    finally:
        if conn is not None:
            conn.close()


def user_exists(username: str) -> bool:
    """Check whether a username is already taken."""
    conn = None
    try:
        conn = app_db.get_database_connection()
        cur = conn.cursor()
        cur.execute(app_db.q("SELECT 1 FROM users WHERE username = ?;"), (username,))
        exists = cur.fetchone() is not None
        cur.close()
        return exists
    except Exception as e:
        error_msg = str(e).lower()
        if "connection" in error_msg or "database" in error_msg:
            print(f"Database connection error checking user: {e}")
        else:
            print(f"Error checking user: {e}")
        return False
    finally:
        if conn is not None:
            conn.close()


def email_exists(email: str) -> bool:
    """Check whether an email address is already registered."""
    conn = None
    try:
        conn = app_db.get_database_connection()
        cur = conn.cursor()
        cur.execute(app_db.q("SELECT 1 FROM users WHERE email = ?;"), (email,))
        exists = cur.fetchone() is not None
        cur.close()
        return exists
    except Exception as e:
        error_msg = str(e).lower()
        if "connection" in error_msg or "database" in error_msg:
            print(f"Database connection error checking email: {e}")
        else:
            print(f"Error checking email: {e}")
        return False
    finally:
        if conn is not None:
            conn.close()


def delete_user(username: str) -> bool:
    """Delete a user by username."""
    conn = None
    try:
        conn = app_db.get_database_connection()
        cur = conn.cursor()
        cur.execute(app_db.q("DELETE FROM users WHERE username = ?;"), (username,))
        deleted = cur.rowcount > 0
        conn.commit()
        cur.close()
        return deleted
    except Exception as e:
        print(f"Error deleting user: {e}")
        return False
    finally:
        if conn is not None:
            conn.close()
