"""Farm Input Tracker.

A small local web app for recording farming inputs, planting, and harvests.
It is meant for a camp extension officer or a farmer who keeps records on
one computer. Nothing is sent to the internet.
"""

import os
from pathlib import Path

from flask import Flask, render_template

from app.db import close_db, connect, init_db
from app.formatting import format_amount, format_hectares, format_kg, human_date
from app.routes import bp

# Folder that contains run.py, requirements.txt, and the data directory.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB = PROJECT_ROOT / "data" / "farm_tracker.db"


def create_app(db_path=None):
    """Build the Flask app.

    Tests pass a temporary db_path so they never touch the real file.
    A normal run uses data/farm_tracker.db inside the project folder.
    """
    app = Flask(__name__)
    # Flash messages need a secret. This default is fine on a private computer.
    # Set FLASK_SECRET_KEY if you ever share the app with other users.
    app.config["SECRET_KEY"] = os.environ.get(
        "FLASK_SECRET_KEY", "local-dev-only-change-me"
    )

    database = Path(db_path) if db_path else DEFAULT_DB
    if not database.is_absolute():
        database = PROJECT_ROOT / database
    app.config["DATABASE"] = str(database)

    app.teardown_appcontext(close_db)
    app.register_blueprint(bp)
    _register_template_filters(app)
    _register_error_pages(app)

    # Create the empty tables the first time, and do nothing if they exist.
    connection = connect(app.config["DATABASE"])
    try:
        init_db(connection)
    finally:
        connection.close()

    return app


def _register_template_filters(app):
    """Filters used by the HTML pages to show dates and numbers."""

    @app.template_filter("humandate")
    def humandate_filter(value):
        return human_date(value)

    @app.template_filter("num")
    def num_filter(value):
        if value is None:
            return "—"
        return format_amount(value)

    @app.template_filter("ha")
    def ha_filter(value):
        if value is None:
            return "—"
        return format_hectares(value)

    @app.template_filter("kg")
    def kg_filter(value):
        if value is None:
            return "—"
        return format_kg(value)


def _register_error_pages(app):
    @app.errorhandler(404)
    def not_found(_error):
        return render_template("not_found.html"), 404
