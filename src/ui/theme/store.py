# store.py
"""AppearanceStore — per-user theme persistence + theme file export/import.

Preferences are stored as JSON in the `user_preferences` table, keyed by
username, and follow the user across logins. Export/import writes the same
JSON to a file so themes can be shared ("Cyberverse Dark" etc.).
"""
import json
import os

try:
    from ...db import app_db
except ImportError:  # pragma: no cover - flat sys.path layout (src/ on path)
    from db import app_db

from .spec import ThemeSpec

THEME_FILE_VERSION = 1


class AppearanceStore:
    def __init__(self):
        self._current_user: str | None = None

    # ---- per-user profile storage ----
    def set_current_user(self, username: str | None) -> None:
        self._current_user = username

    @property
    def current_user(self) -> str | None:
        return self._current_user

    def load(self, username: str) -> ThemeSpec | None:
        """Load the saved ThemeSpec for a user (None if never saved)."""
        conn = None
        try:
            conn = app_db.get_database_connection()
            cur = conn.cursor()
            cur.execute(
                app_db.q("SELECT prefs_json FROM user_preferences WHERE username = ?;"),
                (username,),
            )
            row = cur.fetchone()
            cur.close()
            if row is None:
                return None
            data = json.loads(row[0])
            return ThemeSpec.from_dict(data.get("spec", data))
        except Exception as e:
            print(f"Error loading preferences: {e}")
            return None
        finally:
            if conn is not None:
                conn.close()

    def save(self, username: str, spec: ThemeSpec) -> bool:
        conn = None
        try:
            conn = app_db.get_database_connection()
            cur = conn.cursor()
            cur.execute(
                app_db.q("""
                    INSERT INTO user_preferences (username, prefs_json, updated_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(username) DO UPDATE SET
                        prefs_json = excluded.prefs_json,
                        updated_at = CURRENT_TIMESTAMP;
                """),
                (username, json.dumps({"spec": spec.to_dict()})),
            )
            conn.commit()
            cur.close()
            return True
        except Exception as e:
            print(f"Error saving preferences: {e}")
            return False
        finally:
            if conn is not None:
                conn.close()

    # ---- theme file export / import ----
    def export_theme(self, path: str, spec: ThemeSpec, name: str = "My Theme") -> bool:
        payload = {
            "name": name,
            "version": THEME_FILE_VERSION,
            "spec": spec.to_dict(),
            # Also expose a flat "colors" view for humans / other tools.
            "colors": {
                k: v for k, v in spec.custom_colors.items()
            } or {"primary": spec.accent},
            "layout": {
                "density": spec.density,
                "radius": spec.radius,
                "sidebar": spec.sidebar,
            },
            "typography": {
                "font_family": spec.font_family,
                "font_scale": spec.font_scale,
            },
        }
        try:
            os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(payload, fh, indent=2)
            return True
        except OSError as e:
            print(f"Error exporting theme: {e}")
            return False

    def import_theme(self, path: str) -> tuple[str | None, ThemeSpec | None]:
        """Return (theme_name, spec) or (None, None) on failure."""
        try:
            with open(path, "r", encoding="utf-8") as fh:
                payload = json.load(fh)
        except (OSError, json.JSONDecodeError) as e:
            print(f"Error importing theme: {e}")
            return None, None

        name = str(payload.get("name") or os.path.splitext(os.path.basename(path))[0])
        data = payload.get("spec", payload)
        if not isinstance(data, dict):
            return None, None
        return name, ThemeSpec.from_dict(data)
