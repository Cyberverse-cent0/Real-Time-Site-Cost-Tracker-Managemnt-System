# app_db.py
"""Database access layer.

Supports two backends:
  * PostgreSQL  – used when psycopg2 is importable AND the server is reachable
                  (or SITE_COST_DB_BACKEND=postgres forces it).
  * SQLite      – zero-config fallback used everywhere else.

All SQL in the codebase is written with '?' placeholders; `q()` translates
them to '%s' when running on PostgreSQL. RETURNING works on both backends
(SQLite >= 3.35, psycopg2).
"""
import os
import sqlite3

try:
    import psycopg2
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
except ImportError:  # pragma: no cover - optional dependency
    psycopg2 = None
    ISOLATION_LEVEL_AUTOCOMMIT = None

# ---- Configuration ----
# Postgres settings can be overridden through environment variables.
DB_NAME = os.environ.get("SITE_COST_DB_NAME", "site_cost_tracker_prototype_db")
DB_USER = os.environ.get("SITE_COST_DB_USER", "system")
DB_PASSWORD = os.environ.get("SITE_COST_DB_PASSWORD", "ESFErvxu88823")
DB_HOST = os.environ.get("SITE_COST_DB_HOST", "localhost")
DB_PORT = int(os.environ.get("SITE_COST_DB_PORT", "5432"))

# SQLite database lives in <project root>/data/ (gitignored).
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
DB_PATH = os.path.join(DATA_DIR, f"{DB_NAME}.db")

_backend = None          # cached decision: "postgres" | "sqlite"
_warned_fallback = False


def _is_sqlite_mode() -> bool:
    return _resolve_backend() == "sqlite"


def _resolve_backend() -> str:
    """Decide the backend once: explicit env override, else auto-detect.

    Auto = Postgres when psycopg2 is importable AND the server answers;
    otherwise SQLite so the app always runs out of the box.
    """
    global _backend, _warned_fallback
    if _backend is not None:
        return _backend

    forced = os.environ.get("SITE_COST_DB_BACKEND", "").strip().lower()
    if forced == "postgres":
        _backend = "postgres"
        return _backend
    if forced == "sqlite":
        _backend = "sqlite"
        return _backend

    if psycopg2 is None:
        _backend = "sqlite"
        return _backend

    try:
        conn = psycopg2.connect(
            dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD,
            host=DB_HOST, port=DB_PORT, connect_timeout=3,
        )
        conn.close()
        _backend = "postgres"
    except Exception as e:
        if not _warned_fallback:
            print(f"[app_db] Postgres unavailable ({e}); falling back to SQLite at {DB_PATH}")
            _warned_fallback = True
        _backend = "sqlite"
    return _backend


def q(sql: str) -> str:
    """Translate '?' placeholders to '%s' when running on PostgreSQL."""
    return sql.replace("?", "%s") if _resolve_backend() == "postgres" else sql


def get_database_connection():
    """Return a connection to the target database."""
    backend = _resolve_backend()
    if backend == "sqlite":
        try:
            os.makedirs(DATA_DIR, exist_ok=True)
            conn = sqlite3.connect(DB_PATH)
            conn.execute("PRAGMA foreign_keys = ON;")
            return conn
        except PermissionError as e:
            raise Exception(f"Permission denied: Cannot create database directory at {DATA_DIR}. Error: {e}")
        except sqlite3.Error as e:
            raise Exception(f"SQLite connection error: {e}")
        except Exception as e:
            raise Exception(f"Unexpected error connecting to SQLite database: {e}")
    
    try:
        return psycopg2.connect(
            dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD,
            host=DB_HOST, port=DB_PORT,
        )
    except psycopg2.OperationalError as e:
        raise Exception(f"PostgreSQL connection failed: {e}. Check if database server is running and credentials are correct.")
    except psycopg2.Error as e:
        raise Exception(f"PostgreSQL error: {e}")
    except Exception as e:
        raise Exception(f"Unexpected error connecting to PostgreSQL: {e}")


def rows_as_dicts(cursor) -> list[dict]:
    """Convert the full fetchall() result into a list of dicts."""
    cols = [d[0] for d in cursor.description]
    return [dict(zip(cols, row)) for row in cursor.fetchall()]


# ---- Existence / creation ----
def database_exists() -> bool:
    """Check if the target database exists."""
    if _is_sqlite_mode():
        return os.path.exists(DB_PATH)
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD,
            host=DB_HOST, port=DB_PORT, connect_timeout=3,
        )
        conn.close()
        return True
    except Exception:
        return False


