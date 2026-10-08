# budget_operations.py
"""CRUD operations for budgets table in the centralized database."""
from typing import Optional, List, Dict

try:
    from . import app_db
except ImportError:
    import app_db


def create_budget(project_id: int, category: str, budget_limit: float, spent_amount: float = 0.0) -> dict:
    """
    Create a new budget in the database.
    Returns a dict with status, message, and id.
    """
    conn = None
    try:
        conn = app_db.get_database_connection()
        cur = conn.cursor()
        cur.execute(
            app_db.q("""
                INSERT INTO budgets (project_id, category, budget_limit, spent_amount)
                VALUES (?, ?, ?, ?)
                RETURNING id;
            """),
            (project_id, category, budget_limit, spent_amount),
        )
        new_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        return {"status": True, "message": "Budget created", "id": new_id, "return_code": 201}
    except Exception as e:
        if conn is not None:
            try:
                conn.rollback()
            except Exception:
                pass
        error_msg = str(e).lower()
        if "foreign key" in error_msg:
            return {"status": False, "message": "Project not found", "id": None, "return_code": 404}
        elif "unique" in error_msg or "duplicate" in error_msg:
            return {"status": False, "message": "Budget for this category already exists", "id": None, "return_code": 409}
        elif "connection" in error_msg or "database" in error_msg:
            return {"status": False, "message": "Database connection error", "id": None, "return_code": 503}
        else:
            print(f"Error creating budget: {e}")
            return {"status": False, "message": f"Failed to create budget: {str(e)}", "id": None, "return_code": 500}
    finally:
        if conn is not None:
            conn.close()


def get_budget(budget_id: int) -> Optional[dict]:
    """Get a budget by ID."""
    conn = None
    try:
        conn = app_db.get_database_connection()
        cur = conn.cursor()
        cur.execute(app_db.q("SELECT * FROM budgets WHERE id = ?;"), (budget_id,))
        row = cur.fetchone()
        cur.close()
        if row:
            cols = [d[0] for d in cur.description]
            return dict(zip(cols, row))
        return None
    except Exception as e:
        print(f"Error getting budget: {e}")
        return None
    finally:
        if conn is not None:
            conn.close()


def get_budget_by_project_category(project_id: int, category: str) -> Optional[dict]:
    """Get a budget by project ID and category."""
    conn = None
    try:
        conn = app_db.get_database_connection()
        cur = conn.cursor()
        cur.execute(
            app_db.q("SELECT * FROM budgets WHERE project_id = ? AND category = ?;"),
            (project_id, category)
        )
        row = cur.fetchone()
        cur.close()
        if row:
            cols = [d[0] for d in cur.description]
            return dict(zip(cols, row))
        return None
    except Exception as e:
        print(f"Error getting budget by project/category: {e}")
        return None
    finally:
        if conn is not None:
            conn.close()


def list_budgets(project_id: Optional[int] = None) -> List[dict]:
    """List budgets, optionally filtered by project."""
    conn = None
    try:
        conn = app_db.get_database_connection()
        cur = conn.cursor()
        
        if project_id is not None:
            cur.execute(app_db.q("SELECT * FROM budgets WHERE project_id = ? ORDER BY category;"), (project_id,))
        else:
            cur.execute(app_db.q("SELECT * FROM budgets ORDER BY project_id, category;"))
        
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description]
        cur.close()
        return [dict(zip(cols, row)) for row in rows]
    except Exception as e:
        print(f"Error listing budgets: {e}")
        return []
    finally:
        if conn is not None:
            conn.close()


def update_budget(budget_id: int, budget_limit: Optional[float] = None, 
                 spent_amount: Optional[float] = None) -> dict:
    """Update a budget's fields."""
    conn = None
    try:
        conn = app_db.get_database_connection()
        cur = conn.cursor()
        
        updates = []
        params = []
        
        if budget_limit is not None:
            updates.append("budget_limit = ?")
            params.append(budget_limit)
        if spent_amount is not None:
            updates.append("spent_amount = ?")
            params.append(spent_amount)
        
        if not updates:
            return {"status": False, "message": "No fields to update", "return_code": 400}
        
        params.append(budget_id)
        cur.execute(
            app_db.q(f"UPDATE budgets SET {', '.join(updates)} WHERE id = ?;"),
            tuple(params)
        )
        conn.commit()
        cur.close()
        return {"status": True, "message": "Budget updated", "return_code": 200}
    except Exception as e:
        if conn is not None:
            try:
                conn.rollback()
            except Exception:
                pass
        print(f"Error updating budget: {e}")
        return {"status": False, "message": f"Failed to update budget: {str(e)}", "return_code": 500}
    finally:
        if conn is not None:
            conn.close()


