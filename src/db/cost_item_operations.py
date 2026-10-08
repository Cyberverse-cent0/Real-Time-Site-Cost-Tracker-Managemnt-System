# cost_item_operations.py
"""CRUD operations for cost_items table in the centralized database."""
from typing import Optional, List, Dict

try:
    from . import app_db
except ImportError:
    import app_db


def create_cost_item(project_id: int, category: str, item_name: str, quantity: float,
                    unit_cost: float, total_cost: float, note: Optional[str] = None) -> dict:
    """
    Create a new cost item in the database.
    Returns a dict with status, message, and id.
    """
    conn = None
    try:
        conn = app_db.get_database_connection()
        cur = conn.cursor()
        cur.execute(
            app_db.q("""
                INSERT INTO cost_items (project_id, category, item_name, quantity, unit_cost, total_cost, note)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                RETURNING id;
            """),
            (project_id, category, item_name, quantity, unit_cost, total_cost, note or ""),
        )
        new_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        return {"status": True, "message": "Cost item created", "id": new_id, "return_code": 201}
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
            print(f"Error creating cost item: {e}")
            return {"status": False, "message": f"Failed to create cost item: {str(e)}", "id": None, "return_code": 500}
    finally:
        if conn is not None:
            conn.close()


def get_cost_item(item_id: int) -> Optional[dict]:
    """Get a cost item by ID."""
    conn = None
    try:
        conn = app_db.get_database_connection()
        cur = conn.cursor()
        cur.execute(app_db.q("SELECT * FROM cost_items WHERE id = ?;"), (item_id,))
        row = cur.fetchone()
        cur.close()
        if row:
            cols = [d[0] for d in cur.description]
            return dict(zip(cols, row))
        return None
    except Exception as e:
        print(f"Error getting cost item: {e}")
        return None
    finally:
        if conn is not None:
            conn.close()


def list_cost_items(project_id: Optional[int] = None, category: Optional[str] = None,
                   limit: Optional[int] = None) -> List[dict]:
    """List cost items with optional filters."""
    conn = None
    try:
        conn = app_db.get_database_connection()
        cur = conn.cursor()
        
        sql = "SELECT * FROM cost_items WHERE 1=1"
        params = []
        
        if project_id is not None:
            sql += " AND project_id = ?"
            params.append(project_id)
        if category is not None:
            sql += " AND category = ?"
            params.append(category)
        
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
        print(f"Error listing cost items: {e}")
        return []
    finally:
        if conn is not None:
            conn.close()


def update_cost_item(item_id: int, category: Optional[str] = None, item_name: Optional[str] = None,
                    quantity: Optional[float] = None, unit_cost: Optional[float] = None,
                    total_cost: Optional[float] = None, note: Optional[str] = None) -> dict:
    """Update a cost item's fields."""
    conn = None
    try:
        conn = app_db.get_database_connection()
        cur = conn.cursor()
        
        updates = []
        params = []
        
        if category is not None:
            updates.append("category = ?")
            params.append(category)
        if item_name is not None:
            updates.append("item_name = ?")
            params.append(item_name)
        if quantity is not None:
            updates.append("quantity = ?")
            params.append(quantity)
        if unit_cost is not None:
            updates.append("unit_cost = ?")
            params.append(unit_cost)
        if total_cost is not None:
            updates.append("total_cost = ?")
            params.append(total_cost)
        if note is not None:
            updates.append("note = ?")
            params.append(note)
        
        if not updates:
            return {"status": False, "message": "No fields to update", "return_code": 400}
        
        params.append(item_id)
        cur.execute(
            app_db.q(f"UPDATE cost_items SET {', '.join(updates)} WHERE id = ?;"),
            tuple(params)
        )
        conn.commit()
        cur.close()
        return {"status": True, "message": "Cost item updated", "return_code": 200}
    except Exception as e:
        if conn is not None:
            try:
                conn.rollback()
            except Exception:
                pass
        print(f"Error updating cost item: {e}")
        return {"status": False, "message": f"Failed to update cost item: {str(e)}", "return_code": 500}
    finally:
        if conn is not None:
            conn.close()


def delete_cost_item(item_id: int) -> dict:
    """Delete a cost item by ID."""
    conn = None
    try:
        conn = app_db.get_database_connection()
        cur = conn.cursor()
        cur.execute(app_db.q("DELETE FROM cost_items WHERE id = ?;"), (item_id,))
        deleted = cur.rowcount > 0
        conn.commit()
        cur.close()
        if deleted:
            return {"status": True, "message": "Cost item deleted", "return_code": 200}
        return {"status": False, "message": "Cost item not found", "return_code": 404}
    except Exception as e:
        if conn is not None:
            try:
                conn.rollback()
            except Exception:
                pass
        print(f"Error deleting cost item: {e}")
        return {"status": False, "message": f"Failed to delete cost item: {str(e)}", "return_code": 500}
    finally:
        if conn is not None:
            conn.close()


def get_cost_item_summary(project_id: int) -> dict:
    """Get cost item summary for a project (total by category, overall total)."""
    conn = None
    try:
        conn = app_db.get_database_connection()
        cur = conn.cursor()
        
        # Total by category
        cur.execute(
            app_db.q("""
                SELECT category, COALESCE(SUM(total_cost), 0) as total, 
                       COALESCE(SUM(quantity), 0) as total_quantity, COUNT(*) as count
                FROM cost_items
                WHERE project_id = ?
                GROUP BY category;
            """),
            (project_id,)
        )
        by_category = [{
            "category": row[0],
            "total": float(row[1]),
            "total_quantity": float(row[2]),
            "count": row[3]
        } for row in cur.fetchall()]
        
        # Overall total
        cur.execute(
            app_db.q("""
                SELECT COALESCE(SUM(total_cost), 0) as total, 
                       COALESCE(SUM(quantity), 0) as total_quantity, COUNT(*) as count
                FROM cost_items
                WHERE project_id = ?;
            """),
            (project_id,)
        )
        total_row = cur.fetchone()
        total = float(total_row[0]) if total_row else 0.0
        total_quantity = float(total_row[1]) if total_row else 0.0
        count = total_row[2] if total_row else 0
        
        cur.close()
        return {
            "project_id": project_id,
            "total": total,
            "total_quantity": total_quantity,
            "count": count,
            "by_category": by_category
        }
    except Exception as e:
        print(f"Error getting cost item summary: {e}")
        return {"project_id": project_id, "total": 0.0, "total_quantity": 0.0, "count": 0, "by_category": []}
    finally:
        if conn is not None:
            conn.close()
