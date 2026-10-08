# init_project.py
"""Project & expense data model.

Each project lives in its own SQLite database file under
~/site_cost_projects/ (override with SITE_COST_PROJECTS_DIR), containing:

    projects   – one row describing the project
    cost_items – every logged cost (quantity x unit_cost)
    budgets    – optional spending limit per category

The class offers the full write side (create project, log cost item, set
budget) and read side (list projects, items, summaries, alerts) used by
the dashboard UI.
"""
import os
import sqlite3
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Optional

CATEGORIES = ("Labor", "Materials", "Equipment", "Subcontractor", "Miscellaneous")

# Budget usage thresholds for alerts.
WARN_THRESHOLD = 0.80      # approaching the category budget
DANGER_THRESHOLD = 1.00    # at/over the category budget

PROJECTS_DIR = Path(os.environ.get(
    "SITE_COST_PROJECTS_DIR", str(Path.home() / "site_cost_projects")))


def format_money(amount: float) -> str:
    sign = "-" if amount < 0 else ""
    return f"{sign}${abs(amount):,.2f}"


@dataclass
class Error:
    message: str
    status: bool = False
    suggestion: Optional[str] = None


@dataclass
class BudgetStatus:
    fraction: float
    tone: str  # success | warning | danger

    @property
    def label(self) -> str:
        if self.fraction >= DANGER_THRESHOLD:
            return "Over budget"
        if self.fraction >= WARN_THRESHOLD:
            return "Near budget"
        return "On budget"


def budget_status(budget: float, spent: float) -> BudgetStatus:
    fraction = (spent / budget) if budget > 0 else 0.0
    if fraction >= DANGER_THRESHOLD:
        tone = "danger"
    elif fraction >= WARN_THRESHOLD:
        tone = "warning"
    else:
        tone = "success"
    return BudgetStatus(fraction=fraction, tone=tone)


def safe_name(name: str) -> str:
    return "".join(ch if ch.isalnum() or ch in "-_" else "_"
                   for ch in name.strip().lower().replace(" ", "_"))


