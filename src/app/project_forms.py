from datetime import date
from pathlib import Path
from tkinter import ttk
import tkinter as tk

from .init_project import ProjectDatabase, CATEGORIES, PROJECTS_DIR
from .theme import theme, get_font, apply_button_style, apply_entry_style, apply_label_style, create_card_frame
from ui.context_menu import attach_entry_menu


DEFAULT_PROJECT_DIR = PROJECTS_DIR
DEFAULT_DB_NAME = "default_project.db"


def ensure_default_project_db() -> Path:
    DEFAULT_PROJECT_DIR.mkdir(parents=True, exist_ok=True)
    db_path = ProjectDatabase.project_db_path("Default Project")
    project = ProjectDatabase()
    project.ProjectName = "Default Project"
    project.ProjectDescription = "Default project for site cost tracking"
    project.ProjectStartDate = date.today()
    project.ProjectPath = str(DEFAULT_PROJECT_DIR)
    project.create_project_database()
    return db_path


def load_projects(db_path: str | None = None):
    """All project names across per-project databases (model layer)."""
    return [(name, name) for name in sorted(
        p["name"] for p in ProjectDatabase().list_all_projects())]


class ProjectEntryForm:
    def __init__(self, parent: tk.Widget, on_save=None):
        self.parent = parent
        self.on_save = on_save
        self.frame = create_card_frame(parent)
        self.frame.pack(fill="both", expand=True, padx=16, pady=16)
        self._build_form()

    def _build_form(self):
        colors = theme.colors
        spacing = theme.spacing

        title = tk.Label(self.frame, text="Create Project", bg=colors.bg_card)
        apply_label_style(title, variant="subtitle")
        title.pack(anchor="w", padx=spacing.lg, pady=(spacing.lg, spacing.md))

        form = tk.Frame(self.frame, bg=colors.bg_card)
        form.pack(fill="both", expand=True, padx=spacing.lg, pady=(0, spacing.lg))

        entries = {}

        tk.Label(form, text="Project name", bg=colors.bg_card).pack(anchor="w", pady=(0, 4))
        name_var = tk.StringVar()
        name_entry = tk.Entry(form, textvariable=name_var, width=40)
        apply_entry_style(name_entry)
        name_entry.pack(fill="x", pady=(0, 12))
        attach_entry_menu(name_entry)
        entries["name"] = name_var

        tk.Label(form, text="Description", bg=colors.bg_card).pack(anchor="w", pady=(0, 4))
        desc_var = tk.StringVar()
        desc_entry = tk.Entry(form, textvariable=desc_var, width=40)
        apply_entry_style(desc_entry)
        desc_entry.pack(fill="x", pady=(0, 12))
        attach_entry_menu(desc_entry)
        entries["description"] = desc_var

        tk.Label(form, text="Start date", bg=colors.bg_card).pack(anchor="w", pady=(0, 4))
        start_var = tk.StringVar(value=str(date.today()))
        start_entry = tk.Entry(form, textvariable=start_var, width=40)
        apply_entry_style(start_entry)
        start_entry.pack(fill="x", pady=(0, 12))
        attach_entry_menu(start_entry)
        entries["start_date"] = start_var

        status_label = tk.Label(form, text="", bg=colors.bg_card, fg=colors.error)
        status_label.pack(anchor="w", pady=(0, 8))

        def save_project():
            name = entries["name"].get().strip()
            description = entries["description"].get().strip()
            start_date = entries["start_date"].get().strip()

            if not name or not description:
                status_label.config(text="Project name and description are required.")
                return

            project = ProjectDatabase()
            project.ProjectName = name
            project.ProjectDescription = description
            project.ProjectPath = str(DEFAULT_PROJECT_DIR)
            if start_date:
                try:
                    project.ProjectStartDate = date.fromisoformat(start_date)
                except ValueError:
                    status_label.config(text="Start date must be in YYYY-MM-DD format.")
                    return
            else:
                project.ProjectStartDate = date.today()

            if project.create_project_database():
                status_label.config(text="Project saved successfully.", fg=colors.success)
                if self.on_save:
                    self.on_save()
            else:
                status_label.config(text="Project could not be saved.", fg=colors.error)

        btn_row = tk.Frame(form, bg=colors.bg_card)
        btn_row.pack(fill="x", pady=(12, 0))

        save_btn = tk.Button(btn_row, text="Save Project", command=save_project)
        apply_button_style(save_btn, variant="primary", size="medium")
        save_btn.pack(side="left")


