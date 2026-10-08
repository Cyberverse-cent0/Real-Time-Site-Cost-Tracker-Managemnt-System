# operations_helper.py
"""Helper functions for database operations to demonstrate usage and integration."""
from typing import Dict, List, Optional

try:
    from . import app_db
    from . import project_operations
    from . import expense_operations
    from . import cost_item_operations
    from . import budget_operations
except ImportError:
    import app_db
    import project_operations
    import expense_operations
    import cost_item_operations
    import budget_operations


def initialize_database_if_needed() -> bool:
    """Initialize the database if it doesn't exist."""
    try:
        if not app_db.database_exists():
            return app_db.initialize_database()
        return True
    except Exception as e:
        print(f"Error initializing database: {e}")
        return False


def create_project_with_defaults(name: str, description: str, created_by: str, 
                                start_date: str = None, budget: float = 0.0) -> Dict:
    """Create a project with sensible defaults."""
    from datetime import date
    
    if start_date is None:
        start_date = date.today().isoformat()
    
    return project_operations.create_project(
        name=name,
        description=description,
        start_date=start_date,
        budget=budget,
        created_by=created_by
    )


def get_project_complete_summary(project_id: int) -> Dict:
    """Get a complete summary of a project including expenses, cost items, and budgets."""
    # Get project details
    project = project_operations.get_project(project_id)
    if not project:
        return {"error": "Project not found"}
    
    # Get expense summary
    expense_summary = expense_operations.get_expense_summary(project_id)
    
    # Get cost item summary
    cost_item_summary = cost_item_operations.get_cost_item_summary(project_id)
    
    # Get budget summary
    budget_summary = budget_operations.get_project_budget_summary(project_id)
    
    return {
        "project": project,
        "expenses": expense_summary,
        "cost_items": cost_item_summary,
        "budgets": budget_summary,
        "total_spent": expense_summary["total"] + cost_item_summary["total"],
        "total_budget": budget_summary["total_budget"],
        "budget_remaining": budget_summary["total_remaining"]
    }


def add_expense_with_auto_budget_update(project_id: int, category: str, notes: str,
                                       amount: float, expense_date: str, created_by: str) -> Dict:
    """Add an expense and automatically update the budget spent amount."""
    # Create the expense
    result = expense_operations.create_expense(
        project_id=project_id,
        category=category,
        notes=notes,
        amount=amount,
        expense_date=expense_date,
        created_by=created_by
    )
    
    if result["status"]:
        # Update budget spent amount
        budget_operations.update_spent_amount(project_id, category, amount)
    
    return result


def add_cost_item_with_auto_budget_update(project_id: int, category: str, item_name: str,
                                          quantity: float, unit_cost: float, note: str = None) -> Dict:
    """Add a cost item and automatically update the budget spent amount."""
    total_cost = quantity * unit_cost
    
    # Create the cost item
    result = cost_item_operations.create_cost_item(
        project_id=project_id,
        category=category,
        item_name=item_name,
        quantity=quantity,
        unit_cost=unit_cost,
        total_cost=total_cost,
        note=note
    )
    
    if result["status"]:
        # Update budget spent amount
        budget_operations.update_spent_amount(project_id, category, total_cost)
    
    return result


def get_user_projects(created_by: str) -> List[Dict]:
    """Get all projects for a specific user with summary data."""
    projects = project_operations.list_projects(created_by=created_by)
    
    for project in projects:
        project_id = project["id"]
        summary = get_project_complete_summary(project_id)
        project["summary"] = summary
    
    return projects


def delete_project_cascade(project_id: int) -> Dict:
    """Delete a project (this cascades to expenses, cost_items, and budgets via foreign keys)."""
    return project_operations.delete_project(project_id)


def get_dashboard_summary(created_by: str) -> Dict:
    """Get a high-level summary for the dashboard."""
    projects = project_operations.list_projects(created_by=created_by)
    
    total_budget = 0.0
    total_spent = 0.0
    project_count = len(projects)
    
    for project in projects:
        project_id = project["id"]
        budget_summary = budget_operations.get_project_budget_summary(project_id)
        expense_summary = expense_operations.get_expense_summary(project_id)
        cost_item_summary = cost_item_operations.get_cost_item_summary(project_id)
        
        total_budget += budget_summary["total_budget"]
        total_spent += budget_summary["total_spent"]
        total_spent += expense_summary["total"]
        total_spent += cost_item_summary["total"]
    
    remaining = total_budget - total_spent
    percentage = (total_spent / total_budget * 100) if total_budget > 0 else 0.0
    
    # Determine status
    if percentage >= 100:
        status = "over"
    elif percentage >= 80:
        status = "warning"
    else:
        status = "ok"
    
    return {
        "project_count": project_count,
        "total_budget": total_budget,
        "total_spent": total_spent,
        "remaining": remaining,
        "percentage": percentage,
        "status": status,
        "projects": projects
    }


# Example usage demonstration
if __name__ == "__main__":
    print("Database Operations Helper Module")
    print("=" * 50)
    
    # Initialize database
    if initialize_database_if_needed():
        print("✓ Database initialized")
    else:
        print("✗ Database initialization failed")
        exit(1)
    
    # Example: Create a project
    result = create_project_with_defaults(
        name="Example Project",
        description="A sample project for demonstration",
        created_by="demo_user",
        budget=10000.0
    )
    
    if result["status"]:
        print(f"✓ Project created with ID: {result['id']}")
        project_id = result["id"]
        
        # Set a budget for a category
        budget_result = budget_operations.upsert_budget(
            project_id=project_id,
            category="Materials",
            budget_limit=5000.0
        )
        print(f"✓ Budget set: {budget_result['message']}")
        
        # Add a cost item
        cost_result = add_cost_item_with_auto_budget_update(
            project_id=project_id,
            category="Materials",
            item_name="Cement",
            quantity=10.0,
            unit_cost=50.0,
            note="Foundation materials"
        )
        print(f"✓ Cost item added: {cost_result['message']}")
        
        # Get project summary
        summary = get_project_complete_summary(project_id)
        print(f"\nProject Summary:")
        print(f"  Total Budget: ${summary['total_budget']:.2f}")
        print(f"  Total Spent: ${summary['total_spent']:.2f}")
        print(f"  Remaining: ${summary['budget_remaining']:.2f}")
        
        # Clean up
        delete_project_cascade(project_id)
        print(f"\n✓ Test project deleted")
    else:
        print(f"✗ Failed to create project: {result['message']}")
