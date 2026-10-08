# Database Engine Design and Implementation

## Overview

The Site Cost Tracker uses a dual database approach to support different use cases:

1. **Centralized Database** (`app_db.py`) - Single database for all data
2. **Per-Project Databases** (`init_project.py`) - Separate SQLite file per project

## Centralized Database Architecture

### Database Schema

The centralized database contains the following tables:

#### 1. `users` Table
- Stores user authentication data
- Fields: id, username, password (bcrypt hashed), email, created_at
- Module: `user_setup.py`

#### 2. `projects` Table
- Stores project metadata
- Fields: id, name, description, start_date, budget, created_by, created_at
- Module: `project_operations.py`

#### 3. `expenses` Table
- Stores expense records linked to projects
- Fields: id, project_id (FK), category, notes, amount, expense_date, created_by, created_at
- Module: `expense_operations.py`

#### 4. `cost_items` Table
- Stores detailed cost items with quantity and unit cost
- Fields: id, project_id, category, item_name, quantity, unit_cost, total_cost, note, created_at
- Module: `cost_item_operations.py`

#### 5. `budgets` Table
- Stores budget limits per category per project
- Fields: id, project_id, category, budget_limit, spent_amount, created_at
- Module: `budget_operations.py`

#### 6. `user_preferences` Table
- Stores user UI and application preferences
- Fields: username, prefs_json, updated_at
- Module: `preferences.py`

### Database Backend Support

The system automatically detects and uses the best available backend:

- **PostgreSQL**: Used when `psycopg2` is available and server is reachable
- **SQLite**: Fallback option that works everywhere without configuration

Configuration via environment variables:
```bash
SITE_COST_DB_NAME=site_cost_tracker_prototype_db
SITE_COST_DB_USER=system
SITE_COST_DB_PASSWORD=ESFErvxu88823
SITE_COST_DB_HOST=localhost
SITE_COST_DB_PORT=5432
SITE_COST_DB_BACKEND=postgres  # or sqlite
```

## CRUD Operations Modules

### 1. project_operations.py

**Functions:**
- `create_project(name, description, start_date, budget, created_by)` - Create new project
- `get_project(project_id)` - Get project by ID
- `get_project_by_name(name)` - Get project by name
- `list_projects(created_by=None)` - List all projects or filter by creator
- `update_project(project_id, ...)` - Update project fields
- `delete_project(project_id)` - Delete project (cascades to related tables)
- `project_exists(name)` - Check if project name exists

**Example:**
```python
from db import project_operations

result = project_operations.create_project(
    name="Construction Site A",
    description="Main building construction",
    start_date="2024-01-01",
    budget=100000.0,
    created_by="john_doe"
)
```

### 2. expense_operations.py

**Functions:**
- `create_expense(project_id, category, notes, amount, expense_date, created_by)` - Create expense
- `get_expense(expense_id)` - Get expense by ID
- `list_expenses(project_id=None, category=None, created_by=None, limit=None)` - List with filters
- `update_expense(expense_id, ...)` - Update expense fields
- `delete_expense(expense_id)` - Delete expense
- `get_expense_summary(project_id)` - Get expense totals by category

**Example:**
```python
from db import expense_operations

result = expense_operations.create_expense(
    project_id=1,
    category="Materials",
    notes="Steel beams for framing",
    amount=5000.0,
    expense_date="2024-01-15",
    created_by="john_doe"
)
```

### 3. cost_item_operations.py

**Functions:**
- `create_cost_item(project_id, category, item_name, quantity, unit_cost, total_cost, note)` - Create cost item
- `get_cost_item(item_id)` - Get cost item by ID
- `list_cost_items(project_id=None, category=None, limit=None)` - List with filters
- `update_cost_item(item_id, ...)` - Update cost item fields
- `delete_cost_item(item_id)` - Delete cost item
- `get_cost_item_summary(project_id)` - Get cost item totals by category

**Example:**
```python
from db import cost_item_operations

result = cost_item_operations.create_cost_item(
    project_id=1,
    category="Materials",
    item_name="Cement bags",
    quantity=50.0,
    unit_cost=12.0,
    total_cost=600.0,
    note="Foundation materials"
)
```

### 4. budget_operations.py

