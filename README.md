# UNKNOWN.

An editorial index behind a server-checked access gate.

## Run locally

1. Create a virtual environment and install `requirements.txt`.
2. Copy `.env.example` to `.env` and set a private `SITE_PASSWORD` and a long random `SESSION_SECRET`.
3. Run `python server.py` and open `http://127.0.0.1:5000`.

The `.env` file is git-ignored. The password is read only by the server and is never sent to the browser. For public deployment, provide the same variables through the host's secret settings, use HTTPS, and run behind a production WSGI server.

Nomination form submissions are appended to the private, git-ignored `submissions.json` file in the project root. Protect the host and its disk backups as confidential applicant data. The access-request form is not connected to a storage destination yet.

## Deploy on Vercel

Import this repository in Vercel and set the project root to this folder. Vercel detects the Flask app in `server.py`; static assets are served from `public/`, while protected pages are rendered from `templates/`. Configure `SITE_PASSWORD` and `SESSION_SECRET` as Vercel environment variables for Production, Preview, and Development as needed. Use a long random value for `SESSION_SECRET`.

Vercel Functions do not provide durable local file storage. The nomination endpoint intentionally returns a clear `503` until a durable database or storage service is configured; it will not claim that a nomination was saved when it was not. The local development server continues to save nominations to `submissions.json`.
