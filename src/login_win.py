# login_win.py
import tkinter as tk
from tkinter import messagebox
import pathlib

try:
    import sesion
except ModuleNotFoundError:  # pragma: no cover - compatibility when run as a package
    from db import sesion

import main_windows as mw
from app.theme import theme, get_font, apply_button_style, apply_entry_style, apply_label_style, create_card_frame
from ui.context_menu import attach_entry_menu


def _sync_auth_columns(main_container: tk.Frame, left_container: tk.Frame, right_container: tk.Frame) -> None:
    """Keep the form column near 25% of the window width and the promo column at 75%."""
    total_width = max(1, main_container.winfo_width())
    left_width = max(260, int(total_width * 0.25))
    left_container.config(width=left_width)
    right_container.config(width=max(1, total_width - left_width))


def create_login_frame(parent) -> tk.Frame:
    """Build the login form and return its frame."""
    colors = theme.colors
    spacing = theme.spacing
    
    # Set window background
    parent.config(bg=colors.bg_main)
    
    # Main container split into left (25%) and right (75%)
    main_container = tk.Frame(parent, bg=colors.bg_main)
    main_container.pack(expand=True, fill="both")
    main_container.pack_propagate(False)
    
    # Left side - Login form (25%)
    left_container = tk.Frame(main_container, bg=colors.bg_main)
    left_container.pack(side="left", fill="y")
    left_container.pack_propagate(False)
    
    # Right side - Advertising/Marketing content (75%)
    right_container = tk.Frame(main_container, bg=colors.primary)
    right_container.pack(side="right", fill="both", expand=True)
    right_container.pack_propagate(False)
    main_container.bind("<Configure>", lambda event: _sync_auth_columns(main_container, left_container, right_container))
    _sync_auth_columns(main_container, left_container, right_container)
    
    # Login card (smaller, centered on left)
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
    title_label = tk.Label(card, text="Site Cost Tracker", bg=colors.bg_card)
    apply_label_style(title_label, variant="title")
    title_label.pack(pady=(0, spacing.xs))
    
    subtitle_label = tk.Label(card, text="Sign in to your account", bg=colors.bg_card)
    apply_label_style(subtitle_label, variant="muted")
    subtitle_label.pack(pady=(0, spacing.lg))
    
    # Form container
    form_container = tk.Frame(card, bg=colors.bg_card)
    form_container.pack(padx=spacing.xl, pady=spacing.md)
    
    username_var = tk.StringVar()
    password_var = tk.StringVar()
    
    # Username field
    username_label = tk.Label(form_container, text="Username", bg=colors.bg_card)
    apply_label_style(username_label, variant="body")
    username_label.pack(anchor="w", pady=(spacing.sm, spacing.xs))
    
    username_entry = tk.Entry(form_container, textvariable=username_var, width=25)
    apply_entry_style(username_entry)
    username_entry.pack(fill="x", pady=(0, spacing.md))
    attach_entry_menu(username_entry)
    
    # Password field
    password_label = tk.Label(form_container, text="Password", bg=colors.bg_card)
    apply_label_style(password_label, variant="body")
    password_label.pack(anchor="w", pady=(spacing.sm, spacing.xs))
    
    password_entry = tk.Entry(form_container, textvariable=password_var, width=25, show="•")
    apply_entry_style(password_entry)
    password_entry.pack(fill="x", pady=(0, spacing.sm))
    attach_entry_menu(password_entry, sensitive=True)
    
    # Show password checkbox
    show_pw = tk.BooleanVar()
    checkbox_frame = tk.Frame(form_container, bg=colors.bg_card)
    checkbox_frame.pack(anchor="w", pady=(spacing.xs, spacing.lg))
    
    checkbutton = tk.Checkbutton(
        checkbox_frame,
        text="Show password",
        variable=show_pw,
        bg=colors.bg_card,
        fg=colors.text_secondary,
        activebackground=colors.bg_card,
        activeforeground=colors.text_primary,
        selectcolor=colors.bg_card,
        command=lambda: password_entry.config(show="" if show_pw.get() else "•"),
        font=get_font(theme.fonts.body_small)
    )
    checkbutton.pack()
    
    def on_login():
        username = username_var.get().strip()
        password = password_var.get()
        if not username or not password:
            messagebox.showwarning("Missing info", "Enter username and password.")
            return

        # Initialize database if needed
        try:
            from db import app_db
            if not app_db.database_exists():
                if not app_db.initialize_database():
                    messagebox.showerror("Database Error", "Failed to initialize database. Please check your permissions and try again.")
                    return
        except PermissionError as e:
            messagebox.showerror("Permission Error", f"Cannot create database directory. Check file permissions: {str(e)}")
            return
        except Exception as e:
            messagebox.showerror("Database Error", f"Database initialization failed: {str(e)}")
            return

        result = sesion.authenticate_user(username, password)
        if result.status:
            messagebox.showinfo("Welcome", f"Logged in as {username}")
            _open_main_window(username, result.token)
        else:
            messagebox.showerror("Login failed", result.message)
            password_var.set("")

    def open_create_account():
        mw.clear_root()
        import create_account
        create_account.create_create_account_frame(mw.get_root())

    # Button row
    btn_row = tk.Frame(card, bg=colors.bg_card)
    btn_row.pack(pady=(spacing.lg, spacing.md))
    
    login_btn = tk.Button(btn_row, text="Login", command=on_login)
    apply_button_style(login_btn, variant="primary", size="large")
    login_btn.pack(side="left", padx=spacing.xs)
    
    create_account_btn = tk.Button(btn_row, text="Create Account", command=open_create_account)
    apply_button_style(create_account_btn, variant="outline", size="large")
    create_account_btn.pack(side="left", padx=spacing.xs)
    
    exit_btn = tk.Button(btn_row, text="Exit", command=mw.get_root().destroy)
    apply_button_style(exit_btn, variant="ghost", size="large")
    exit_btn.pack(side="left", padx=spacing.xs)

    username_entry.focus_set()
    mw.get_root().bind("<Return>", lambda e: on_login())
    
    _create_advertising_content(right_container)

    return main_container


