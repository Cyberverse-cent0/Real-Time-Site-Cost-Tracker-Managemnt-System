# expense_operations.py
"""CRUD operations for expenses table in the centralized database."""
from typing import Optional, List, Dict

try:
    from . import app_db
except ImportError:
    import app_db


def create_expense(project_id: int, category: str, notes: str, amount: float,
                  expense_date: str, created_by: str) -> dict:
    """
    Create a new expense in the database.
    Returns a dict with status, message, and id.
    """
    conn = None
    try:
        conn = app_db.get_database_connection()
        cur = conn.cursor()
        cur.execute(
            app_db.q("""
                INSERT INTO expenses (project_id, category, notes, amount, expense_date, created_by)
                VALUES (?, ?, ?, ?, ?, ?)
                RETURNING id;
            """),
            (project_id, category, notes, amount, expense_date, created_by),
        )
        new_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        return {"status": True, "message": "Expense created", "id": new_id, "return_code": 201}
    except Exception as e:
        if conn is not None:
            try:
                conn.rollback()
            except Exception:
                pass
        error_msg = str(e).lower()
        if "foreign key" in error_msg:
            return {"status": False, "message": "Project not found", "id": None, "return_code": 404}
        elif "connection" in error_msg or "database" in error_msg:
            return {"status": False, "message": "Database connection error", "id": None, "return_code": 503}
        else:
            print(f"Error creating expense: {e}")
            return {"status": False, "message": f"Failed to create expense: {str(e)}", "id": None, "return_code": 500}
    finally:
        if conn is not None:
            conn.close()


def get_expense(expense_id: int) -> Optional[dict]:
    """Get an expense by ID."""
    conn = None
    try:
        conn = app_db.get_database_connection()
        cur = conn.cursor()
        cur.execute(app_db.q("SELECT * FROM expenses WHERE id = ?;"), (expense_id,))
        row = cur.fetchone()
        cur.close()
        if row:
            cols = [d[0] for d in cur.description]
            return dict(zip(cols, row))
        return None
    except Exception as e:
        print(f"Error getting expense: {e}")
        return None
    finally:
        if conn is not None:
            conn.close()


def list_expenses(project_id: Optional[int] = None, category: Optional[str] = None,
                 created_by: Optional[str] = None, limit: Optional[int] = None) -> List[dict]:
    """List expenses with optional filters."""
    conn = None
    try:
        conn = app_db.get_database_connection()
        cur = conn.cursor()
        
        sql = "SELECT * FROM expenses WHERE 1=1"
        params = []
        
        if project_id is not None:
            sql += " AND project_id = ?"
            params.append(project_id)
        if category is not None:
            sql += " AND category = ?"
            params.append(category)
        if created_by is not None:
            sql += " AND created_by = ?"
            params.append(created_by)
        
        sql += " ORDER BY created_at DESC"
        
        if limit is not None:
            sql += " LIMIT ?"
            params.append(limit)
        
        cur.execute(app_db.q(sql), tuple(params))
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description]
        cur.close()
        return [dict(zip(cols, row)) for row in rows]
    except Exception as e:
        print(f"Error listing expenses: {e}")
        return []
    finally:
        if conn is not None:
            conn.close()


def update_expense(expense_id: int, category: Optional[str] = None, notes: Optional[str] = None,
                  amount: Optional[float] = None, expense_date: Optional[str] = None) -> dict:
    """Update an expense's fields."""
    conn = None
    try:
        conn = app_db.get_database_connection()
        cur = conn.cursor()
        
        updates = []
        params = []
        
        if category is not None:
            updates.append("category = ?")
            params.append(category)
        if notes is not None:
            updates.append("notes = ?")
            params.append(notes)
        if amount is not None:
            updates.append("amount = ?")
            params.append(amount)
        if expense_date is not None:
            updates.append("expense_date = ?")
            params.append(expense_date)
        
        if not updates:
            return {"status": False, "message": "No fields to update", "return_code": 400}
        
        params.append(expense_id)
        cur.execute(
            app_db.q(f"UPDATE expenses SET {', '.join(updates)} WHERE id = ?;"),
            tuple(params)
        )
        conn.commit()
        cur.close()
        return {"status": True, "message": "Expense updated", "return_code": 200}
    except Exception as e:
        if conn is not None:
            try:
                conn.rollback()
            except Exception:
                pass
        print(f"Error updating expense: {e}")
        return {"status": False, "message": f"Failed to update expense: {str(e)}", "return_code": 500}
    finally:
        if conn is not None:
            conn.close()


def delete_expense(expense_id: int) -> dict:
    """Delete an expense by ID."""
    conn = None
    try:
        conn = app_db.get_database_connection()
        cur = conn.cursor()
        cur.execute(app_db.q("DELETE FROM expenses WHERE id = ?;"), (expense_id,))
        deleted = cur.rowcount > 0
        conn.commit()
        cur.close()
        if deleted:
            return {"status": True, "message": "Expense deleted", "return_code": 200}
        return {"status": False, "message": "Expense not found", "return_code": 404}
    except Exception as e:
        if conn is not None:
            try:
                conn.rollback()
            except Exception:
                pass
        print(f"Error deleting expense: {e}")
        return {"status": False, "message": f"Failed to delete expense: {str(e)}", "return_code": 500}
    finally:
        if conn is not None:
            conn.close()


def get_expense_summary(project_id: int) -> dict:
    """Get expense summary for a project (total by category, overall total)."""
    conn = None
    try:
        conn = app_db.get_database_connection()
        cur = conn.cursor()
        
        # Total by category
        cur.execute(
            app_db.q("""
                SELECT category, COALESCE(SUM(amount), 0) as total, COUNT(*) as count
                FROM expenses
                WHERE project_id = ?
                GROUP BY category;
            """),
            (project_id,)
        )
        by_category = [{"category": row[0], "total": float(row[1]), "count": row[2]} for row in cur.fetchall()]
        
        # Overall total
        cur.execute(
            app_db.q("""
                SELECT COALESCE(SUM(amount), 0) as total, COUNT(*) as count
                FROM expenses
                WHERE project_id = ?;
            """),
            (project_id,)
        )
        total_row = cur.fetchone()
        total = float(total_row[0]) if total_row else 0.0
        count = total_row[1] if total_row else 0
        
        cur.close()
        return {
            "project_id": project_id,
            "total": total,
            "count": count,
            "by_category": by_category
        }
    except Exception as e:
        print(f"Error getting expense summary: {e}")
        return {"project_id": project_id, "total": 0.0, "count": 0, "by_category": []}
    finally:
        if conn is not None:
            conn.close()
