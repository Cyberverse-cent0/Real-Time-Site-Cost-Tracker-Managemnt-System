# create_account.py
import tkinter as tk
from tkinter import messagebox
import pathlib

try:
    import user_setup
except ModuleNotFoundError:  # pragma: no cover - compatibility when run as a package
    from db import user_setup

import main_windows as mw
from app.theme import theme, get_font, apply_button_style, apply_entry_style, apply_label_style, create_card_frame
from ui.context_menu import attach_entry_menu


def _sync_auth_columns(main_container: tk.Frame, left_container: tk.Frame, right_container: tk.Frame) -> None:
    """Keep the form column near 25% of the window width and the promo column at 75%."""
    total_width = max(1, main_container.winfo_width())
    left_width = max(260, int(total_width * 0.25))
    left_container.config(width=left_width)
    right_container.config(width=max(1, total_width - left_width))


def create_create_account_frame(parent) -> tk.Frame:
    """Build the create-account form and return its frame."""
    mw.set_window_title("Create Account")
    
    colors = theme.colors
    spacing = theme.spacing
    
    # Set window background
    parent.config(bg=colors.bg_main)
    
    # Main container split into left (25%) and right (75%)
    main_container = tk.Frame(parent, bg=colors.bg_main)
    main_container.pack(expand=True, fill="both")
    main_container.pack_propagate(False)
    
    # Left side - Create account form (25%)
    left_container = tk.Frame(main_container, bg=colors.bg_main)
    left_container.pack(side="left", fill="y")
    left_container.pack_propagate(False)
    
    # Right side - Advertising/Marketing content (75%)
    right_container = tk.Frame(main_container, bg=colors.secondary)
    right_container.pack(side="right", fill="both", expand=True)
    right_container.pack_propagate(False)
    main_container.bind("<Configure>", lambda event: _sync_auth_columns(main_container, left_container, right_container))
    _sync_auth_columns(main_container, left_container, right_container)
    
    # Account creation card (smaller, centered on left)
    card = create_card_frame(left_container)
    card.pack(expand=True, fill="both", padx=spacing.xl, pady=spacing.xl)
    
    # Logo
    logo_frame = tk.Frame(card, bg=colors.bg_card)
    logo_frame.pack(pady=(spacing.lg, spacing.md))
    
    try:
        logo_path = pathlib.Path("public/app_logo.svg")
        if logo_path.exists():
            logo = tk.PhotoImage(file=str(logo_path)).subsample(2, 2)
            logo_label = tk.Label(logo_frame, image=logo, bg=colors.bg_card)
            logo_label.image = logo  # Keep reference
            logo_label.pack()
    except Exception:
        pass  # Fallback if logo fails to load
    
    # Title
    title_label = tk.Label(card, text="Create Account", bg=colors.bg_card)
    apply_label_style(title_label, variant="title")
    title_label.pack(pady=(0, spacing.xs))
    
    subtitle_label = tk.Label(card, text="Join Site Cost Tracker", bg=colors.bg_card)
    apply_label_style(subtitle_label, variant="muted")
    subtitle_label.pack(pady=(0, spacing.lg))
    
    # Form container
    form_container = tk.Frame(card, bg=colors.bg_card)
    form_container.pack(padx=spacing.xl, pady=spacing.md)
    
    username_var = tk.StringVar()
    password_var = tk.StringVar()
    confirm_password_var = tk.StringVar()
    email_var = tk.StringVar()
    
    # Username field
    username_label = tk.Label(form_container, text="Username", bg=colors.bg_card)
    apply_label_style(username_label, variant="body")
    username_label.pack(anchor="w", pady=(spacing.sm, spacing.xs))
    
    username_entry = tk.Entry(form_container, textvariable=username_var, width=25)
    apply_entry_style(username_entry)
    username_entry.pack(fill="x", pady=(0, spacing.md))
    attach_entry_menu(username_entry)

    # Email field
    email_label = tk.Label(form_container, text="Email", bg=colors.bg_card)
    apply_label_style(email_label, variant="body")
    email_label.pack(anchor="w", pady=(spacing.sm, spacing.xs))

    email_entry = tk.Entry(form_container, textvariable=email_var, width=25)
    apply_entry_style(email_entry)
    email_entry.pack(fill="x", pady=(0, spacing.md))
    attach_entry_menu(email_entry)

    # Password field
    password_label = tk.Label(form_container, text="Password", bg=colors.bg_card)
    apply_label_style(password_label, variant="body")
    password_label.pack(anchor="w", pady=(spacing.sm, spacing.xs))

    password_entry = tk.Entry(form_container, textvariable=password_var, width=25, show="•")
    apply_entry_style(password_entry)
    password_entry.pack(fill="x", pady=(0, spacing.md))
    attach_entry_menu(password_entry, sensitive=True)

    # Confirm password field
    confirm_password_label = tk.Label(form_container, text="Confirm Password", bg=colors.bg_card)
    apply_label_style(confirm_password_label, variant="body")
    confirm_password_label.pack(anchor="w", pady=(spacing.sm, spacing.xs))

    confirm_password_entry = tk.Entry(form_container, textvariable=confirm_password_var, width=25, show="•")
    apply_entry_style(confirm_password_entry)
    confirm_password_entry.pack(fill="x", pady=(0, spacing.sm))
    attach_entry_menu(confirm_password_entry, sensitive=True)
    
    # Show password checkbox
    show_pw = tk.BooleanVar()
    checkbox_frame = tk.Frame(form_container, bg=colors.bg_card)
    checkbox_frame.pack(anchor="w", pady=(spacing.xs, spacing.md))
    
    def toggle_password_visibility():
        show = show_pw.get()
        password_entry.config(show="" if show else "•")
        confirm_password_entry.config(show="" if show else "•")
    
    checkbutton = tk.Checkbutton(
        checkbox_frame,
        text="Show password",
        variable=show_pw,
        bg=colors.bg_card,
        fg=colors.text_secondary,
        activebackground=colors.bg_card,
        activeforeground=colors.text_primary,
        selectcolor=colors.bg_card,
        command=toggle_password_visibility,
        font=get_font(theme.fonts.body_small)
    )
    checkbutton.pack()
    
    # Status label
    status_label = tk.Label(form_container, text="", bg=colors.bg_card)
    apply_label_style(status_label, variant="caption")
    status_label.pack(pady=(spacing.xs, spacing.md))

    def on_submit():
        username = username_var.get().strip()
        password = password_var.get()
        confirm_password = confirm_password_var.get()
        email = email_var.get().strip()

        if not username or not password or not email or not confirm_password:
            status_label.config(text="All fields are required.", fg=colors.error)
            return

        if len(username) < 3:
            status_label.config(text="Username must be at least 3 characters.", fg=colors.error)
            return

        if len(username) > 50:
            status_label.config(text="Username must be less than 50 characters.", fg=colors.error)
            return

        if "@" not in email or "." not in email:
            status_label.config(text="Please enter a valid email address.", fg=colors.error)
            return

        if len(password) < 6:
            status_label.config(text="Password must be at least 6 characters.", fg=colors.error)
            return

        if password != confirm_password:
            status_label.config(text="Passwords do not match.", fg=colors.error)
            return

        try:
            from db import app_db
            if not app_db.database_exists():
                app_db.initialize_database()
        except PermissionError as e:
            status_label.config(text=f"Permission denied: Cannot create database. Check file permissions.", fg=colors.error)
            return
        except Exception as e:
            status_label.config(text=f"Database setup failed: {str(e)}", fg=colors.error)
            return

        try:
            if user_setup.user_exists(username):
                status_label.config(text="Username already taken.", fg=colors.error)
                return

            if user_setup.email_exists(email):
                status_label.config(text="Email already registered.", fg=colors.error)
                return

            result = user_setup.create_user(username, password, email)
            if result["status"]:
                messagebox.showinfo("Success", "Account created! You can now log in.")
                go_back_to_login()
                return

            error_msg = str(result.get("message", "Unknown error"))
            if "UNIQUE" in error_msg.upper() or "duplicate" in error_msg.lower():
                status_label.config(text="Username or email already exists.", fg=colors.error)
            else:
                status_label.config(text=f"Unable to create account: {error_msg}", fg=colors.error)
        except Exception as exc:
            status_label.config(text=f"Account creation failed: {exc}", fg=colors.error)

    def go_back_to_login():
        mw.clear_root()
        import login_win
        login_win.create_login_frame(mw.get_root())

    # Button row
    btn_row = tk.Frame(card, bg=colors.bg_card)
    btn_row.pack(pady=(spacing.lg, spacing.md))
    
    create_btn = tk.Button(btn_row, text="Create Account", command=on_submit)
    apply_button_style(create_btn, variant="primary", size="large")
    create_btn.pack(side="left", padx=spacing.xs)
    
    back_btn = tk.Button(btn_row, text="Back to Login", command=go_back_to_login)
    apply_button_style(back_btn, variant="outline", size="large")
    back_btn.pack(side="left", padx=spacing.xs)
    
    _create_advertising_content(right_container)

    return main_container