**Functions:**
- `create_budget(project_id, category, budget_limit, spent_amount=0.0)` - Create budget
- `get_budget(budget_id)` - Get budget by ID
- `get_budget_by_project_category(project_id, category)` - Get budget by project & category
- `list_budgets(project_id=None)` - List budgets
- `update_budget(budget_id, ...)` - Update budget fields
- `upsert_budget(project_id, category, budget_limit)` - Insert or update budget
- `delete_budget(budget_id)` - Delete budget
- `update_spent_amount(project_id, category, amount)` - Add to spent amount
- `get_budget_status(project_id, category)` - Get budget usage status
- `get_project_budget_summary(project_id)` - Get complete budget summary

**Example:**
```python
from db import budget_operations

result = budget_operations.upsert_budget(
    project_id=1,
    category="Materials",
    budget_limit=50000.0
)

status = budget_operations.get_budget_status(1, "Materials")
print(f"Budget status: {status['percentage']:.1f}% used")
```

## Helper Module (operations_helper.py)

The `operations_helper.py` module provides high-level helper functions for common operations:

- `initialize_database_if_needed()` - Initialize database if not exists
- `create_project_with_defaults()` - Create project with sensible defaults
- `get_project_complete_summary(project_id)` - Get complete project summary
- `add_expense_with_auto_budget_update()` - Add expense and update budget
- `add_cost_item_with_auto_budget_update()` - Add cost item and update budget
- `get_user_projects(created_by)` - Get all projects for a user with summaries
- `delete_project_cascade(project_id)` - Delete project (cascades via FK)
- `get_dashboard_summary(created_by)` - Get dashboard-level summary

**Example:**
```python
from db import operations_helper

# Initialize database
operations_helper.initialize_database_if_needed()

# Create project
result = operations_helper.create_project_with_defaults(
    name="My Project",
    description="Sample project",
    created_by="user123"
)

# Add cost item with automatic budget update
operations_helper.add_cost_item_with_auto_budget_update(
    project_id=result["id"],
    category="Materials",
    item_name="Steel",
    quantity=100.0,
    unit_cost=50.0
)

# Get complete summary
summary = operations_helper.get_project_complete_summary(result["id"])
print(f"Total spent: ${summary['total_spent']:.2f}")
```

## Error Handling

All CRUD operations return a standardized response dictionary:

```python
{
    "status": True/False,
    "message": "Human-readable message",
    "id": created_id (for create operations),
    "return_code": HTTP-like status code
}
```

Common return codes:
- `200` - Success
- `201` - Created
- `400` - Bad request (validation error)
- `404` - Not found
- `409` - Conflict (duplicate)
- `500` - Internal server error
- `503` - Service unavailable (database connection error)

## Foreign Key Constraints

The database uses foreign key constraints with CASCADE delete:
- `expenses.project_id` → `projects.id` (ON DELETE CASCADE)
- `cost_items.project_id` → `projects.id` (no FK constraint in current schema)
- `budgets.project_id` → `projects.id` (no FK constraint in current schema)

**Note:** Deleting a project will automatically delete all related expenses.

## Testing

Run the helper module to test the database operations:

```bash
python src/db/operations_helper.py
```

This will:
1. Initialize the database
2. Create a test project
3. Set a budget
4. Add a cost item
5. Display summary
6. Clean up by deleting the test project

## Integration with Dashboard

The dashboard (`dashboard.py`) currently uses the per-project database approach (`init_project.py`). To integrate the centralized database:

1. Replace `ProjectDatabase` calls with the appropriate CRUD operations
2. Use `operations_helper.get_dashboard_summary()` for the home view
3. Use `operations_helper.get_user_projects()` for the projects view
4. Use `operations_helper.get_project_complete_summary()` for project details

## Security Notes

- Passwords are hashed using bcrypt before storage
- Database credentials should be stored in environment variables
- The system uses parameterized queries to prevent SQL injection
- SQLite database file is in the `data/` directory (gitignored)

## Performance Considerations

- PostgreSQL is recommended for production deployments
- SQLite is suitable for development and small deployments
- Consider adding indexes on frequently queried columns:
  - `projects.created_by`
  - `expenses.project_id`, `expenses.category`
  - `cost_items.project_id`, `cost_items.category`
  - `budgets.project_id`, `budgets.category`
