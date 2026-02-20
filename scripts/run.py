"""Entry point: initialize DB if needed and run the Flask app."""

import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from webapp.app import create_app
from webapp.config import Config


def main():
    db_path = Path(Config.DATABASE)

    if not db_path.exists():
        print("Database not found. Initializing...")
        from scripts.init_db import main as init_main
        init_main()
        print()

    app = create_app()
    print("Starting Board Game Best Year tournament...")
    print(f"  App:   http://127.0.0.1:5000")
    print(f"  Admin: http://127.0.0.1:5000/admin/{Config.ADMIN_SECRET}")
    print()
    app.run(debug=True, port=5000)


if __name__ == "__main__":
    main()