def upsert_budget(project_id: int, category: str, budget_limit: float) -> dict:
    """Insert or update a budget for a project category."""
    conn = None
    try:
        conn = app_db.get_database_connection()
        cur = conn.cursor()
        
        # Check if budget exists
        existing = get_budget_by_project_category(project_id, category)
        
        if existing:
            # Update existing
            cur.execute(
                app_db.q("UPDATE budgets SET budget_limit = ? WHERE id = ?;"),
                (budget_limit, existing["id"])
            )
            conn.commit()
            cur.close()
            return {"status": True, "message": "Budget updated", "id": existing["id"], "return_code": 200}
        else:
            # Create new
            cur.execute(
                app_db.q("""
                    INSERT INTO budgets (project_id, category, budget_limit, spent_amount)
                    VALUES (?, ?, ?, 0)
                    RETURNING id;
                """),
                (project_id, category, budget_limit)
            )
            new_id = cur.fetchone()[0]
            conn.commit()
            cur.close()
            return {"status": True, "message": "Budget created", "id": new_id, "return_code": 201}
    except Exception as e:
        if conn is not None:
            try:
                conn.rollback()
            except Exception:
                pass
        print(f"Error upserting budget: {e}")
        return {"status": False, "message": f"Failed to upsert budget: {str(e)}", "return_code": 500}
    finally:
        if conn is not None:
            conn.close()


def delete_budget(budget_id: int) -> dict:
    """Delete a budget by ID."""
    conn = None
    try:
        conn = app_db.get_database_connection()
        cur = conn.cursor()
        cur.execute(app_db.q("DELETE FROM budgets WHERE id = ?;"), (budget_id,))
        deleted = cur.rowcount > 0
        conn.commit()
        cur.close()
        if deleted:
            return {"status": True, "message": "Budget deleted", "return_code": 200}
        return {"status": False, "message": "Budget not found", "return_code": 404}
    except Exception as e:
        if conn is not None:
            try:
                conn.rollback()
            except Exception:
                pass
        print(f"Error deleting budget: {e}")
        return {"status": False, "message": f"Failed to delete budget: {str(e)}", "return_code": 500}
    finally:
        if conn is not None:
            conn.close()


def update_spent_amount(project_id: int, category: str, amount: float) -> dict:
    """Update the spent amount for a budget (add to existing)."""
    conn = None
    try:
        conn = app_db.get_database_connection()
        cur = conn.cursor()
        
        cur.execute(
            app_db.q("""
                UPDATE budgets 
                SET spent_amount = spent_amount + ?
                WHERE project_id = ? AND category = ?;
            """),
            (amount, project_id, category)
        )
        
        updated = cur.rowcount > 0
        conn.commit()
        cur.close()
        
        if updated:
            return {"status": True, "message": "Spent amount updated", "return_code": 200}
        return {"status": False, "message": "Budget not found", "return_code": 404}
    except Exception as e:
        if conn is not None:
            try:
                conn.rollback()
            except Exception:
                pass
        print(f"Error updating spent amount: {e}")
        return {"status": False, "message": f"Failed to update spent amount: {str(e)}", "return_code": 500}
    finally:
        if conn is not None:
            conn.close()


def get_budget_status(project_id: int, category: str) -> dict:
    """Get budget status including usage percentage and remaining amount."""
    budget = get_budget_by_project_category(project_id, category)
    
    if not budget:
        return {
            "exists": False,
            "budget_limit": 0.0,
            "spent_amount": 0.0,
            "remaining": 0.0,
            "percentage": 0.0,
            "status": "none"
        }
    
    budget_limit = float(budget["budget_limit"])
    spent = float(budget["spent_amount"])
    remaining = budget_limit - spent
    percentage = (spent / budget_limit * 100) if budget_limit > 0 else 0.0
    
    # Determine status
    if percentage >= 100:
        status = "over"
    elif percentage >= 80:
        status = "warning"
    else:
        status = "ok"
    
    return {
        "exists": True,
        "budget_limit": budget_limit,
        "spent_amount": spent,
        "remaining": remaining,
        "percentage": percentage,
        "status": status
    }


def get_project_budget_summary(project_id: int) -> dict:
    """Get complete budget summary for a project."""
    conn = None
    try:
        conn = app_db.get_database_connection()
        cur = conn.cursor()
        
        # Get all budgets for project
        cur.execute(
            app_db.q("SELECT * FROM budgets WHERE project_id = ?;"),
            (project_id,)
        )
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description]
        budgets = [dict(zip(cols, row)) for row in rows]
        
        # Calculate totals
        total_budget = sum(float(b["budget_limit"]) for b in budgets)
        total_spent = sum(float(b["spent_amount"]) for b in budgets)
        total_remaining = total_budget - total_spent
        overall_percentage = (total_spent / total_budget * 100) if total_budget > 0 else 0.0
        
        # Determine overall status
        if overall_percentage >= 100:
            overall_status = "over"
        elif overall_percentage >= 80:
            overall_status = "warning"
        else:
            overall_status = "ok"
        
        cur.close()
        return {
            "project_id": project_id,
            "budgets": budgets,
            "total_budget": total_budget,
            "total_spent": total_spent,
            "total_remaining": total_remaining,
            "overall_percentage": overall_percentage,
            "overall_status": overall_status
        }
    except Exception as e:
        print(f"Error getting budget summary: {e}")
        return {
            "project_id": project_id,
            "budgets": [],
            "total_budget": 0.0,
            "total_spent": 0.0,
            "total_remaining": 0.0,
            "overall_percentage": 0.0,
            "overall_status": "none"
        }
    finally:
        if conn is not None:
            conn.close()