def _create_advertising_content(parent: tk.Frame):
    """Create advertising/features content on the right side."""
    colors = theme.colors
    spacing = theme.spacing
    
    # Content container
    content = tk.Frame(parent, bg=colors.secondary)
    content.pack(expand=True, fill="both", padx=spacing.xxl, pady=spacing.xxl)
    
    # Large logo
    try:
        logo_path = pathlib.Path("public/logo.svg")
        if logo_path.exists():
            logo = tk.PhotoImage(file=str(logo_path)).subsample(2, 2)
            logo_label = tk.Label(content, image=logo, bg=colors.secondary)
            logo_label.image = logo
            logo_label.pack(pady=(spacing.xxl, spacing.lg))
    except Exception:
        pass
    
    # Main title
    title = tk.Label(
        content,
        text="Start Managing Your\nConstruction Costs Today",
        bg=colors.secondary,
        fg=colors.text_white,
        font=get_font(theme.fonts.title_large, bold=True)
    )
    title.pack(pady=(0, spacing.md))
    
    # Benefits list with better spacing
    benefits = [
        "📊 Real-time budget tracking",
        "💰 Prevent cost overruns",
        "🏗️ Manage multiple projects",
        "📱 Access from anywhere",
        "🔒 Secure & reliable",
        "📈 Detailed analytics",
        "⚡ Instant notifications",
        "👥 Team collaboration"
    ]
    
    for benefit in benefits:
        benefit_label = tk.Label(
            content,
            text=benefit,
            bg=colors.secondary,
            fg=colors.text_white,
            font=get_font(theme.fonts.body_large)
        )
        benefit_label.pack(pady=spacing.sm, anchor="w")
    
    # Statistics section
    stats_frame = tk.Frame(content, bg=colors.secondary)
    stats_frame.pack(pady=spacing.xl, fill="x")
    
    stats = [
        ("500+", "Companies"),
        ("2M+", "Projects Managed"),
        ("24/7", "Support")
    ]
    
    for stat_value, stat_label in stats:
        stat_row = tk.Frame(stats_frame, bg=colors.secondary)
        stat_row.pack(fill="x", pady=spacing.sm)
        
        value_label = tk.Label(
            stat_row,
            text=stat_value,
            bg=colors.secondary,
            fg=colors.text_white,
            font=get_font(theme.fonts.title_large, bold=True)
        )
        value_label.pack(side="left")
        
        desc_label = tk.Label(
            stat_row,
            text=stat_label,
            bg=colors.secondary,
            fg=colors.text_light,
            font=get_font(theme.fonts.body_normal)
        )
        desc_label.pack(side="left", padx=spacing.sm)
    
    # CTA
    cta_label = tk.Label(
        content,
        text="Free trial available • No credit card required\nStart your 14-day free trial today",
        bg=colors.secondary,
        fg=colors.text_light,
        font=get_font(theme.fonts.body_normal)
    )
    cta_label.pack(pady=(spacing.xl, 0))