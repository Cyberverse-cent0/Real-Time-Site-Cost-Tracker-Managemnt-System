import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import main_windows
import login_win


def main() -> None:
    main_windows.center_on_screen()
    
    # Initialize theme engine before using theme (optional for login screen)
    try:
        from ui.theme.engine import init_engine
        from ui.theme.store import AppearanceStore
        init_engine(main_windows.get_root(), AppearanceStore())
        print("Theme engine initialized successfully")
    except Exception as e:
        print(f"Warning: Could not initialize theme engine: {e}")
        # Continue without theme engine - fallback colors will be used
    
    login_win.create_login_frame(main_windows.get_root())
    print("Login frame created successfully")
    main_windows.run()


if __name__ == "__main__":
    main()