class CostItemEntryForm:
    def __init__(self, parent: tk.Widget, on_save=None, selected_project: str | None = None):
        self.parent = parent
        self.on_save = on_save
        self.selected_project = selected_project
        self.frame = create_card_frame(parent)
        self.frame.pack(fill="both", expand=True, padx=16, pady=16)
        self._build_form()

    def _build_form(self):
        colors = theme.colors
        spacing = theme.spacing

        title = tk.Label(self.frame, text="Add Cost Item", bg=colors.bg_card)
        apply_label_style(title, variant="subtitle")
        title.pack(anchor="w", padx=spacing.lg, pady=(spacing.lg, spacing.md))

        form = tk.Frame(self.frame, bg=colors.bg_card)
        form.pack(fill="both", expand=True, padx=spacing.lg, pady=(0, spacing.lg))

        project_names = [name for name, _ in load_projects()]
        project_var = tk.StringVar(value=self.selected_project or (project_names[0] if project_names else ""))
        if self.selected_project:
            tk.Label(form, text=f"Project: {self.selected_project}", bg=colors.bg_card).pack(anchor="w", pady=(0, 12))
        else:
            ttk.OptionMenu(form, project_var, project_var.get(), *project_names or [""]).pack(fill="x", pady=(0, 12))

        tk.Label(form, text="Category", bg=colors.bg_card).pack(anchor="w", pady=(0, 4))
        category_var = tk.StringVar(value=CATEGORIES[0])
        category_combo = ttk.Combobox(form, textvariable=category_var, state="readonly",
                                      values=list(CATEGORIES))
        category_combo.pack(fill="x", pady=(0, 12))

        fields = {
            "item_name": ("Item name", ""),
            "quantity": ("Quantity", "1"),
            "unit_cost": ("Unit cost", "0"),
            "note": ("Note", ""),
        }

        widgets = {}
        for key, (label_text, default) in fields.items():
            tk.Label(form, text=label_text, bg=colors.bg_card).pack(anchor="w", pady=(0, 4))
            var = tk.StringVar(value=default)
            entry = tk.Entry(form, textvariable=var, width=40)
            apply_entry_style(entry)
            entry.pack(fill="x", pady=(0, 12))
            attach_entry_menu(entry)
            widgets[key] = var

        status_label = tk.Label(form, text="", bg=colors.bg_card, fg=colors.error)
        status_label.pack(anchor="w", pady=(0, 8))

        def save_item():
            project_name = project_var.get().strip() or "Default Project"
            category = category_var.get().strip()
            item_name = widgets["item_name"].get().strip()
            try:
                quantity = float(widgets["quantity"].get())
                unit_cost = float(widgets["unit_cost"].get())
            except ValueError:
                status_label.config(text="Quantity and unit cost must be numeric.", fg=colors.error)
                return

            if not item_name:
                status_label.config(text="Item name is required.", fg=colors.error)
                return

            result = ProjectDatabase().add_cost_item(
                project=project_name,
                category=category,
                item_name=item_name,
                quantity=quantity,
                unit_cost=unit_cost,
                note=widgets["note"].get().strip(),
            )
            if result["status"]:
                status_label.config(text=result["message"] + " successfully.", fg=colors.success)
                if self.on_save:
                    self.on_save()
            else:
                status_label.config(text=result["message"], fg=colors.error)

        btn_row = tk.Frame(form, bg=colors.bg_card)
        btn_row.pack(fill="x", pady=(12, 0))

        save_btn = tk.Button(btn_row, text="Save Cost Item", command=save_item)
        apply_button_style(save_btn, variant="success", size="medium")
        save_btn.pack(side="left")


class BudgetEntryForm:
    def __init__(self, parent: tk.Widget, on_save=None, selected_project: str | None = None):
        self.parent = parent
        self.on_save = on_save
        self.selected_project = selected_project
        self.frame = create_card_frame(parent)
        self.frame.pack(fill="both", expand=True, padx=16, pady=16)
        self._build_form()

    def _build_form(self):
        colors = theme.colors
        spacing = theme.spacing

        title = tk.Label(self.frame, text="Add Budget", bg=colors.bg_card)
        apply_label_style(title, variant="subtitle")
        title.pack(anchor="w", padx=spacing.lg, pady=(spacing.lg, spacing.md))

        form = tk.Frame(self.frame, bg=colors.bg_card)
        form.pack(fill="both", expand=True, padx=spacing.lg, pady=(0, spacing.lg))

        project_names = [name for name, _ in load_projects()]
        project_var = tk.StringVar(value=self.selected_project or (project_names[0] if project_names else ""))
        if self.selected_project:
            tk.Label(form, text=f"Project: {self.selected_project}", bg=colors.bg_card).pack(anchor="w", pady=(0, 12))
        else:
            ttk.OptionMenu(form, project_var, project_var.get(), *project_names or [""]).pack(fill="x", pady=(0, 12))

        tk.Label(form, text="Category", bg=colors.bg_card).pack(anchor="w", pady=(0, 4))
        category_var = tk.StringVar(value=CATEGORIES[0])
        category_combo = ttk.Combobox(form, textvariable=category_var, state="readonly",
                                      values=list(CATEGORIES))
        category_combo.pack(fill="x", pady=(0, 12))

        tk.Label(form, text="Budget limit", bg=colors.bg_card).pack(anchor="w", pady=(0, 4))
        limit_var = tk.StringVar(value="0")
        limit_entry = tk.Entry(form, textvariable=limit_var, width=40)
        apply_entry_style(limit_entry)
        limit_entry.pack(fill="x", pady=(0, 12))
        attach_entry_menu(limit_entry)

        status_label = tk.Label(form, text="", bg=colors.bg_card, fg=colors.error)
        status_label.pack(anchor="w", pady=(0, 8))

        def save_budget():
            project_name = project_var.get().strip() or "Default Project"
            category = category_var.get().strip()
            try:
                budget_limit = float(limit_var.get())
            except ValueError:
                status_label.config(text="Budget limit must be numeric.", fg=colors.error)
                return

            # Model layer handles validation and upserts (re-saving a category
            # updates its limit instead of inserting a duplicate row).
            result = ProjectDatabase().set_category_budget(
                project=project_name, category=category, limit=budget_limit)
            if result["status"]:
                status_label.config(text=result["message"] + " successfully.", fg=colors.success)
                if self.on_save:
                    self.on_save()
            else:
                status_label.config(text=result["message"], fg=colors.error)

        btn_row = tk.Frame(form, bg=colors.bg_card)
        btn_row.pack(fill="x", pady=(12, 0))

        save_btn = tk.Button(btn_row, text="Save Budget", command=save_budget)
        apply_button_style(save_btn, variant="secondary", size="medium")
        save_btn.pack(side="left")
