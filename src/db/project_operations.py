# project_operations.py
"""CRUD operations for projects table in the centralized database."""
from typing import Optional, List, Dict

try:
    from . import app_db
except ImportError:
    import app_db


def create_project(name: str, description: str, start_date: str, budget: float, created_by: str) -> dict:
    """
    Create a new project in the database.
    Returns a dict with status, message, and id.
    """
    conn = None
    try:
        conn = app_db.get_database_connection()
        cur = conn.cursor()
        cur.execute(
            app_db.q("""
                INSERT INTO projects (name, description, start_date, budget, created_by)
                VALUES (?, ?, ?, ?, ?)
                RETURNING id;
            """),
            (name, description, start_date, budget, created_by),
        )
        new_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        return {"status": True, "message": "Project created", "id": new_id, "return_code": 201}
    except Exception as e:
        if conn is not None:
            try:
                conn.rollback()
            except Exception:
                pass
        error_msg = str(e).lower()
        if "unique" in error_msg or "duplicate" in error_msg:
            return {"status": False, "message": "Project name already exists", "id": None, "return_code": 409}
        elif "connection" in error_msg or "database" in error_msg:
            return {"status": False, "message": "Database connection error", "id": None, "return_code": 503}
        else:
            print(f"Error creating project: {e}")
            return {"status": False, "message": f"Failed to create project: {str(e)}", "id": None, "return_code": 500}
    finally:
        if conn is not None:
            conn.close()


def get_project(project_id: int) -> Optional[dict]:
    """Get a project by ID."""
    conn = None
    try:
        conn = app_db.get_database_connection()
        cur = conn.cursor()
        cur.execute(app_db.q("SELECT * FROM projects WHERE id = ?;"), (project_id,))
        row = cur.fetchone()
        cur.close()
        if row:
            cols = [d[0] for d in cur.description]
            return dict(zip(cols, row))
        return None
    except Exception as e:
        print(f"Error getting project: {e}")
        return None
    finally:
        if conn is not None:
            conn.close()


def get_project_by_name(name: str) -> Optional[dict]:
    """Get a project by name."""
    conn = None
    try:
        conn = app_db.get_database_connection()
        cur = conn.cursor()
        cur.execute(app_db.q("SELECT * FROM projects WHERE name = ?;"), (name,))
        row = cur.fetchone()
        cur.close()
        if row:
            cols = [d[0] for d in cur.description]
            return dict(zip(cols, row))
        return None
    except Exception as e:
        print(f"Error getting project by name: {e}")
        return None
    finally:
        if conn is not None:
            conn.close()


def list_projects(created_by: Optional[str] = None) -> List[dict]:
    """List all projects, optionally filtered by creator."""
    conn = None
    try:
        conn = app_db.get_database_connection()
        cur = conn.cursor()
        if created_by:
            cur.execute(app_db.q("SELECT * FROM projects WHERE created_by = ? ORDER BY created_at DESC;"), (created_by,))
        else:
            cur.execute(app_db.q("SELECT * FROM projects ORDER BY created_at DESC;"))
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description]
        cur.close()
        return [dict(zip(cols, row)) for row in rows]
    except Exception as e:
        print(f"Error listing projects: {e}")
        return []
    finally:
        if conn is not None:
            conn.close()


def update_project(project_id: int, name: Optional[str] = None, description: Optional[str] = None,
                  start_date: Optional[str] = None, budget: Optional[float] = None) -> dict:
    """Update a project's fields."""
    conn = None
    try:
        conn = app_db.get_database_connection()
        cur = conn.cursor()
        
        updates = []
        params = []
        
        if name is not None:
            updates.append("name = ?")
            params.append(name)
        if description is not None:
            updates.append("description = ?")
            params.append(description)
        if start_date is not None:
            updates.append("start_date = ?")
            params.append(start_date)
        if budget is not None:
            updates.append("budget = ?")
            params.append(budget)
        
        if not updates:
            return {"status": False, "message": "No fields to update", "return_code": 400}
        
        params.append(project_id)
        cur.execute(
            app_db.q(f"UPDATE projects SET {', '.join(updates)} WHERE id = ?;"),
            tuple(params)
        )
        conn.commit()
        cur.close()
        return {"status": True, "message": "Project updated", "return_code": 200}
    except Exception as e:
        if conn is not None:
            try:
                conn.rollback()
            except Exception:
                pass
        print(f"Error updating project: {e}")
        return {"status": False, "message": f"Failed to update project: {str(e)}", "return_code": 500}
    finally:
        if conn is not None:
            conn.close()


def delete_project(project_id: int) -> dict:
    """Delete a project by ID (cascades to expenses, cost_items, budgets)."""
    conn = None
    try:
        conn = app_db.get_database_connection()
        cur = conn.cursor()
        cur.execute(app_db.q("DELETE FROM projects WHERE id = ?;"), (project_id,))
        deleted = cur.rowcount > 0
        conn.commit()
        cur.close()
        if deleted:
            return {"status": True, "message": "Project deleted", "return_code": 200}
        return {"status": False, "message": "Project not found", "return_code": 404}
    except Exception as e:
        if conn is not None:
            try:
                conn.rollback()
            except Exception:
                pass
        print(f"Error deleting project: {e}")
        return {"status": False, "message": f"Failed to delete project: {str(e)}", "return_code": 500}
    finally:
        if conn is not None:
            conn.close()


def project_exists(name: str) -> bool:
    """Check if a project name already exists."""
    conn = None
    try:
        conn = app_db.get_database_connection()
        cur = conn.cursor()
        cur.execute(app_db.q("SELECT 1 FROM projects WHERE name = ?;"), (name,))
        exists = cur.fetchone() is not None
        cur.close()
        return exists
    except Exception as e:
        print(f"Error checking project existence: {e}")
        return False
    finally:
        if conn is not None:
            conn.close()