def _create_advertising_content(parent: tk.Frame):
    """Create advertising/features content on the right side."""
    colors = theme.colors
    spacing = theme.spacing
    
    # Content container
    content = tk.Frame(parent, bg=colors.primary)
    content.pack(expand=True, fill="both", padx=spacing.xxl, pady=spacing.xxl)
    
    # Large logo
    try:
        logo_path = pathlib.Path("public/logo.svg")
        if logo_path.exists():
            logo = tk.PhotoImage(file=str(logo_path)).subsample(2, 2)
            logo_label = tk.Label(content, image=logo, bg=colors.primary)
            logo_label.image = logo
            logo_label.pack(pady=(spacing.xxl, spacing.lg))
    except Exception:
        pass
    
    # Main title
    title = tk.Label(
        content,
        text="Construction Cost\nManagement Made Simple",
        bg=colors.primary,
        fg=colors.text_white,
        font=get_font(theme.fonts.title_large, bold=True)
    )
    title.pack(pady=(0, spacing.md))
    
    # Features list with better spacing
    features = [
        "✓ Real-time cost tracking",
        "✓ Budget management & alerts",
        "✓ Multi-site support",
        "✓ Detailed analytics & reports",
        "✓ Role-based access control",
        "✓ Mobile-friendly interface",
        "✓ Automated invoicing",
        "✓ Cloud-based backup"
    ]
    
    for feature in features:
        feature_label = tk.Label(
            content,
            text=feature,
            bg=colors.primary,
            fg=colors.text_white,
            font=get_font(theme.fonts.body_large)
        )
        feature_label.pack(pady=spacing.sm, anchor="w")
    
    # Statistics section
    stats_frame = tk.Frame(content, bg=colors.primary)
    stats_frame.pack(pady=spacing.xl, fill="x")
    
    stats = [
        ("10K+", "Active Users"),
        ("50M+", "Costs Tracked"),
        ("99.9%", "Uptime")
    ]
    
    for stat_value, stat_label in stats:
        stat_row = tk.Frame(stats_frame, bg=colors.primary)
        stat_row.pack(fill="x", pady=spacing.sm)
        
        value_label = tk.Label(
            stat_row,
            text=stat_value,
            bg=colors.primary,
            fg=colors.text_white,
            font=get_font(theme.fonts.title_large, bold=True)
        )
        value_label.pack(side="left")
        
        desc_label = tk.Label(
            stat_row,
            text=stat_label,
            bg=colors.primary,
            fg=colors.text_light,
            font=get_font(theme.fonts.body_normal)
        )
        desc_label.pack(side="left", padx=spacing.sm)
    
    # CTA
    cta_label = tk.Label(
        content,
        text="Join thousands of construction professionals\nwho trust Site Cost Tracker",
        bg=colors.primary,
        fg=colors.text_light,
        font=get_font(theme.fonts.body_normal)
    )
    cta_label.pack(pady=(spacing.xl, 0))


def _open_main_window(username: str, token: str) -> None:
    """Replace login screen with the main app screen."""
    mw.clear_root()
    mw.set_window_title("Site Cost Tracker — Dashboard")

    colors = theme.colors
    mw.get_root().config(bg=colors.bg_main)

    from app.dashboard import Dashboard
    Dashboard(mw.get_root(), username)