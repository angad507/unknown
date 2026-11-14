# UNKNOWN.

An editorial index behind a server-checked access gate.

## Run locally

1. Create a virtual environment and install `requirements.txt`.
2. Copy `.env.example` to `.env` and set a private `SITE_PASSWORD`, a long random `SESSION_SECRET`, and a Fernet `SUBMISSIONS_ENCRYPTION_KEY`.
3. Run `python server.py` and open `http://127.0.0.1:5000`.

The `.env` file is git-ignored. The password is read only by the server and is never sent to the browser. For public deployment, provide the same variables through the host's secret settings, use HTTPS, and run behind a production WSGI server.

Locally, nomination and access-request submissions are encrypted and appended to the private, git-ignored `submissions.txt` file. Production submissions are encrypted before upload and stored as separate private `.txt` objects in Vercel Blob.

## Deploy on Vercel

Import this repository in Vercel and set the project root to this folder. Vercel detects the Flask app in `server.py`; static assets are served from `public/`, while protected pages are rendered from `templates/`. Configure `SITE_PASSWORD` and `SESSION_SECRET` as Vercel environment variables for Production, Preview, and Development as needed. Use a long random value for `SESSION_SECRET`.

Vercel Functions have a read-only filesystem, so the app stores production submissions in Vercel Blob rather than on the function's disk. In the Vercel project, create a **Private Blob** store and connect it to the project for Production. Vercel supplies the Blob connection settings to the app through project-scoped credentials. Add `SUBMISSIONS_ENCRYPTION_KEY` as a Vercel secret environment variable, using the same key kept in your local `.env`. Generate a Fernet key with `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`. Keep this key separate from the `.txt` objects and back it up securely; losing it makes the submissions unreadable. Redeploy after configuring the store and key. Without either setting, the form returns an error instead of claiming the submission was saved.

Blob objects are private and contain Fernet-encrypted UTF-8 JSON in `.txt` files. To read a local file, run `python decrypt_submissions.py submissions.txt`. For production, download the private `.txt` objects from the Vercel Blob dashboard and decrypt them with `python decrypt_submissions.py <downloaded-file>`. Treat access-request details as confidential and apply an appropriate retention period.
