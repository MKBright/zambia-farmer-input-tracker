"""Start the local web app.

From the project folder:

    python run.py

Then open http://127.0.0.1:5000 in a browser on this computer.
The app listens only on localhost, so other machines cannot connect.

Set PORT=5001 if port 5000 is already in use.
Set FLASK_DEBUG=1 only while you are changing the code.
"""

import os

from app import create_app

app = create_app()

if __name__ == "__main__":
    debug = os.environ.get("FLASK_DEBUG") == "1"
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="127.0.0.1", port=port, debug=debug)
