# UNKNOWN.

An editorial index behind a server-checked access gate.

## Run locally

1. Create a virtual environment and install `requirements.txt`.
2. Copy `.env.example` to `.env` and set a private `SITE_PASSWORD` and a long random `SESSION_SECRET`.
3. Run `python server.py` and open `http://127.0.0.1:5000`.

The `.env` file is git-ignored. The password is read only by the server and is never sent to the browser. For public deployment, provide the same variables through the host's secret settings, use HTTPS, and run behind a production WSGI server.

Locally, nomination and access-request submissions are appended to the private, git-ignored `submissions.json` file in the project root. If `DATABASE_URL` is set, both forms use PostgreSQL instead.

## Deploy on Vercel

Import this repository in Vercel and set the project root to this folder. Vercel detects the Flask app in `server.py`; static assets are served from `public/`, while protected pages are rendered from `templates/`. Configure `SITE_PASSWORD` and `SESSION_SECRET` as Vercel environment variables for Production, Preview, and Development as needed. Use a long random value for `SESSION_SECRET`.

Vercel Functions have a read-only filesystem, so local JSON files cannot store production submissions durably. [Install a Postgres integration such as Neon from Vercel Marketplace](https://vercel.com/marketplace/neon), connect it to this project, and ensure its `DATABASE_URL` environment variable is available to Production. The app creates a private `unknown_submissions` table on the first submission and stores both nomination and access-request form entries there. Redeploy after adding the integration. Without `DATABASE_URL`, the API safely returns a temporary-unavailable response instead of losing submissions.

To review entries in the database SQL editor, run `SELECT id, type, received_at, payload FROM unknown_submissions ORDER BY received_at DESC;`. Treat access-request details as confidential and apply an appropriate retention period.