class ProjectDatabase:
    def __init__(self):
        self.ProjectName: Optional[str] = None
        self.ProjectDescription: Optional[str] = None
        self.ProjectStartDate: Optional[date] = None
        self.ProjectPath: Optional[str] = None

    # ---------------- validation ----------------
    def validate_project(self) -> Optional[Error]:
        """Validate the fields on this instance.

        Returns None on success, an Error otherwise. Error(status=True)
        marks a *warning* the caller may accept (e.g. defaulting a date).
        """
        if not self.ProjectName or not self.ProjectName.strip():
            return Error(
                message="Project name is required.",
                status=False,
                suggestion="Please provide a name for the project.",
            )

        cleaned_name = self.ProjectName.strip()
        if len(cleaned_name) < 3:
            return Error(
                message="Project name must be at least 3 characters long.",
                status=False,
                suggestion="Please provide a longer project name.",
            )

        if len(cleaned_name) > 50:
            return Error(
                message="Project name must not exceed 50 characters.",
                status=False,
                suggestion="Please provide a shorter project name.",
            )

        if not self.ProjectDescription or not self.ProjectDescription.strip():
            return Error(
                message="Project description is required.",
                status=False,
                suggestion="Write a detailed description for the project.",
            )

        if not self.ProjectStartDate:
            self.ProjectStartDate = date.today()
            return Error(
                message="Date is empty. Using today's date.",
                status=True,
                suggestion="Proceed with today's date or select a different date.",
            )

        if not self.ProjectPath:
            self.ProjectPath = str(PROJECTS_DIR)
            return Error(
                message="Project path is empty.",
                status=True,
                suggestion="Using the default project directory.",
            )

        return None

    # Backwards-compatible alias (previous spelling).
    vlidate_project = validate_project

    # ---------------- paths / connections ----------------
    @staticmethod
    def project_db_path(name: str) -> Path:
        PROJECTS_DIR.mkdir(parents=True, exist_ok=True)
        return PROJECTS_DIR / f"{safe_name(name)}.db"

    def _project_db_path(self) -> Path:
        if not self.ProjectName:
            PROJECTS_DIR.mkdir(parents=True, exist_ok=True)
            return PROJECTS_DIR / "unnamed.db"
        return self.project_db_path(self.ProjectName)

    @staticmethod
    def _connect(db_path: Path) -> sqlite3.Connection:
        db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.row_factory = sqlite3.Row
        return conn

    @staticmethod
    def _create_project_tables(conn: sqlite3.Connection) -> None:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                start_date TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS cost_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                category TEXT NOT NULL,
                item_name TEXT NOT NULL,
                quantity REAL DEFAULT 0,
                unit_cost REAL DEFAULT 0,
                total_cost REAL DEFAULT 0,
                note TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(project_id) REFERENCES projects(id)
            );
            CREATE TABLE IF NOT EXISTS budgets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                category TEXT NOT NULL,
                budget_limit REAL NOT NULL DEFAULT 0,
                spent_amount REAL NOT NULL DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(project_id) REFERENCES projects(id)
            );
            """
        )
        project_columns = {
            row["name"] for row in conn.execute("PRAGMA table_info(projects)")
        }
        if "created_at" not in project_columns:
            conn.execute("ALTER TABLE projects ADD COLUMN created_at TEXT")
            conn.execute(
                "UPDATE projects SET created_at = CURRENT_TIMESTAMP "
                "WHERE created_at IS NULL"
            )

    def ensure_project_tables(self, project: str) -> bool:
        """Create missing project tables in that project's existing database."""
        db_path = self.project_db_path(project)
        if not db_path.exists():
            return False
        conn = None
        try:
            conn = self._connect(db_path)
            self._create_project_tables(conn)
            conn.commit()
            return True
        except sqlite3.Error as exc:
            print(f"Error initializing tables for {project}: {exc}")
            return False
        finally:
            if conn is not None:
                conn.close()

    # ---------------- write side ----------------
    def create_project_database(self) -> bool:
        """Create (or refuse to duplicate) a project database. Returns True on success."""
        validation_error = self.validate_project()
        if validation_error and not validation_error.status:
            print(validation_error.message)
            return False

        db_path = self.project_db_path(self.ProjectName.strip())
        if db_path.exists():
            print(f"A project named '{self.ProjectName.strip()}' already exists.")
            return False
        self.ProjectPath = str(db_path.parent)

        try:
            conn = self._connect(db_path)
            self._create_project_tables(conn)
            cur = conn.cursor()

            cur.execute(
                """
                INSERT INTO projects (name, description, start_date)
                VALUES (?, ?, ?)
                ON CONFLICT(name) DO NOTHING
                """,
                (
                    self.ProjectName.strip(),
                    self.ProjectDescription.strip(),
                    self.ProjectStartDate.isoformat(),
                ),
            )

            conn.commit()
            cur.close()
            conn.close()
            return True
        except Exception as exc:
            print(f"Error creating project database: {exc}")
            return False

    def create_default_tables(self) -> bool:
        """Compatibility helper for callers expecting a separate table setup method."""
        return self.create_project_database()

    # ---------------- read side ----------------
    def list_all_projects(self) -> list[dict]:
        """Every project on disk with its totals (for the dashboard)."""
        results: list[dict] = []
        if not PROJECTS_DIR.exists():
            return results
        for db_file in sorted(PROJECTS_DIR.glob("*.db")):
            try:
                conn = self._connect(db_file)
                self._create_project_tables(conn)
                conn.commit()
                cur = conn.cursor()
                row = cur.execute(
                    "SELECT name, description, start_date, created_at FROM projects LIMIT 1;"
                ).fetchone()
                if row is None:
                    cur.close()
                    conn.close()
                    continue
                totals = cur.execute(
                    "SELECT COALESCE(SUM(total_cost), 0) AS spent,"
                    " COUNT(*) AS items FROM cost_items;"
                ).fetchone()
                budget = cur.execute(
                    "SELECT COALESCE(SUM(budget_limit), 0) AS total FROM budgets;"
                ).fetchone()
                cur.close()
                conn.close()

                budget_total = float(budget["total"] or 0)
                spent = float(totals["spent"] or 0)
                results.append({
                    "name": row["name"],
                    "description": row["description"] or "",
                    "start_date": row["start_date"],
                    "created_at": row["created_at"],
                    "path": str(db_file),
                    "item_count": int(totals["items"] or 0),
                    "budget": round(budget_total, 2),
                    "spent": round(spent, 2),
                    "remaining": round(budget_total - spent, 2),
                    "status": budget_status(budget_total, spent),
                })
            except sqlite3.Error as exc:
                print(f"Skipping {db_file.name}: {exc}")
        return results

    def add_cost_item(self, project: str, category: str, item_name: str,
                      quantity: float, unit_cost: float, note: str = "") -> dict:
        """Log a cost item into a project database."""
        name = (item_name or "").strip()
        if not name:
            return {"status": False, "message": "Item name is required."}
        if category not in CATEGORIES:
            return {"status": False,
                    "message": f"Category must be one of: {', '.join(CATEGORIES)}"}
        try:
            qty = float(quantity)
            cost = float(unit_cost)
        except (TypeError, ValueError):
            return {"status": False, "message": "Quantity and unit cost must be numbers."}
        if qty < 0 or cost < 0:
            return {"status": False, "message": "Quantity and unit cost cannot be negative."}

        db_path = self.project_db_path(project)
        if not db_path.exists():
            return {"status": False,
                    "message": f"Project '{project}' does not exist."}

        try:
            conn = self._connect(db_path)
            cur = conn.cursor()
            cur.execute("SELECT id FROM projects LIMIT 1;")
            row = cur.fetchone()
            if row is None:
                cur.close()
                conn.close()
                return {"status": False, "message": "Project record missing."}
            project_id = row["id"]
            cur.execute(
                """
                INSERT INTO cost_items (project_id, category, item_name,
                                        quantity, unit_cost, total_cost, note)
                VALUES (?, ?, ?, ?, ?, ?, ?);
                """,
                (project_id, category, name, qty, cost, round(qty * cost, 2),
                 (note or "").strip()),
            )
            new_id = cur.lastrowid
            conn.commit()
            cur.close()
            conn.close()
            return {"status": True, "message": "Cost item logged", "id": new_id}
        except Exception as exc:
            print(f"Error adding cost item: {exc}")
            return {"status": False, "message": str(exc)}

    def list_cost_items(self, project: str, category: str | None = None,
                        limit: int | None = None) -> list[dict]:
        db_path = self.project_db_path(project)
        if not db_path.exists():
            return []
        try:
            conn = self._connect(db_path)
            cur = conn.cursor()
            sql = "SELECT id, category, item_name, quantity, unit_cost, total_cost," \
                  " note, created_at FROM cost_items"
            params: list = []
            if category:
                sql += " WHERE category = ?"
                params.append(category)
            sql += " ORDER BY id DESC"
            if limit:
                sql += " LIMIT ?"
                params.append(int(limit))
            rows = [dict(r) for r in cur.execute(sql, tuple(params)).fetchall()]
            cur.close()
            conn.close()
            for r in rows:
                for field in ("quantity", "unit_cost", "total_cost"):
                    r[field] = float(r[field] or 0)
            return rows
        except sqlite3.Error as exc:
            print(f"Error listing cost items: {exc}")
            return []

    def set_category_budget(self, project: str, category: str, limit: float) -> dict:
        """Insert or update the budget limit for one category."""
        if category not in CATEGORIES:
            return {"status": False,
                    "message": f"Category must be one of: {', '.join(CATEGORIES)}"}
        try:
            value = round(float(limit), 2)
        except (TypeError, ValueError):
            return {"status": False, "message": "Budget limit must be a number."}
        if value < 0:
            return {"status": False, "message": "Budget limit cannot be negative."}

        db_path = self.project_db_path(project)
        if not db_path.exists():
            return {"status": False, "message": f"Project '{project}' does not exist."}
        try:
            conn = self._connect(db_path)
            cur = conn.cursor()
            cur.execute("SELECT id FROM projects LIMIT 1;")
            row = cur.fetchone()
            if row is None:
                cur.close()
                conn.close()
                return {"status": False, "message": "Project record missing."}
            project_id = row["id"]
            # Manual upsert (the budgets table has no UNIQUE(project_id, category)
            # constraint, so ON CONFLICT cannot be used here).
            existing = cur.execute(
                "SELECT id FROM budgets WHERE project_id = ? AND category = ?;",
                (project_id, category),
            ).fetchone()
            if existing is not None:
                cur.execute(
                    "UPDATE budgets SET budget_limit = ? WHERE id = ?;",
                    (value, existing["id"]),
                )
            else:
                cur.execute(
                    """
                    INSERT INTO budgets (project_id, category, budget_limit, spent_amount)
                    VALUES (?, ?, ?, 0);
                    """,
                    (project_id, category, value),
                )
            conn.commit()
            cur.close()
            conn.close()
            return {"status": True, "message": "Budget saved"}
        except Exception as exc:
            print(f"Error setting budget: {exc}")
            return {"status": False, "message": str(exc)}

    def project_summary(self, project: str) -> dict:
        """Totals per category with budget comparison + alert status."""
        db_path = self.project_db_path(project)
        summary = {
            "name": project,
            "exists": db_path.exists(),
            "categories": [],
            "budget": 0.0,
            "spent": 0.0,
            "remaining": 0.0,
            "status": budget_status(0.0, 0.0),
        }
        if not db_path.exists():
            return summary
        try:
            conn = self._connect(db_path)
            cur = conn.cursor()
            budgets = {r["category"]: float(r["budget_limit"] or 0)
                       for r in cur.execute("SELECT category, budget_limit FROM budgets;")}
            spent_rows = cur.execute(
                "SELECT category, COALESCE(SUM(total_cost), 0) AS total,"
                " COUNT(*) AS n FROM cost_items GROUP BY category;"
            ).fetchall()
            cur.close()
            conn.close()

            spent_map = {r["category"]: float(r["total"] or 0) for r in spent_rows}
            counts = {r["category"]: int(r["n"] or 0) for r in spent_rows}
            cats = []
            for cat in CATEGORIES:
                b = round(budgets.get(cat, 0.0), 2)
                s = round(spent_map.get(cat, 0.0), 2)
                cats.append({
                    "category": cat,
                    "budget": b,
                    "spent": s,
                    "remaining": round(b - s, 2),
                    "items": counts.get(cat, 0),
                    "status": budget_status(b, s),
                })
            total_budget = round(sum(c["budget"] for c in cats), 2)
            total_spent = round(sum(c["spent"] for c in cats), 2)
            summary.update({
                "categories": cats,
                "budget": total_budget,
                "spent": total_spent,
                "remaining": round(total_budget - total_spent, 2),
                "status": budget_status(total_budget, total_spent),
            })
            return summary
        except sqlite3.Error as exc:
            print(f"Error building summary: {exc}")
            return summary

    def delete_project(self, project: str) -> bool:
        """Delete a project database file (cost items go with it)."""
        db_path = self.project_db_path(project)
        if not db_path.exists():
            return False
        try:
            db_path.unlink()
            return True
        except OSError as exc:
            print(f"Error deleting project: {exc}")
            return False

    def delete_cost_item(self, project: str, item_id: int) -> dict:
        """Remove one logged cost item by id."""
        db_path = self.project_db_path(project)
        if not db_path.exists():
            return {"status": False, "message": f"Project '{project}' does not exist."}
        try:
            conn = self._connect(db_path)
            cur = conn.cursor()
            cur.execute("DELETE FROM cost_items WHERE id = ?;", (int(item_id),))
            deleted = cur.rowcount
            conn.commit()
            cur.close()
            conn.close()
            if deleted:
                return {"status": True, "message": "Cost item deleted"}
            return {"status": False, "message": "Cost item not found."}
        except Exception as exc:
            print(f"Error deleting cost item: {exc}")
            return {"status": False, "message": str(exc)}

    def remove_category_budget(self, project: str, category: str) -> dict:
        """Delete the budget row for one category (logged spend is kept)."""
        db_path = self.project_db_path(project)
        if not db_path.exists():
            return {"status": False, "message": f"Project '{project}' does not exist."}
        try:
            conn = self._connect(db_path)
            cur = conn.cursor()
            cur.execute(
                """
                DELETE FROM budgets
                WHERE category = ?
                  AND project_id = (SELECT id FROM projects LIMIT 1);
                """,
                (category,),
            )
            deleted = cur.rowcount
            conn.commit()
            cur.close()
            conn.close()
            if deleted:
                return {"status": True, "message": "Budget removed"}
            return {"status": False, "message": "No budget set for that category."}
        except Exception as exc:
            print(f"Error removing budget: {exc}")
            return {"status": False, "message": str(exc)}

    # ---------------- dashboard aggregate ----------------
    def dashboard_totals(self) -> dict:
        projects = self.list_all_projects()
        total_budget = sum(p["budget"] for p in projects)
        total_spent = sum(p["spent"] for p in projects)
        by_category = {c: 0.0 for c in CATEGORIES}
        for project in projects:
            summary = self.project_summary(project["name"])
            for cat in summary["categories"]:
                by_category[cat["category"]] += cat["spent"]
        alerts = [p for p in projects
                  if p["budget"] > 0 and p["status"].fraction >= WARN_THRESHOLD]
        return {
            "projects": projects,
            "project_count": len(projects),
            "total_budget": round(total_budget, 2),
            "total_spent": round(total_spent, 2),
            "remaining": round(total_budget - total_spent, 2),
            "by_category": {k: round(v, 2) for k, v in by_category.items()},
            "status": budget_status(total_budget, total_spent),
            "alerts": alerts,
        }
