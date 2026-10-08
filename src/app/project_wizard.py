# project_wizard.py
"""Multi-step project creation wizard with 5 guided steps.

Step 1: Basic Info (name, description, start date)
Step 2: Budget Setup (total budget, currency)
Step 3: Categories (select/edit expense categories)
Step 4: Team Members (add collaborators)
Step 5: Review & Confirm (summary of all settings)
"""
import tkinter as tk
from tkinter import ttk
from datetime import date
from typing import Callable, Dict, Any, Tuple

from .wizard import Wizard, WizardStep
from .theme import theme, get_font, apply_label_style, create_card_frame
from .widget_styles import apply_ctk_entry_style, apply_ctk_button_style, apply_ctk_card_style
from .init_project import CATEGORIES


class ProjectCreationWizard:
    """5-step wizard for creating new projects."""
    
    def __init__(self, parent: tk.Widget, on_complete: Callable = None, 
                 on_cancel: Callable = None, created_by: str = "User"):
        self.parent = parent
        self.created_by = created_by
        
        # Create wizard
        self.wizard = Wizard(
            parent,
            title="Create New Project",
            on_complete=self._on_wizard_complete,
            on_cancel=on_cancel
        )
        
        # Build steps
        self._build_step1_basic_info()
        self._build_step2_budget_setup()
        self._build_step3_categories()
        self._build_step4_team_members()
        self._build_step5_review()
        
        # Start wizard
        self.wizard.start()
    
    def _build_step1_basic_info(self) -> None:
        """Step 1: Basic project information."""
        colors = theme.colors
        spacing = theme.spacing
        
        # Create content frame
        content = tk.Frame(self.wizard.content_frame, bg=colors.bg_card)
        
        # Title
        title = tk.Label(content, text="Basic Information", bg=colors.bg_card)
        apply_label_style(title, variant="subtitle")
        title.pack(anchor="w", pady=(0, spacing.md))
        
        # Description
        desc = tk.Label(
            content,
            text="Enter the basic details for your project.",
            bg=colors.bg_card
        )
        apply_label_style(desc, variant="muted")
        desc.pack(anchor="w", pady=(0, spacing.lg))
        
        # Form fields
        form = tk.Frame(content, bg=colors.bg_card)
        form.pack(fill="both", expand=True)
        
        # Project name
        tk.Label(form, text="Project Name *", bg=colors.bg_card).pack(anchor="w", pady=(0, spacing.xs))
        name_var = tk.StringVar()
        name_entry = tk.Entry(form, textvariable=name_var, width=40)
        apply_ctk_entry_style(name_entry, corner_radius="sm")
        name_entry.pack(fill="x", pady=(0, spacing.md))
        
        # Description
        tk.Label(form, text="Description *", bg=colors.bg_card).pack(anchor="w", pady=(0, spacing.xs))
        desc_var = tk.StringVar()
        desc_entry = tk.Entry(form, textvariable=desc_var, width=40)
        apply_ctk_entry_style(desc_entry, corner_radius="sm")
        desc_entry.pack(fill="x", pady=(0, spacing.md))
        
        # Start date
        tk.Label(form, text="Start Date", bg=colors.bg_card).pack(anchor="w", pady=(0, spacing.xs))
        date_var = tk.StringVar(value=str(date.today()))
        date_entry = tk.Entry(form, textvariable=date_var, width=40)
        apply_ctk_entry_style(date_entry, corner_radius="sm")
        date_entry.pack(fill="x", pady=(0, spacing.md))
        
        # Store variables in wizard data
        self.wizard.set_step_data({
            "name_var": name_var,
            "description_var": desc_var,
            "date_var": date_var
        })
        
        # Validator
        def validate_step1(data: Dict[str, Any]) -> Tuple[bool, str]:
            name = data.get("name_var", tk.StringVar()).get().strip()
            description = data.get("description_var", tk.StringVar()).get().strip()
            date_str = data.get("date_var", tk.StringVar()).get().strip()
            
            if not name:
                return False, "Project name is required"
            if len(name) < 3:
                return False, "Project name must be at least 3 characters"
            if not description:
                return False, "Description is required"
            if len(description) < 10:
                return False, "Description must be at least 10 characters"
            
            try:
                date.fromisoformat(date_str)
            except ValueError:
                return False, "Date must be in YYYY-MM-DD format"
            
            return True, ""
        
        # Add step to wizard
        step = WizardStep(
            title="Basic Info",
            description="Enter project details"
        )
        self.wizard.add_step(step, content, validate_step1)
    
    def _build_step2_budget_setup(self) -> None:
        """Step 2: Budget configuration."""
        colors = theme.colors
        spacing = theme.spacing
        
        content = tk.Frame(self.wizard.content_frame, bg=colors.bg_card)
        
        title = tk.Label(content, text="Budget Setup", bg=colors.bg_card)
        apply_label_style(title, variant="subtitle")
        title.pack(anchor="w", pady=(0, spacing.md))
        
        desc = tk.Label(
            content,
            text="Set your project budget and currency.",
            bg=colors.bg_card
        )
        apply_label_style(desc, variant="muted")
        desc.pack(anchor="w", pady=(0, spacing.lg))
        
        form = tk.Frame(content, bg=colors.bg_card)
        form.pack(fill="both", expand=True)
        
        # Total budget
        tk.Label(form, text="Total Budget", bg=colors.bg_card).pack(anchor="w", pady=(0, spacing.xs))
        budget_var = tk.StringVar(value="0")
        budget_entry = tk.Entry(form, textvariable=budget_var, width=40)
        apply_ctk_entry_style(budget_entry, corner_radius="sm")
        budget_entry.pack(fill="x", pady=(0, spacing.md))
        
        # Currency
        tk.Label(form, text="Currency", bg=colors.bg_card).pack(anchor="w", pady=(0, spacing.xs))
        currency_var = tk.StringVar(value="USD")
        currency_combo = ttk.Combobox(
            form,
            textvariable=currency_var,
            state="readonly",
            values=["USD", "EUR", "GBP", "CAD", "AUD", "JPY", "INR"]
        )
        currency_combo.pack(fill="x", pady=(0, spacing.md))
        
        self.wizard.set_step_data({
            "budget_var": budget_var,
            "currency_var": currency_var
        })
        
        def validate_step2(data: Dict[str, Any]) -> Tuple[bool, str]:
            budget_str = data.get("budget_var", tk.StringVar()).get().strip()
            
            try:
                budget = float(budget_str)
                if budget < 0:
                    return False, "Budget cannot be negative"
            except ValueError:
                return False, "Budget must be a valid number"
            
            return True, ""
        
        step = WizardStep(
            title="Budget Setup",
            description="Configure project budget",
            can_skip=True
        )
        self.wizard.add_step(step, content, validate_step2)
    
    def _build_step3_categories(self) -> None:
        """Step 3: Category selection and configuration."""
        colors = theme.colors
        spacing = theme.spacing
        
        content = tk.Frame(self.wizard.content_frame, bg=colors.bg_card)
        
        title = tk.Label(content, text="Expense Categories", bg=colors.bg_card)
        apply_label_style(title, variant="subtitle")
        title.pack(anchor="w", pady=(0, spacing.md))
        
        desc = tk.Label(
            content,
            text="Select the expense categories you want to track.",
            bg=colors.bg_card
        )
        apply_label_style(desc, variant="muted")
        desc.pack(anchor="w", pady=(0, spacing.lg))
        
        # Category checkboxes
        categories_frame = tk.Frame(content, bg=colors.bg_card)
        categories_frame.pack(fill="both", expand=True)
        
        category_vars = {}
        for category in CATEGORIES:
            var = tk.BooleanVar(value=True)
            category_vars[category] = var
            
            row = tk.Frame(categories_frame, bg=colors.bg_card)
            row.pack(fill="x", pady=spacing.xs)
            
            cb = tk.Checkbutton(
                row,
                text=category,
                variable=var,
                bg=colors.bg_card,
                fg=colors.text_primary,
                activebackground=colors.bg_card,
                activeforeground=colors.text_primary,
                selectcolor=colors.bg_card,
                font=get_font(theme.fonts.body_normal)
            )
            cb.pack(side="left")
        
        self.wizard.set_step_data({"category_vars": category_vars})
        
        def validate_step3(data: Dict[str, Any]) -> Tuple[bool, str]:
            category_vars = data.get("category_vars", {})
            selected = [cat for cat, var in category_vars.items() if var.get()]
            
            if not selected:
                return False, "At least one category must be selected"
            
            return True, ""
        
        step = WizardStep(
            title="Categories",
            description="Select expense categories"
        )
        self.wizard.add_step(step, content, validate_step3)
    
    def _build_step4_team_members(self) -> None:
        """Step 4: Team member management."""
        colors = theme.colors
        spacing = theme.spacing
        
        content = tk.Frame(self.wizard.content_frame, bg=colors.bg_card)
        
        title = tk.Label(content, text="Team Members", bg=colors.bg_card)
        apply_label_style(title, variant="subtitle")
        title.pack(anchor="w", pady=(0, spacing.md))
        
        desc = tk.Label(
            content,
            text="Add team members to collaborate on this project (optional).",
            bg=colors.bg_card
        )
        apply_label_style(desc, variant="muted")
        desc.pack(anchor="w", pady=(0, spacing.lg))
        
        form = tk.Frame(content, bg=colors.bg_card)
        form.pack(fill="both", expand=True)
        
        # Team member list
        team_list_frame = tk.Frame(form, bg=colors.bg_card)
        team_list_frame.pack(fill="both", expand=True, pady=(0, spacing.md))
        
        # Add member field
        add_frame = tk.Frame(form, bg=colors.bg_card)
        add_frame.pack(fill="x")
        
        tk.Label(add_frame, text="Add Member (username):", bg=colors.bg_card).pack(side="left")
        member_var = tk.StringVar()
        member_entry = tk.Entry(add_frame, textvariable=member_var, width=20)
        apply_ctk_entry_style(member_entry, corner_radius="sm")
        member_entry.pack(side="left", padx=spacing.xs)
        
        team_members = []
        
        def add_member():
            username = member_var.get().strip()
            if username and username not in team_members:
                team_members.append(username)
                member_var.set("")
                _update_team_list()
        
        add_btn = tk.Button(add_frame, text="Add", command=add_member)
        apply_ctk_button_style(add_btn, variant="secondary", size="small")
        add_btn.pack(side="left", padx=spacing.xs)
        
        def _update_team_list():
            for widget in team_list_frame.winfo_children():
                widget.destroy()
            
            for member in team_members:
                row = tk.Frame(team_list_frame, bg=colors.bg_card)
                row.pack(fill="x", pady=spacing.xs)
                
                tk.Label(row, text=f"• {member}", bg=colors.bg_card).pack(side="left")
                
                remove_btn = tk.Button(
                    row,
                    text="×",
                    command=lambda m=member: _remove_member(m),
                    bg=colors.error,
                    fg=colors.text_white,
                    relief="flat",
                    bd=0,
                    padx=spacing.xs
                )
                remove_btn.pack(side="right")
        
        def _remove_member(member: str):
            if member in team_members:
                team_members.remove(member)
                _update_team_list()
        
        self.wizard.set_step_data({
            "member_var": member_var,
            "team_members": team_members
        })
        
        def validate_step4(data: Dict[str, Any]) -> Tuple[bool, str]:
            # Team members are optional
            return True, ""
        
        step = WizardStep(
            title="Team Members",
            description="Add collaborators (optional)",
            is_optional=True
        )
        self.wizard.add_step(step, content, validate_step4)
    
    def _build_step5_review(self) -> None:
        """Step 5: Review and confirm all settings."""
        colors = theme.colors
        spacing = theme.spacing
        
        content = tk.Frame(self.wizard.content_frame, bg=colors.bg_card)
        
        title = tk.Label(content, text="Review & Confirm", bg=colors.bg_card)
        apply_label_style(title, variant="subtitle")
        title.pack(anchor="w", pady=(0, spacing.md))
        
        desc = tk.Label(
            content,
            text="Review your project settings before creating.",
            bg=colors.bg_card
        )
        apply_label_style(desc, variant="muted")
        desc.pack(anchor="w", pady=(0, spacing.lg))
        
        # Summary display
        summary_frame = create_card_frame(content)
        summary_frame.pack(fill="both", expand=True, padx=spacing.md, pady=spacing.md)
        apply_ctk_card_style(summary_frame, shadow="sm", corner_radius="md")
        
        summary_label = tk.Label(
            summary_frame,
            text="",
            bg=colors.bg_card,
            justify="left",
            font=get_font(theme.fonts.body_normal)
        )
        summary_label.pack(fill="both", expand=True, padx=spacing.md, pady=spacing.md)
        
        self.summary_label = summary_label
        
        # Update summary when shown
        def update_summary():
            self._update_summary_display()
        
        # Override show_step to update summary
        original_show = self.wizard.show_step
        def custom_show_step(step_index: int):
            original_show(step_index)
            if step_index == 4:  # Review step
                update_summary()
        
        self.wizard.show_step = custom_show_step
        
        def validate_step5(data: Dict[str, Any]) -> Tuple[bool, str]:
            return True, ""
        
        step = WizardStep(
            title="Review",
            description="Confirm project settings"
        )
        self.wizard.add_step(step, content, validate_step5)
    
    def _update_summary_display(self) -> None:
        """Update the summary display with all wizard data."""
        colors = theme.colors
        spacing = theme.spacing
        
        # Get data from all steps
        step1_data = self.wizard.get_step_data(0)
        step2_data = self.wizard.get_step_data(1)
        step3_data = self.wizard.get_step_data(2)
        step4_data = self.wizard.get_step_data(3)
        
        # Extract values
        name = step1_data.get("name_var", tk.StringVar()).get()
        description = step1_data.get("description_var", tk.StringVar()).get()
        start_date = step1_data.get("date_var", tk.StringVar()).get()
        budget = step2_data.get("budget_var", tk.StringVar()).get()
        currency = step2_data.get("currency_var", tk.StringVar()).get()
        category_vars = step3_data.get("category_vars", {})
        team_members = step4_data.get("team_members", [])
        
        # Build summary text
        summary = f"""Project Name: {name}
Description: {description}
Start Date: {start_date}
Budget: {currency} {budget}

Categories:
"""
        
        selected_categories = [cat for cat, var in category_vars.items() if var.get()]
        for cat in selected_categories:
            summary += f"  • {cat}\n"
        
        if team_members:
            summary += f"\nTeam Members:\n"
            for member in team_members:
                summary += f"  • {member}\n"
        
        self.summary_label.config(text=summary)
    
    def _on_wizard_complete(self, all_data: Dict[int, Dict[str, Any]]) -> None:
        """Handle wizard completion - create the project."""
        # Extract final data
        step1_data = all_data[0]
        step2_data = all_data[1]
        step3_data = all_data[2]
        step4_data = all_data[3]
        
        name = step1_data["name_var"].get()
        description = step1_data["description_var"].get()
        start_date = step1_data["date_var"].get()
        budget = float(step2_data["budget_var"].get())
        currency = step2_data["currency_var"].get()
        category_vars = step3_data["category_vars"]
        team_members = step4_data["team_members"]
        
        selected_categories = [cat for cat, var in category_vars.items() if var.get()]
        
        # Create project using database operations
        try:
            from db import project_operations
            from db import operations_helper
            
            # Initialize database if needed
            operations_helper.initialize_database_if_needed()
            
            # Create project
            result = project_operations.create_project(
                name=name,
                description=description,
                start_date=start_date,
                budget=budget,
                created_by=self.created_by
            )
            
            if result["status"]:
                # Success - could add categories and team members here
                print(f"Project created successfully with ID: {result['id']}")
                print(f"Selected categories: {selected_categories}")
                print(f"Team members: {team_members}")
                
                # Show success message
                self._show_success_message()
            else:
                self._show_error_message(result["message"])
        
        except Exception as e:
            self._show_error_message(f"Failed to create project: {str(e)}")
    
    def _show_success_message(self) -> None:
        """Show success message after project creation."""
        colors = theme.colors
        spacing = theme.spacing
        
        # Clear wizard
        self.wizard.container.destroy()
        
        # Show success card
        success_card = create_card_frame(self.parent)
        success_card.pack(fill="both", expand=True, padx=spacing.xl, pady=spacing.xl)
        apply_ctk_card_style(success_card, shadow="lg", corner_radius="lg")
        
        tk.Label(
            success_card,
            text="✓",
            bg=colors.bg_card,
            fg=colors.success,
            font=("Segoe UI", 48)
        ).pack(pady=spacing.xl)
        
        tk.Label(
            success_card,
            text="Project Created Successfully!",
            bg=colors.bg_card
        ).apply_label_style(variant="title")
        tk.Label(success_card, text="Project Created Successfully!", bg=colors.bg_card)
        apply_label_style(tk.Label(success_card, text="Project Created Successfully!", bg=colors.bg_card), variant="title")
        tk.Label(success_card, text="Project Created Successfully!", bg=colors.bg_card).pack(pady=spacing.md)
        
        tk.Button(
            success_card,
            text="Back to Dashboard",
            command=self._close_success
        ).apply_ctk_button_style(variant="primary", size="medium")
        tk.Button(success_card, text="Back to Dashboard", command=self._close_success)
        apply_ctk_button_style(tk.Button(success_card, text="Back to Dashboard", command=self._close_success), variant="primary", size="medium")
        tk.Button(success_card, text="Back to Dashboard", command=self._close_success).pack(pady=spacing.lg)
    
    def _show_error_message(self, message: str) -> None:
        """Show error message."""
        colors = theme.colors
        spacing = theme.spacing
        
        tk.Label(
            self.wizard.content_frame,
            text=f"Error: {message}",
            bg=colors.bg_card,
            fg=colors.error
        ).pack(pady=spacing.md)
    
    def _close_success(self) -> None:
        """Close success view and return to dashboard."""
        from .dashboard import Dashboard
        self.parent.destroy()
        # Dashboard should handle showing projects view
    
    def show(self) -> None:
        """Show the wizard."""
        self.wizard.container.pack(fill="both", expand=True)