def create_database() -> bool:
    """Create the target database if it doesn't exist (Postgres only)."""
    if _is_sqlite_mode():
        try:
            os.makedirs(DATA_DIR, exist_ok=True)
            sqlite3.connect(DB_PATH).close()
            return True
        except Exception as e:
            print(f"Error creating SQLite database: {e}")
            return False
    try:
        conn = psycopg2.connect(
            dbname="postgres", user=DB_USER, password=DB_PASSWORD,
            host=DB_HOST, port=DB_PORT,
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        cur.execute(f'CREATE DATABASE "{DB_NAME}";')
        cur.execute(f'GRANT ALL PRIVILEGES ON DATABASE "{DB_NAME}" TO {DB_USER};')
        cur.execute(f'ALTER DATABASE "{DB_NAME}" OWNER TO {DB_USER};')
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Error creating database: {e}")
        return False


_USER_TABLE = {
    "sqlite": """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );""",
    "postgres": """
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );""",
}

_PROJECT_TABLE = {
    "sqlite": """
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT NOT NULL DEFAULT '',
            start_date TEXT,
            budget REAL NOT NULL DEFAULT 0,
            created_by TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );""",
    "postgres": """
        CREATE TABLE IF NOT EXISTS projects (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            description TEXT NOT NULL DEFAULT '',
            start_date DATE,
            budget NUMERIC(12, 2) NOT NULL DEFAULT 0,
            created_by VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );""",
}

_EXPENSE_TABLE = {
    "sqlite": """
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY,
            project_id INTEGER NOT NULL
                REFERENCES projects(id) ON DELETE CASCADE,
            category TEXT NOT NULL,
            notes TEXT NOT NULL DEFAULT '',
            amount REAL NOT NULL,
            expense_date TEXT,
            created_by TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );""",
    "postgres": """
        CREATE TABLE IF NOT EXISTS expenses (
            id SERIAL PRIMARY KEY,
            project_id INTEGER NOT NULL
                REFERENCES projects(id) ON DELETE CASCADE,
            category VARCHAR(30) NOT NULL,
            notes TEXT NOT NULL DEFAULT '',
            amount NUMERIC(12, 2) NOT NULL,
            expense_date DATE,
            created_by VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );""",
}

_COST_ITEMS_TABLE = {
    "sqlite": """
        CREATE TABLE IF NOT EXISTS cost_items (
            id INTEGER PRIMARY KEY,
            project_id INTEGER NOT NULL,
            category TEXT NOT NULL,
            item_name TEXT NOT NULL,
            quantity REAL DEFAULT 0,
            unit_cost REAL DEFAULT 0,
            total_cost REAL DEFAULT 0,
            note TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );""",
    "postgres": """
        CREATE TABLE IF NOT EXISTS cost_items (
            id SERIAL PRIMARY KEY,
            project_id INTEGER NOT NULL,
            category VARCHAR(50) NOT NULL,
            item_name VARCHAR(100) NOT NULL,
            quantity NUMERIC(12, 2) DEFAULT 0,
            unit_cost NUMERIC(12, 2) DEFAULT 0,
            total_cost NUMERIC(12, 2) DEFAULT 0,
            note TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );""",
}

_BUDGET_TABLE = {
    "sqlite": """
        CREATE TABLE IF NOT EXISTS budgets (
            id INTEGER PRIMARY KEY,
            project_id INTEGER NOT NULL,
            category TEXT NOT NULL,
            budget_limit REAL NOT NULL DEFAULT 0,
            spent_amount REAL NOT NULL DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );""",
    "postgres": """
        CREATE TABLE IF NOT EXISTS budgets (
            id SERIAL PRIMARY KEY,
            project_id INTEGER NOT NULL,
            category VARCHAR(50) NOT NULL,
            budget_limit NUMERIC(12, 2) NOT NULL DEFAULT 0,
            spent_amount NUMERIC(12, 2) NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );""",
}

_PREF_TABLE = {
    "sqlite": """
        CREATE TABLE IF NOT EXISTS user_preferences (
            username TEXT PRIMARY KEY,
            prefs_json TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );""",
    "postgres": """
        CREATE TABLE IF NOT EXISTS user_preferences (
            username VARCHAR(50) PRIMARY KEY,
            prefs_json TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );""",
}


def create_tables() -> bool:
    """Create all tables in the target database."""
    conn = None
    try:
        conn = get_database_connection()
        cur = conn.cursor()
        backend = "sqlite" if _is_sqlite_mode() else "postgres"
        for ddl in (
            _USER_TABLE[backend],
            _PROJECT_TABLE[backend],
            _EXPENSE_TABLE[backend],
            _COST_ITEMS_TABLE[backend],
            _BUDGET_TABLE[backend],
            _PREF_TABLE[backend],
        ):
            cur.execute(ddl)
        conn.commit()
        cur.close()
        return True
    except Exception as e:
        print(f"Error creating tables: {e}")
        return False
    finally:
        if conn is not None:
            conn.close()


def initialize_database() -> bool:
    """Full setup: create DB (if needed) and create tables."""
    if not database_exists():
        if not create_database():
            return False
    return create_tables()


if __name__ == "__main__":
    ok = initialize_database()
    print(f"Database initialized ({_resolve_backend()})" if ok else "Database initialization FAILED")
