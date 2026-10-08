# dashboard.py
import tkinter as tk
import typing
import pathlib
from tkinter import ttk
from tkinter import messagebox
from .theme import theme, get_font, apply_button_style, apply_label_style, create_card_frame
from .sidebar import Sidebar, Icon
from .preferences_ui import PreferencesPage
from .project_forms import ProjectEntryForm, CostItemEntryForm, BudgetEntryForm
from ui.context_menu import (
    ContextItem,
    bind_context_menu,
    bind_context_menu_all,
    bind_treeview_context_menu,
    copy_text,
    header as menu_header,
    separator as menu_separator,
)

try:
    from ..db import app_db
except ImportError:  # pragma: no cover - compatibility when run from src root
    from db import app_db


class Dashboard:
    """Main dashboard with sidebar, header, and content area."""
    
    def __init__(self, parent: tk.Widget, username: str = "User"):
        self.parent = parent
        self.username = username
        self.colors = theme.colors
        
        # Initialize preferences system
        try:
            from .preferences import PreferencesEngine
            self.prefs_engine = PreferencesEngine(username)
        except Exception:
            self.prefs_engine = None
        
        # Main container
        self.main_container = tk.Frame(parent, bg=self.colors.bg_main)
        self.main_container.pack(fill="both", expand=True)
        
        # Create sidebar
        self.sidebar = Sidebar(self.main_container)
        
        # Create content area (right side)
        self.content_area = tk.Frame(self.main_container, bg=self.colors.bg_main)
        self.content_area.pack(side="right", fill="both", expand=True)
        
        # Create header
        self.header = self._create_header()
        
        # Create main content frame
        self.content_frame = tk.Frame(self.content_area, bg=self.colors.bg_main)
        self.content_frame.pack(fill="both", expand=True, padx=theme.spacing.lg, pady=theme.spacing.lg)

        # Right-click on empty content area: view navigation + refresh
        bind_context_menu(self.content_frame, self._background_menu_items)

        # Data model (per-project SQLite files) + view tracking
        from .init_project import ProjectDatabase
        self.model = ProjectDatabase()
        self._current_view = "home"
        from ui.theme.engine import get_engine
        get_engine().add_listener(self.main_container, self._on_theme_changed)

        # Add navigation items to sidebar
        self._add_navigation()

        # Show default view
        self.show_home_view()

    def _on_theme_changed(self):
        """Re-render the current view when the theme changes."""
        t = theme.colors
        try:
            self.main_container.config(bg=t.bg_main)
            self.content_area.config(bg=t.bg_main)
            self.content_frame.config(bg=t.bg_main)
            self._refresh_current_view()
        except tk.TclError:
            pass  # widgets already destroyed (logout)

    def _refresh_current_view(self):
        """Re-render whatever view is currently shown."""
        views = {
            "home": self.show_home_view,
            "projects": self.show_projects_view,
            "form": self.show_project_form_view,
            "expenses": self.show_expenses_view,
            "reports": self.show_reports_view,
            "settings": self.show_settings_view,
        }
        views.get(self._current_view, self.show_home_view)()

    def _background_menu_items(self):
        """Navigation menu for right-clicks on the content background."""
        return [
            menu_header("Go to"),
            ContextItem("Home", self.show_home_view, glyph="⌂"),
            ContextItem("Projects", self.show_projects_view, glyph="▦"),
            ContextItem("New entry", self.show_project_form_view, glyph="✓"),
            ContextItem("Expenses", self.show_expenses_view, glyph="🧾"),
            ContextItem("Reports", self.show_reports_view, glyph="📋"),
            ContextItem("Settings", self.show_settings_view, glyph="⚙"),
            menu_separator(),
            ContextItem("Refresh view", self._refresh_current_view, glyph="⟳"),
        ]
    
    def _create_header(self) -> tk.Frame:
        """Create the dashboard header."""
        colors = self.colors
        spacing = theme.spacing
        
        header = tk.Frame(
            self.content_area,
            bg=colors.bg_card,
            height=theme.header_height
        )
        header.pack(fill="x", side="top")
        header.pack_propagate(False)
        
        # Left side - Title
        title_frame = tk.Frame(header, bg=colors.bg_card)
        title_frame.pack(side="left", padx=spacing.lg, pady=spacing.md)
        
        title_label = tk.Label(
            title_frame,
            text="Dashboard",
            bg=colors.bg_card
        )
        apply_label_style(title_label, variant="subtitle")
        title_label.pack(side="left")
        
        # Right side - User info and actions
        actions_frame = tk.Frame(header, bg=colors.bg_card)
        actions_frame.pack(side="right", padx=spacing.lg, pady=spacing.md)
        
        # User avatar/initials
        avatar_frame = tk.Frame(
            actions_frame,
            bg=colors.primary,
            width=40,
            height=40
        )
        avatar_frame.pack(side="right", padx=spacing.sm)
        avatar_frame.pack_propagate(False)
        
        initials = self.username[0].upper() if self.username else "U"
        avatar_label = tk.Label(
            avatar_frame,
            text=initials,
            bg=colors.primary,
            fg=colors.text_white,
            font=get_font(theme.fonts.title_small, bold=True)
        )
        avatar_label.pack(expand=True)
        
        # User name
        user_label = tk.Label(
            actions_frame,
            text=self.username,
            bg=colors.bg_card
        )
        apply_label_style(user_label, variant="body")
        user_label.pack(side="right", padx=(spacing.sm, spacing.xs))
        
        # Notification bell + appearance button (SVGs can't load in tk.PhotoImage)
        actions_frame = self._header_actions = actions_frame

        def _icon_button(parent, glyph, cmd):
            btn = tk.Button(
                parent, text=glyph, bg=colors.bg_card, fg=colors.text_secondary,
                activebackground=colors.hover, relief="flat", bd=0,
                cursor="hand2", font=("Segoe UI Symbol", 13), command=cmd,
            )
            btn.pack(side="right", padx=spacing.sm)
            btn.bind("<Enter>", lambda e: btn.config(bg=colors.hover))
            btn.bind("<Leave>", lambda e: btn.config(bg=colors.bg_card))
            return btn

        _icon_button(actions_frame, "🔔", self.show_reports_view)
        self._appearance_btn = _icon_button(
            actions_frame, "🎨",
            lambda: self._open_appearance())

        # Right-click on the user chip: appearance, preferences, logout
        bind_context_menu_all(avatar_frame, self._user_menu_items)
        bind_context_menu(user_label, self._user_menu_items)

        return header

    def _user_menu_items(self):
        """Menu for the header user chip."""
        return [
            menu_header(self.username or "User"),
            ContextItem("Appearance…", self._open_appearance, glyph="🎨"),
            ContextItem("Preferences…", self.show_settings_view, glyph="⚙"),
            menu_separator(),
            ContextItem("Log out", self.logout, glyph="⏻", tone="danger"),
        ]

    def _open_appearance(self):
        from ui.theme.appearance import open_appearance_panel
        open_appearance_panel(self._appearance_btn)
    
    def _add_navigation(self):
        """Add navigation items to the sidebar."""
        # Home
        self.sidebar.add_button(
            "Home",
            self.show_home_view,
            Icon(path="Home.svg", size=(24, 24))
        )
        
        # Projects
        self.sidebar.add_button(
            "Projects",
            self.show_projects_view,
            Icon(path="square-dashed.svg", size=(24, 24))
        )

        # New project / cost / budget entry forms
        self.sidebar.add_button(
            "New Entry",
            self.show_project_form_view,
            Icon(path="check.svg", size=(24, 24))
        )

        # Expenses
        self.sidebar.add_button(
            "Expenses",
            self.show_expenses_view,
            Icon(path="clipboard-paste.svg", size=(24, 24))
        )
        
        # Reports
        self.sidebar.add_button(
            "Reports",
            self.show_reports_view,
            Icon(path="copy.svg", size=(24, 24))
        )
        
        self.sidebar.add_separator()
        
        # Settings
        self.sidebar.add_button(
            "Settings",
            self.show_settings_view,
            Icon(path="settings.svg", size=(24, 24))
        )
        
        self.sidebar.add_spacer()
        
        # Logout
        self.sidebar.add_button(
            "Logout",
            self.logout,
            Icon(path="user.svg", size=(24, 24))
        )
    
    def clear_content(self):
        """Clear the content frame."""
        for widget in self.content_frame.winfo_children():
            widget.destroy()
    
    def show_home_view(self):
        """Show the home/dashboard view."""
        self._current_view = "home"
        self.clear_content()
        self._show_dashboard_widgets()

    def show_projects_view(self):
        """Show the projects overview view."""
        self._current_view = "projects"
        self.clear_content()
        self._show_project_overview()

    def show_project_form_view(self):
        """Show a lightweight project setup form with cost and budget entry."""
        self._current_view = "form"
        self.clear_content()
        colors = self.colors
        spacing = theme.spacing

        wrapper = tk.Frame(self.content_frame, bg=colors.bg_main)
        wrapper.pack(fill="both", expand=True, padx=spacing.lg, pady=spacing.lg)

        title = tk.Label(wrapper, text="Project Setup", bg=colors.bg_main)
        apply_label_style(title, variant="heading")
        title.pack(anchor="w", pady=(0, spacing.md))

        form_stack = tk.Frame(wrapper, bg=colors.bg_main)
        form_stack.pack(fill="both", expand=True)

        ProjectEntryForm(form_stack, on_save=self.show_projects_view)
        CostItemEntryForm(form_stack, on_save=self.show_projects_view)
        BudgetEntryForm(form_stack, on_save=self.show_projects_view)
    
    def show_expenses_view(self):
        """Show the expenses view."""
        self._current_view = "expenses"
        self.clear_content()
        self._show_expenses_view()

    def show_reports_view(self):
        """Show the reports view."""
        self._current_view = "reports"
        self.clear_content()
        self._show_budget_view()

    def show_settings_view(self):
        """Show the settings view."""
        self._current_view = "settings"
        self.clear_content()
        if self.prefs_engine is not None:
            PreferencesPage(self.content_frame, self.prefs_engine)
        else:
            self._show_placeholder("Settings", "Preferences are unavailable.")
    
    def logout(self):
        """Handle logout."""
        # Import here to avoid circular dependency
        import main_windows as mw
        import sys
        from pathlib import Path
        
        mw.clear_root()
        mw.set_window_title("Login")
        
        # Dynamically import login_win
        src_path = Path(__file__).parent.parent
        if str(src_path) not in sys.path:
            sys.path.insert(0, str(src_path))
        
        import login_win
        login_win.create_login_frame(mw.get_root())
    
    def _show_placeholder(self, title: str, description: str):
        """Show a placeholder view for unimplemented sections."""
        colors = self.colors
        spacing = theme.spacing
        
        card = create_card_frame(self.content_frame)
        card.pack(fill="both", expand=True, padx=spacing.lg, pady=spacing.lg)
        
        title_label = tk.Label(card, text=title, bg=colors.bg_card)
        apply_label_style(title_label, variant="subtitle")
        title_label.pack(pady=spacing.lg)
        
        desc_label = tk.Label(card, text=description, bg=colors.bg_card)
        apply_label_style(desc_label, variant="muted")
        desc_label.pack(pady=spacing.xs)

    def _show_project_overview(self, selected_project=None):
        """Display saved projects and their current budget/spend state."""
        colors = self.colors
        spacing = theme.spacing
        summary = self._read_summary()

        card = create_card_frame(self.content_frame)
        card.pack(fill="both", expand=True, padx=spacing.lg, pady=spacing.lg)

        header = tk.Frame(card, bg=colors.bg_card)
        header.pack(fill="x", padx=spacing.lg, pady=(spacing.lg, spacing.md))

        title = tk.Label(header, text="Projects", bg=colors.bg_card)
        apply_label_style(title, variant="subtitle")
        title.pack(side="left")

        actions = tk.Frame(header, bg=colors.bg_card)
        actions.pack(side="right", padx=spacing.md, pady=spacing.sm)
        add_button = tk.Button(
            actions,
            text="New Project",
            command=self.show_project_form_view,
            bg=colors.primary,
            fg=colors.text_white,
            activebackground=colors.hover,
            relief="flat",
            padx=spacing.md,
            pady=spacing.sm,
            cursor="hand2",
            font=get_font(theme.fonts.body_small, bold=True),
        )
        add_button.pack()

        if not summary['projects']:
            empty = tk.Label(
                card,
                text="No projects saved yet. Create your first project from the project form.",
                bg=colors.bg_card,
                fg=colors.text_secondary,
                font=get_font(theme.fonts.body_normal),
            )
            empty.pack(anchor="w", padx=spacing.lg, pady=(0, spacing.lg))
            return

        left = tk.Frame(card, bg=colors.bg_card)
        left.pack(side="left", fill="y", padx=(spacing.lg, spacing.md), pady=(0, spacing.lg))
        left.pack_propagate(False)
        left.config(width=280)

        right = tk.Frame(card, bg=colors.bg_main)
        right.pack(side="right", fill="both", expand=True, padx=(0, spacing.lg), pady=(0, spacing.lg))

        self._render_project_list(left, right, summary['projects'])
        selected_name = selected_project.get("name") if selected_project else None
        selected = next(
            (item for item in summary["projects"] if item["name"] == selected_name),
            summary["projects"][0],
        )
        self._render_project_detail(right, selected)

    def _render_project_list(self, parent: tk.Frame, detail_parent: tk.Frame, projects):
        colors = self.colors
        spacing = theme.spacing

        for project in projects:
            btn = tk.Button(
                parent,
                text=f"{project.get('name', 'Project')}\n{self._money(project.get('budget', 0))}",
                command=lambda p=project, target=detail_parent: self._render_project_detail(target, p),
                bg=colors.bg_main,
                fg=colors.text_primary,
                activebackground=colors.primary,
                activeforeground=colors.text_white,
                anchor="w",
                justify="left",
                relief="flat",
                padx=spacing.md,
                pady=spacing.md,
                wraplength=220,
                height=3,
            )
            btn.pack(fill="x", pady=(0, spacing.sm))
            bind_context_menu(btn, lambda p=project: self._project_menu_items(p))

    def _project_menu_items(self, project):
        """Menu for project rows and the detail pane: open, enter, copy, delete."""
        name = project.get("name", "Project")
        items = [menu_header(name)]
        items.append(ContextItem(
            "Open project",
            lambda: self._show_project_overview_for(project)))
        items.append(menu_separator())
        items.append(ContextItem(
            "Add cost item",
            lambda: self._show_project_entry_for(project, "cost")))
        items.append(ContextItem(
            "Set category budget",
            lambda: self._show_project_entry_for(project, "budget")))
        items.append(menu_separator())
        items.append(ContextItem(
            "Copy project name", lambda: copy_text(self.parent, name)))
        description = str(project.get("description") or "")
        if description:
            items.append(ContextItem(
                "Copy description", lambda: copy_text(self.parent, description)))
        items.append(menu_separator())
        items.append(ContextItem(
            "Delete project…",
            lambda: self._confirm_delete_project(project),
            tone="danger"))
        return items

    def _confirm_delete_project(self, project):
        """Ask for confirmation, then delete the project database."""
        name = project.get("name", "")
        if not name:
            return
        if not messagebox.askyesno(
                "Delete project",
                f"Delete '{name}' with all of its cost items and budgets?\n\n"
                "This cannot be undone."):
            return
        if not self.model.delete_project(name):
            messagebox.showerror("Delete project", f"Could not delete '{name}'.")
            return
        self.show_projects_view()

    def _show_project_overview_for(self, project):
        self._current_view = "projects"
        self.clear_content()
        self._show_project_overview(selected_project=project)

    def _show_project_entry_for(self, project, entry_type: str):
        self._current_view = "form"
        self.clear_content()
        colors = self.colors
        spacing = theme.spacing

        wrapper = tk.Frame(self.content_frame, bg=colors.bg_main)
        wrapper.pack(fill="both", expand=True, padx=spacing.lg, pady=spacing.lg)
        header = tk.Frame(wrapper, bg=colors.bg_main)
        header.pack(fill="x", pady=(0, spacing.md))

        back = tk.Button(
            header,
            text="Projects",
            command=self.show_projects_view,
            relief="flat",
            bg=colors.bg_main,
            fg=colors.primary,
            cursor="hand2",
        )
        back.pack(side="left", padx=(0, spacing.md))
        title = tk.Label(header, text=project["name"], bg=colors.bg_main)
        apply_label_style(title, variant="heading")
        title.pack(side="left")

        form_parent = tk.Frame(wrapper, bg=colors.bg_main)
        form_parent.pack(fill="both", expand=True)
        on_save = lambda: self._show_project_overview_for(project)
        if entry_type == "cost":
            CostItemEntryForm(form_parent, on_save=on_save, selected_project=project["name"])
        else:
            BudgetEntryForm(form_parent, on_save=on_save, selected_project=project["name"])

    def _render_project_detail(self, parent: tk.Frame, project):
        colors = self.colors
        spacing = theme.spacing

        for child in parent.winfo_children():
            child.destroy()

        # Per-project data from the model (previous version showed global totals)
        self.model.ensure_project_tables(project["name"])
        summary = self.model.project_summary(project['name'])
        from ui.widgets import Bar

        project_name = tk.Label(parent, text=project.get('name', 'Project'), bg=colors.bg_main, font=get_font(theme.fonts.title_small, bold=True))
        project_name.pack(anchor="w", padx=spacing.md, pady=(spacing.md, spacing.sm))

        status = summary.get('status')
        if status is not None:
            status_label = tk.Label(parent, text=f"{status.label} — {int(round(status.fraction * 100))}% of budget used",
                                    bg=colors.bg_main,
                                    fg={"success": colors.success, "warning": colors.warning,
                                        "danger": colors.error}[status.tone],
                                    font=get_font(theme.fonts.body_small))
            status_label.pack(anchor="w", padx=spacing.md, pady=(0, spacing.sm))

        description = tk.Label(parent, text=project.get('description', 'No description'), bg=colors.bg_main, fg=colors.text_secondary, justify="left", wraplength=500)
        description.pack(anchor="w", padx=spacing.md, pady=(0, spacing.md))

        stat_frame = tk.Frame(parent, bg=colors.bg_main)
        stat_frame.pack(fill="x", padx=spacing.md, pady=(0, spacing.md))

        tk.Label(stat_frame, text=f"Budget: {self._money(summary.get('budget', 0))}", bg=colors.bg_main).pack(anchor="w", pady=2)
        tk.Label(stat_frame, text=f"Spent: {self._money(summary.get('spent', 0))}", bg=colors.bg_main).pack(anchor="w", pady=2)
        tk.Label(stat_frame, text=f"Remaining: {self._money(summary.get('remaining', 0))}", bg=colors.bg_main).pack(anchor="w", pady=2)

        Bar(stat_frame, fraction=status.fraction if status else 0,
            tone=status.tone if status else "primary").pack(fill="x", pady=(4, 2))

        actions = tk.Frame(parent, bg=colors.bg_main)
        actions.pack(fill="x", padx=spacing.md, pady=(0, spacing.md))
        tk.Button(
            actions,
            text="Add cost item",
            command=lambda p=project: self._show_project_entry_for(p, "cost"),
            bg=colors.primary,
            fg=colors.text_white,
            relief="flat",
            padx=spacing.md,
            pady=spacing.xs,
            cursor="hand2",
        ).pack(side="left", padx=(0, spacing.sm))
        tk.Button(
            actions,
            text="Set category budget",
            command=lambda p=project: self._show_project_entry_for(p, "budget"),
            bg=colors.secondary,
            fg=colors.text_white,
            relief="flat",
            padx=spacing.md,
            pady=spacing.xs,
            cursor="hand2",
        ).pack(side="left")

        # Right-click anywhere in the detail header: same menu as list rows
        detail_menu = lambda: self._project_menu_items(project)
        bind_context_menu(project_name, detail_menu)
        bind_context_menu(description, detail_menu)
        bind_context_menu_all(stat_frame, detail_menu)

        self._render_project_tables(parent, project["name"], summary)

    def _render_project_tables(self, parent: tk.Frame, project_name: str, summary: dict):
        colors = self.colors
        spacing = theme.spacing

        cost_heading = tk.Label(parent, text="Cost items", bg=colors.bg_main)
        apply_label_style(cost_heading, variant="heading")
        cost_heading.pack(anchor="w", padx=spacing.md, pady=(spacing.xs, spacing.xs))

        cost_columns = ("category", "item", "quantity", "unit_cost", "total")
        costs = ttk.Treeview(parent, columns=cost_columns, show="headings", height=6)
        for column, label, width in (
            ("category", "Category", 110),
            ("item", "Item", 190),
            ("quantity", "Qty", 70),
            ("unit_cost", "Unit cost", 95),
            ("total", "Total", 100),
        ):
            costs.heading(column, text=label)
            costs.column(column, width=width, anchor="w" if column in ("category", "item") else "e")
        for item in self.model.list_cost_items(project_name, limit=100):
            costs.insert("", "end", iid=str(item["id"]), values=(
                item["category"], item["item_name"], item["quantity"],
                self._money(item["unit_cost"]), self._money(item["total_cost"]),
            ))
        cost_table_frame = tk.Frame(parent, bg=colors.bg_main)
        cost_table_frame.pack(fill="x", padx=spacing.md, pady=(0, spacing.md))
        cost_scroll = ttk.Scrollbar(cost_table_frame, orient="vertical", command=costs.yview)
        costs.configure(yscrollcommand=cost_scroll.set)
        costs.pack(in_=cost_table_frame, side="left", fill="both", expand=True)
        cost_scroll.pack(side="right", fill="y")
        bind_treeview_context_menu(
            costs,
            lambda iid: self._cost_item_menu_items(project_name, costs, iid))

        budget_heading = tk.Label(parent, text="Category budgets", bg=colors.bg_main)
        apply_label_style(budget_heading, variant="heading")
        budget_heading.pack(anchor="w", padx=spacing.md, pady=(0, spacing.xs))

        budget_columns = ("category", "budget", "spent", "remaining", "status")
        budgets = ttk.Treeview(parent, columns=budget_columns, show="headings", height=5)
        for column, label, width in (
            ("category", "Category", 130),
            ("budget", "Budget", 100),
            ("spent", "Spent", 100),
            ("remaining", "Remaining", 100),
            ("status", "Status", 110),
        ):
            budgets.heading(column, text=label)
            budgets.column(column, width=width, anchor="w" if column in ("category", "status") else "e")
        for category in summary["categories"]:
            if category["budget"] <= 0 and category["items"] == 0:
                continue
            budgets.insert("", "end", iid=category["category"], values=(
                category["category"], self._money(category["budget"]),
                self._money(category["spent"]), self._money(category["remaining"]),
                category["status"].label,
            ))
        budget_table_frame = tk.Frame(parent, bg=colors.bg_main)
        budget_table_frame.pack(fill="x", padx=spacing.md, pady=(0, spacing.md))
        budget_scroll = ttk.Scrollbar(budget_table_frame, orient="vertical", command=budgets.yview)
        budgets.configure(yscrollcommand=budget_scroll.set)
        budgets.pack(in_=budget_table_frame, side="left", fill="both", expand=True)
        budget_scroll.pack(side="right", fill="y")
        bind_treeview_context_menu(
            budgets,
            lambda iid: self._budget_menu_items(project_name, budgets, iid))

    def _cost_item_menu_items(self, project_name: str, tree: ttk.Treeview, iid: str | None):
        """Row-sensitive menu for the cost items table."""
        if not iid:
            return [menu_header("Cost items"),
                    ContextItem("Refresh view", self._refresh_current_view)]
        values = tree.item(iid, "values")
        item_name = str(values[1]) if values else "cost item"
        return [
            menu_header(item_name),
            ContextItem(
                "Copy details",
                lambda: copy_text(tree, " | ".join(str(v) for v in values))),
            menu_separator(),
            ContextItem(
                "Delete cost item…",
                lambda: self._confirm_delete_cost_item(project_name, iid, item_name),
                tone="danger"),
        ]

    def _confirm_delete_cost_item(self, project_name: str, iid: str, item_name: str):
        """Ask for confirmation, then remove the cost item row."""
        if not messagebox.askyesno(
                "Delete cost item",
                f"Delete '{item_name}' from '{project_name}'?\n\n"
                "This cannot be undone."):
            return
        result = self.model.delete_cost_item(project_name, iid)
        if not result.get("status"):
            messagebox.showerror("Delete cost item",
                                 result.get("message", "Deletion failed."))
            return
        self._show_project_overview_for({"name": project_name})

    def _budget_menu_items(self, project_name: str, tree: ttk.Treeview, iid: str | None):
        """Row-sensitive menu for the category budgets table."""
        if not iid:
            return [menu_header("Category budgets"),
                    ContextItem("Refresh view", self._refresh_current_view)]
        values = tree.item(iid, "values")
        return [
            menu_header(str(values[0]) if values else iid),
            ContextItem(
                "Edit budget…",
                lambda: self._show_project_entry_for({"name": project_name}, "budget")),
            ContextItem(
                "Copy row",
                lambda: copy_text(tree, " | ".join(str(v) for v in values))),
            menu_separator(),
            ContextItem(
                "Remove budget…",
                lambda: self._confirm_remove_budget(project_name, iid),
                tone="danger"),
        ]

    def _confirm_remove_budget(self, project_name: str, category: str):
        """Ask for confirmation, then drop the category budget row."""
        if not messagebox.askyesno(
                "Remove budget",
                f"Remove the '{category}' budget for '{project_name}'?\n\n"
                "Logged spending is kept."):
            return
        result = self.model.remove_category_budget(project_name, category)
        if not result.get("status"):
            messagebox.showerror("Remove budget",
                                 result.get("message", "Removal failed."))
            return
        self._show_project_overview_for({"name": project_name})

    def _show_expenses_view(self):
        """Expense overview: totals plus the most recent cost items."""
        colors = self.colors
        spacing = theme.spacing

        card = create_card_frame(self.content_frame)
        card.pack(fill="both", expand=True, padx=spacing.lg, pady=spacing.lg)

        title = tk.Label(card, text="Expenses", bg=colors.bg_card)
        apply_label_style(title, variant="subtitle")
        title.pack(anchor="w", padx=spacing.lg, pady=(spacing.lg, spacing.md))

        summary = self._read_summary()
        if not summary['projects']:
            tk.Label(card, text="No expense records yet. Use New Entry to log a cost item.", bg=colors.bg_card, fg=colors.text_secondary).pack(anchor="w", padx=spacing.lg, pady=(0, spacing.lg))
            return

        amount_label = tk.Label(card, text=f"Total tracked cost: {self._money(summary['total_spent'])}", bg=colors.bg_card)
        apply_label_style(amount_label, variant="body")
        amount_label.pack(anchor="w", padx=spacing.lg, pady=(0, spacing.md))

        items = self._recent_items(limit=12)
        if items:
            list_title = tk.Label(card, text="Recent cost items", bg=colors.bg_card)
            apply_label_style(list_title, variant="heading")
            list_title.pack(anchor="w", padx=spacing.lg, pady=(0, spacing.sm))

            for item in items:
                row = tk.Frame(card, bg=colors.bg_card)
                row.pack(fill="x", padx=spacing.lg, pady=2)

                what = tk.Label(row, text=f"{item.get('category')}: {item.get('item_name', '')}", bg=colors.bg_card, anchor="w")
                apply_label_style(what, variant="body")
                what.pack(side="left")

                where = tk.Label(row, text=str(item.get("project_name") or ""), bg=colors.bg_card, fg=colors.text_secondary)
                apply_label_style(where, variant="caption")
                where.pack(side="right")

                when = tk.Label(row, text=str(item.get("created_at") or "")[:16], bg=colors.bg_card, fg=colors.text_secondary)
                apply_label_style(when, variant="caption")
                when.pack(side="right", padx=spacing.md)

                amount = tk.Label(row, text=self._money(item.get("total_cost", 0)), bg=colors.bg_card)
                apply_label_style(amount, variant="body")
                amount.pack(side="right", padx=spacing.md)

                bind_context_menu_all(
                    row,
                    lambda it=item, r=row: self._expense_menu_items(it, r, self.show_expenses_view))

    def _expense_text(self, item: dict) -> str:
        """One-line plain-text summary of an expense row (for the clipboard)."""
        text = (f"{item.get('category', '')}: {item.get('item_name', '')} — "
                f"{self._money(item.get('total_cost', 0))}")
        if item.get("project_name"):
            text += f" ({item['project_name']})"
        if item.get("created_at"):
            text += f" · {str(item['created_at'])[:16]}"
        return text

    def _expense_menu_items(self, item: dict, widget: tk.Widget, refresh: typing.Callable[[], None]):
        """Shared menu for expense rows in Expenses and Recent Activity."""
        items = [menu_header(f"{item.get('category', 'Cost')}: {item.get('item_name', '')}")]
        items.append(ContextItem(
            "Copy expense details",
            lambda: copy_text(widget, self._expense_text(item))))
        project_name = str(item.get("project_name") or "")
        if project_name:
            items.append(ContextItem(
                "Open project",
                lambda: self._show_project_overview_for({"name": project_name})))
        if project_name and item.get("id") is not None:
            items.append(menu_separator())
            items.append(ContextItem(
                "Delete expense…",
                lambda: self._confirm_delete_expense(item, refresh),
                tone="danger"))
        return items

    def _confirm_delete_expense(self, item: dict, refresh: typing.Callable[[], None]):
        """Ask for confirmation, then remove the logged expense."""
        project_name = str(item.get("project_name") or "")
        if not project_name or item.get("id") is None:
            return
        if not messagebox.askyesno(
                "Delete expense",
                f"Delete '{item.get('item_name', 'this item')}' from '{project_name}'?\n\n"
                "This cannot be undone."):
            return
        result = self.model.delete_cost_item(project_name, item["id"])
        if not result.get("status"):
            messagebox.showerror("Delete expense",
                                 result.get("message", "Deletion failed."))
            return
        refresh()

    def _show_budget_view(self):
        """Budget report: totals plus per-category breakdown per project."""
        colors = self.colors
        spacing = theme.spacing
        from ui.widgets import Bar

        card = create_card_frame(self.content_frame)
        card.pack(fill="both", expand=True, padx=spacing.lg, pady=spacing.lg)

        title = tk.Label(card, text="Budgets", bg=colors.bg_card)
        apply_label_style(title, variant="subtitle")
        title.pack(anchor="w", padx=spacing.lg, pady=(spacing.lg, spacing.md))

        summary = self._read_summary()
        tk.Label(card, text=f"Total budget: {self._money(summary['total_budget'])}", bg=colors.bg_card).pack(anchor="w", padx=spacing.lg, pady=(0, spacing.sm))
        tk.Label(card, text=f"Remaining: {self._money(summary['budget_remaining'])}", bg=colors.bg_card).pack(anchor="w", padx=spacing.lg, pady=(0, spacing.md))

        projects = self.model.list_all_projects()
        if not projects:
            tk.Label(card, text="No projects to report on yet.", bg=colors.bg_card, fg=colors.text_secondary).pack(anchor="w", padx=spacing.lg, pady=(0, spacing.lg))
            return

        for project in projects:
            proj_summary = self.model.project_summary(project["name"])
            status = proj_summary["status"]

            head = tk.Frame(card, bg=colors.bg_card)
            head.pack(fill="x", padx=spacing.lg, pady=(spacing.md, 2))
            name_label = tk.Label(head, text=project["name"], bg=colors.bg_card)
            apply_label_style(name_label, variant="heading")
            name_label.pack(side="left")

            total_label = tk.Label(
                head,
                text=f"{status.label} — {self._money(proj_summary['spent'])} of {self._money(proj_summary['budget'])}",
                bg=colors.bg_card, fg=colors.text_secondary)
            apply_label_style(total_label, variant="caption")
            total_label.pack(side="right")

            bind_context_menu_all(head, lambda pr=project, s=proj_summary, h=head: [
                menu_header(pr["name"]),
                ContextItem(
                    "Open project",
                    lambda: self._show_project_overview_for(pr)),
                ContextItem(
                    "Copy totals",
                    lambda: copy_text(
                        h, f"{pr['name']}: {s['status'].label} — "
                           f"{self._money(s['spent'])} of {self._money(s['budget'])}")),
            ])

            Bar(card, fraction=status.fraction, tone=status.tone).pack(
                fill="x", padx=spacing.lg, pady=(2, 4))

            for cat in proj_summary["categories"]:
                if cat["budget"] <= 0 and cat["items"] == 0:
                    continue
                row = tk.Frame(card, bg=colors.bg_card)
                row.pack(fill="x", padx=spacing.lg, pady=1)

                cname = tk.Label(row, text=cat["category"], bg=colors.bg_card,
                                 width=16, anchor="w")
                apply_label_style(cname, variant="caption")
                cname.pack(side="left")

                Bar(row, fraction=cat["status"].fraction,
                    tone=cat["status"].tone).pack(side="left", fill="x",
                                                  expand=True, padx=spacing.sm, pady=3)

                cval = tk.Label(
                    row,
                    text=f"{self._money(cat['spent'])} / {self._money(cat['budget'])}",
                    bg=colors.bg_card, fg=colors.text_secondary, width=22, anchor="e")
                apply_label_style(cval, variant="caption")
                cval.pack(side="right")

        tk.Frame(card, bg=colors.bg_card, height=spacing.md).pack()
    
    def _money(self, value):
        from .init_project import format_money
        try:
            return format_money(float(value))
        except (TypeError, ValueError):
            return format_money(0)

    def _read_summary(self):
        """Aggregate across all per-project databases via the model layer.

        (The previous implementation queried central tables that the forms
        never write to, so budgets/spend always showed zero.)
        """
        try:
            data = self.model.dashboard_totals()
            projects = [
                {
                    'id': p['name'],
                    'name': p['name'],
                    'description': p['description'],
                    'budget': p['budget'],
                    'spent': p['spent'],
                    'remaining': p['remaining'],
                    'status': p['status'],
                    'item_count': p['item_count'],
                }
                for p in data['projects']
            ]
            return {
                'project_count': data['project_count'],
                'total_spent': data['total_spent'],
                'total_budget': data['total_budget'],
                'budget_remaining': data['remaining'],
                'remaining': data['remaining'],
                'by_category': data['by_category'],
                'status': data['status'],
                'alerts': data['alerts'],
                'projects': projects,
            }
        except Exception as exc:
            print(f"dashboard summary failed: {exc}")
            return {
                'project_count': 0,
                'total_spent': 0.0,
                'total_budget': 0.0,
                'budget_remaining': 0.0,
                'remaining': 0.0,
                'by_category': {c: 0.0 for c in (
                    "Labor", "Materials", "Equipment", "Subcontractor",
                    "Miscellaneous")},
                'status': None,
                'alerts': [],
                'projects': [],
            }

    def _recent_items(self, limit: int = 10) -> list[dict]:
        """Most recent cost items across all projects."""
        items: list[dict] = []
        for project in self.model.list_all_projects():
            for row in self.model.list_cost_items(project["name"], limit=limit):
                row["project_name"] = project["name"]
                items.append(row)
        items.sort(key=lambda r: str(r.get("created_at") or ""), reverse=True)
        return items[:limit]

    def _show_dashboard_widgets(self):
        """Show dashboard widgets (cost cards, budget progress, etc.)."""
        colors = self.colors
        spacing = theme.spacing
        summary = self._read_summary()
        
        title_label = tk.Label(self.content_frame, text="Overview", bg=colors.bg_main)
        apply_label_style(title_label, variant="heading")
        title_label.pack(anchor="w", pady=(0, spacing.lg))
        
        stats_row = tk.Frame(self.content_frame, bg=colors.bg_main)
        stats_row.pack(fill="x", pady=spacing.md)
        
        self._create_stat_card(
            stats_row,
            "Total Spend",
            self._money(summary['total_spent']),
            colors.primary,
            f"{self._money(summary['budget_remaining'])} remaining"
        )
        
        self._create_stat_card(
            stats_row,
            "Budget Remaining",
            self._money(summary['budget_remaining']),
            colors.success,
            f"Budget total: {self._money(summary['total_budget'])}"
        )
        
        self._create_stat_card(
            stats_row,
            "Active Projects",
            str(summary['project_count']),
            colors.secondary,
            "Projects tracked"
        )
        
        self._create_stat_card(
            stats_row,
            "Budget Alerts",
            str(len(summary.get('alerts', []))),
            colors.warning if summary.get('alerts') else colors.success,
            "Projects near/over budget"
        )

        self._create_alerts_section(summary)
        self._create_category_section(summary)
        self._create_budget_progress_section(summary)
        self._create_recent_activity_section(summary)

    def _create_alerts_section(self, summary):
        """Budget alerts — projects at ≥80% of their budget."""
        colors = self.colors
        spacing = theme.spacing
        alerts = summary.get('alerts') or []
        if not alerts:
            return

        section_card = create_card_frame(self.content_frame)
        section_card.pack(fill="x", pady=spacing.md)

        header_frame = tk.Frame(section_card, bg=colors.bg_card)
        header_frame.pack(fill="x", padx=spacing.lg, pady=(spacing.lg, spacing.xs))

        title_label = tk.Label(header_frame, text="⚠ Budget Alerts",
                               bg=colors.bg_card, fg=colors.error)
        apply_label_style(title_label, variant="heading")
        title_label.pack(side="left")

        for project in alerts:
            status = project["status"]
            row = tk.Frame(section_card, bg=colors.bg_card)
            row.pack(fill="x", padx=spacing.lg, pady=spacing.xs)

            tone_color = {"warning": colors.warning, "danger": colors.error,
                          "success": colors.success}[status.tone]
            pct = int(round(status.fraction * 100))
            name_label = tk.Label(row, text=project["name"], bg=colors.bg_card)
            apply_label_style(name_label, variant="body")
            name_label.pack(side="left")

            info_label = tk.Label(
                row,
                text=f"{status.label} — {pct}% used "
                     f"({self._money(project['spent'])} of {self._money(project['budget'])})",
                bg=colors.bg_card, fg=tone_color)
            apply_label_style(info_label, variant="caption")
            info_label.pack(side="right")

            bind_context_menu_all(row, lambda pr=project, r=row: [
                menu_header(pr["name"]),
                ContextItem(
                    "Open project",
                    lambda: self._show_project_overview_for(pr)),
                ContextItem(
                    "Copy alert",
                    lambda: copy_text(
                        r, f"{pr['name']}: {pr['status'].label} — "
                           f"{self._money(pr['spent'])} of {self._money(pr['budget'])}")),
            ])

    def _create_category_section(self, summary):
        """Spend by category with mini progress bars."""
        colors = self.colors
        spacing = theme.spacing

        section_card = create_card_frame(self.content_frame)
        section_card.pack(fill="x", pady=spacing.md)

        header_frame = tk.Frame(section_card, bg=colors.bg_card)
        header_frame.pack(fill="x", padx=spacing.lg, pady=(spacing.lg, spacing.md))
        title_label = tk.Label(header_frame, text="Spend by Category",
                               bg=colors.bg_card)
        apply_label_style(title_label, variant="heading")
        title_label.pack(side="left")

        by_category = summary.get('by_category') or {}
        max_val = max(by_category.values(), default=0.0) or 1.0
        from ui.widgets import Bar
        for category, spent in by_category.items():
            row = tk.Frame(section_card, bg=colors.bg_card)
            row.pack(fill="x", padx=spacing.lg, pady=2)
            name_label = tk.Label(row, text=category, bg=colors.bg_card, width=16,
                                  anchor="w")
            apply_label_style(name_label, variant="body")
            name_label.pack(side="left")

            Bar(row, fraction=spent / max_val, tone="primary").pack(
                side="left", fill="x", expand=True, padx=spacing.sm, pady=4)

            amount_label = tk.Label(row, text=self._money(spent), bg=colors.bg_card,
                                    width=12, anchor="e")
            apply_label_style(amount_label, variant="caption")
            amount_label.pack(side="right")

        tk.Frame(section_card, bg=colors.bg_card, height=spacing.md).pack()
    
    def _create_stat_card(self, parent: tk.Frame, title: str, value: str, color: str, subtitle: str):
        """Create a statistics card."""
        colors = self.colors
        spacing = theme.spacing
        
        card = create_card_frame(parent)
        card.pack(side="left", fill="both", expand=True, padx=spacing.xs)
        
        # Color indicator
        indicator = tk.Frame(card, bg=color, width=4, height=40)
        indicator.pack(side="left", padx=(spacing.md, spacing.sm))
        indicator.pack_propagate(False)
        
        # Content
        content_frame = tk.Frame(card, bg=colors.bg_card)
        content_frame.pack(side="left", fill="both", expand=True, padx=spacing.sm, pady=spacing.md)
        
        title_label = tk.Label(content_frame, text=title, bg=colors.bg_card)
        apply_label_style(title_label, variant="caption")
        title_label.pack(anchor="w")
        
        value_label = tk.Label(content_frame, text=value, bg=colors.bg_card, fg=color)
        apply_label_style(value_label, variant="title")
        value_label.pack(anchor="w", pady=(spacing.xs, 0))
        
        subtitle_label = tk.Label(content_frame, text=subtitle, bg=colors.bg_card)
        apply_label_style(subtitle_label, variant="caption")
        subtitle_label.pack(anchor="w", pady=(spacing.xs, 0))

        # Right-click: copy the metric
        bind_context_menu_all(card, lambda: [
            menu_header(title),
            ContextItem("Copy value", lambda: copy_text(card, value)),
            ContextItem(
                "Copy details",
                lambda: copy_text(card, f"{title}: {value} ({subtitle})")),
        ])
    
    def _create_budget_progress_section(self, summary):
        """Create the budget progress section."""
        colors = self.colors
        spacing = theme.spacing
        
        section_card = create_card_frame(self.content_frame)
        section_card.pack(fill="x", pady=spacing.md)
        
        header_frame = tk.Frame(section_card, bg=colors.bg_card)
        header_frame.pack(fill="x", padx=spacing.lg, pady=(spacing.lg, spacing.md))
        
        title_label = tk.Label(header_frame, text="Budget Progress", bg=colors.bg_card)
        apply_label_style(title_label, variant="heading")
        title_label.pack(side="left")
        
        total_budget = summary['total_budget']
        total_spent = summary['total_spent']
        progress_total = total_budget if total_budget > 0 else max(total_spent, 1)
        percentage = min(100, int((total_spent / progress_total) * 100)) if progress_total else 0
        progress_items = [
            ("Tracked budget", total_spent, progress_total, colors.primary),
        ]
        
        for item_name, spent, total, color in progress_items:
            self._create_progress_bar(section_card, item_name, spent, total, color)

        if summary['projects']:
            summary_label = tk.Label(
                section_card,
                text=f"{percentage}% used across {summary['project_count']} project(s)",
                bg=colors.bg_card,
                fg=colors.text_secondary,
                font=get_font(theme.fonts.body_normal),
            )
            summary_label.pack(anchor="w", padx=spacing.lg, pady=(0, spacing.md))
    
    def _create_progress_bar(self, parent: tk.Frame, label: str, spent: int, total: int, color: str):
        """Create a progress bar widget."""
        colors = self.colors
        spacing = theme.spacing
        
        container = tk.Frame(parent, bg=colors.bg_card)
        container.pack(fill="x", padx=spacing.lg, pady=spacing.sm)
        
        # Label row
        label_row = tk.Frame(container, bg=colors.bg_card)
        label_row.pack(fill="x", pady=(0, spacing.xs))
        
        name_label = tk.Label(label_row, text=label, bg=colors.bg_card)
        apply_label_style(name_label, variant="body")
        name_label.pack(side="left")
        
        percentage = int((spent / total) * 100)
        amount_label = tk.Label(
            label_row,
            text=f"${spent:,} / ${total:,} ({percentage}%)",
            bg=colors.bg_card
        )
        apply_label_style(amount_label, variant="caption")
        amount_label.pack(side="right")
        
        # Progress bar container
        progress_container = tk.Frame(container, bg=colors.bg_card)
        progress_container.pack(fill="x", pady=(spacing.xs, 0))
        
        # Progress bar background
        progress_bg = tk.Canvas(
            progress_container,
            bg=colors.hover,
            height=8,
            highlightthickness=0
        )
        progress_bg.pack(fill="x")
        
        # Store reference for later update
        progress_bg.percentage = percentage
        progress_bg.color = color
        self.progress_bars = getattr(self, 'progress_bars', [])
        self.progress_bars.append(progress_bg)
        
        # Schedule progress bar update after widget is visible
        self.parent.after(100, lambda pb=progress_bg: self._update_progress_bar(pb))
    
    def _update_progress_bar(self, progress_bg: tk.Canvas):
        """Update progress bar width after widget is visible."""
        percentage = getattr(progress_bg, 'percentage', 0)
        color = getattr(progress_bg, 'color', theme.colors.primary)
        
        progress_bg.update_idletasks()
        width = progress_bg.winfo_width()
        if width > 1:
            bar_width = int(width * (percentage / 100))
            progress_bg.create_rectangle(
                0, 0, bar_width, 8,
                fill=color,
                outline=""
            )
    
    def _create_recent_activity_section(self, summary):
        """Create the recent activity section."""
        colors = self.colors
        spacing = theme.spacing
        
        section_card = create_card_frame(self.content_frame)
        section_card.pack(fill="both", expand=True, pady=spacing.md)
        
        header_frame = tk.Frame(section_card, bg=colors.bg_card)
        header_frame.pack(fill="x", padx=spacing.lg, pady=(spacing.lg, spacing.md))
        
        title_label = tk.Label(header_frame, text="Recent Activity", bg=colors.bg_card)
        apply_label_style(title_label, variant="heading")
        title_label.pack(side="left")
        
        if not summary['projects']:
            empty_label = tk.Label(
                section_card,
                text="No project activity yet. Create your first project to begin tracking costs.",
                bg=colors.bg_card,
                fg=colors.text_secondary,
                font=get_font(theme.fonts.body_normal),
            )
            empty_label.pack(anchor="w", padx=spacing.lg, pady=(0, spacing.lg))
            return

        items = self._recent_items(limit=6)
        if not items:
            empty_label = tk.Label(
                section_card,
                text="No cost items logged yet. Open New Entry to record one.",
                bg=colors.bg_card,
                fg=colors.text_secondary,
                font=get_font(theme.fonts.body_normal),
            )
            empty_label.pack(anchor="w", padx=spacing.lg, pady=(0, spacing.lg))
            return

        for item in items:
            category = item.get("category", "Cost")
            name = item.get("item_name", "")
            project = item.get("project_name", "")
            self._create_activity_item(
                section_card,
                f"{category}: {name}",
                self._money(item.get("total_cost", 0)),
                f"{project} · {str(item.get('created_at') or '')[:16]}",
                colors.primary,
                item=item,
            )

    def _create_activity_item(self, parent: tk.Frame, activity: str, amount: str,
                              time: str, color: str, item: dict | None = None):
        """Create an activity list item."""
        colors = self.colors
        spacing = theme.spacing

        item_frame = tk.Frame(parent, bg=colors.bg_card)
        item_frame.pack(fill="x", padx=spacing.lg, pady=spacing.sm)

        # Activity description
        activity_label = tk.Label(item_frame, text=activity, bg=colors.bg_card)
        apply_label_style(activity_label, variant="body")
        activity_label.pack(side="left")

        # Amount
        amount_label = tk.Label(item_frame, text=amount, bg=colors.bg_card, fg=color)
        apply_label_style(amount_label, variant="body")
        amount_label.pack(side="right", padx=spacing.md)

        # Time
        time_label = tk.Label(item_frame, text=time, bg=colors.bg_card)
        apply_label_style(time_label, variant="caption")
        time_label.pack(side="right")

        # Right-click: copy / open project / delete (same menu as Expenses)
        if item is not None:
            bind_context_menu_all(
                item_frame,
                lambda it=item, f=item_frame: self._expense_menu_items(
                    it, f, self.show_home_view))
