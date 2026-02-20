"""
WSGI entry point for PythonAnywhere.

In the PythonAnywhere Web tab, set:
  Source code:   /home/<username>/bg_best_year
  Working dir:   /home/<username>/bg_best_year
  WSGI file:     /home/<username>/bg_best_year/wsgi.py
"""

import sys
import os
from pathlib import Path

# Make sure the project root is on the Python path
project_home = str(Path(__file__).parent)
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Set required environment variables if not already set via the PA env-var panel
os.environ.setdefault("SECRET_KEY", "CHANGE-ME-IN-PYTHONANYWHERE-ENV-VARS")
os.environ.setdefault("ADMIN_SECRET", "CHANGE-ME-IN-PYTHONANYWHERE-ENV-VARS")

from webapp.app import create_app

application = create_app()
