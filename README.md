# UNKNOWN.

An editorial index behind a server-checked access gate.

## Run locally

1. Create a virtual environment and install `requirements.txt`.
2. Copy `.env.example` to `.env` and set a private `SITE_PASSWORD` and a long random `SESSION_SECRET`.
3. Run `python server.py` and open `http://127.0.0.1:5000`.

The `.env` file is git-ignored. The password is read only by the server and is never sent to the browser. For public deployment, provide the same variables through the host's secret settings, use HTTPS, and run behind a production WSGI server.

Nomination form submissions are appended to the private, git-ignored `submissions.json` file in the project root. Protect the host and its disk backups as confidential applicant data. The access-request form is not connected to a storage destination yet.

## Deploy on Render

This folder includes a Render Blueprint (`render.yaml`). Create a Blueprint from the project repository, then set `SITE_PASSWORD` as a secret value when prompted. The Blueprint generates `SESSION_SECRET`, runs the app with Gunicorn, and mounts persistent storage at `/var/data` for nomination records. Persistent storage may incur hosting charges; review the plan and current price in Render before launching.
