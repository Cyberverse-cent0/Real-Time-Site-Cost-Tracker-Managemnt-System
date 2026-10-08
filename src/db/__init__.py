# db/__init__.py
"""Database operations package for Site Cost Tracker.

This package provides two approaches:
1. Centralized database (app_db.py) - All data in one database with tables:
   - users, projects, expenses, cost_items, budgets, user_preferences
   
2. Per-project databases (init_project.py) - Each project in its own SQLite file

The CRUD operation modules (project_operations, expense_operations, etc.)
work with the centralized database approach.
"""

from . import app_db
from . import user_setup
from . import sesion
from . import project_operations
from . import expense_operations
from . import cost_item_operations
from . import budget_operations
from . import operations_helper

__all__ = [
    "app_db",
    "user_setup",
    "sesion",
    "project_operations",
    "expense_operations",
    "cost_item_operations",
    "budget_operations",
    "operations_helper",
]
