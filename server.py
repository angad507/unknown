from __future__ import annotations

import hmac
import json
import os
import re
import secrets
import threading
from pathlib import Path
from datetime import datetime, timezone

from flask import Flask, abort, make_response, redirect, render_template, request, send_from_directory
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")
PASSWORD = os.environ.get("SITE_PASSWORD", "")
SESSION_SECRET = os.environ.get("SESSION_SECRET", "")
if not PASSWORD or not SESSION_SECRET:
    raise RuntimeError("Set SITE_PASSWORD and SESSION_SECRET in the local .env file.")

app = Flask(__name__, static_folder=None)
app.secret_key = SESSION_SECRET
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024
DATA_DIR = Path(os.environ.get("DATA_DIR", str(ROOT))).resolve()
DATA_DIR.mkdir(parents=True, exist_ok=True)
SUBMISSIONS_FILE = DATA_DIR / "submissions.json"
SUBMISSIONS_LOCK = threading.Lock()


def signed_token() -> str:
    import hashlib

    nonce = secrets.token_urlsafe(24)
    signature = hmac.new(SESSION_SECRET.encode(), nonce.encode(), hashlib.sha256).hexdigest()
    return nonce + "." + signature


def valid_grant(token: str) -> tuple[bool, str]:
    """Check a short-lived signed grant and return its unique nonce."""
    import hashlib
    import time

    try:
        nonce, expires, signature = token.rsplit(".", 2)
        if int(expires) < int(time.time()):
            return False, ""
    except (ValueError, TypeError):
        return False, ""
    payload = f"{nonce}.{expires}"
    expected = hmac.new(SESSION_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature, expected):
        return False, ""
    return True, nonce


def consume_document_grant(token: str) -> bool:
    """Retained name for callers; grant validation is stateless on Vercel."""
    return valid_grant(token)[0]


def make_grant() -> str:
    import hashlib
    import time

    nonce = secrets.token_urlsafe(24)
    expires = str(int(time.time()) + 3600)
    payload = f"{nonce}.{expires}"
    signature = hmac.new(SESSION_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return payload + "." + signature


def gate(message: str = ""):
    response = make_response(render_template("gate.html"))
    if message:
        response.headers["X-Gate-Message"] = message
    return response


@app.get("/health")
def health():
    return {"status": "ok"}, 200


@app.get("/gate.css")
def gate_css():
    return send_from_directory(ROOT / "public", "gate.css")


@app.post("/unlock")
def unlock():
    supplied = request.form.get("password", "")
    if not hmac.compare_digest(supplied.encode(), PASSWORD.encode()):
        return gate("The phrase was not recognised. Please try again."), 401
    response = redirect("/", code=303)
    response.set_cookie("unknown_access", make_grant(), httponly=True,
                        secure=request.is_secure or bool(os.environ.get("VERCEL")),
                        samesite="Lax", max_age=3600, path="/")
    return response


@app.post("/leave")
def leave():
    response = redirect("/", code=303)
    response.delete_cookie("unknown_access", path="/")
    return response


def save_submission(kind: str, fields: dict[str, str]) -> None:
    record = {"type": kind, "received_at": datetime.now(timezone.utc).isoformat(), **fields}
    database_url = os.environ.get("DATABASE_URL") or os.environ.get("POSTGRES_URL")
    if database_url:
        import psycopg

        from psycopg.types.json import Json

        with psycopg.connect(database_url, connect_timeout=5, autocommit=True,
                              options="-c statement_timeout=10000") as connection:
            connection.execute("""
                CREATE TABLE IF NOT EXISTS unknown_submissions (
                    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                    type TEXT NOT NULL CHECK (type IN ('nomination', 'access_request')),
                    received_at TIMESTAMPTZ NOT NULL,
                    payload JSONB NOT NULL
                )
            """)
            connection.execute(
                "INSERT INTO unknown_submissions (type, received_at, payload) VALUES (%s, %s, %s)",
                (kind, record["received_at"], Json(fields)),
            )
        return

    if os.environ.get("VERCEL"):
        raise RuntimeError("Persistent submission storage is not configured. Add DATABASE_URL in Vercel.")

    with SUBMISSIONS_LOCK:
        existing = json.loads(SUBMISSIONS_FILE.read_text(encoding="utf-8")) if SUBMISSIONS_FILE.exists() else []
        if not isinstance(existing, list):
            raise ValueError("Submission store must contain a JSON array.")
        existing.append(record)
        temp_file = SUBMISSIONS_FILE.with_suffix(".json.tmp")
        temp_file.write_text(json.dumps(existing, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        os.replace(temp_file, SUBMISSIONS_FILE)


def submit_form(kind: str):
    valid, _ = valid_grant(request.cookies.get("unknown_access", ""))
    if not valid:
        return {"error": "Your access has expired. Enter the password again."}, 401
    if not request.is_json:
        return {"error": "Expected a JSON submission."}, 400
    payload = request.get_json(silent=True) or {}
    if not isinstance(payload, dict):
        return {"error": "Please send a valid form submission."}, 400
    if kind == "nomination":
        fields = {
            "name": str(payload.get("name", "")).strip()[:160],
            "profile": str(payload.get("profile", "")).strip()[:500],
            "field": str(payload.get("field", "")).strip()[:200],
            "reason": str(payload.get("reason", "")).strip()[:500],
        }
        if not fields["name"] or not fields["field"] or not fields["reason"]:
            return {"error": "Please complete the required fields."}, 400
        if fields["profile"] and not fields["profile"].startswith(("https://", "http://")):
            return {"error": "Enter a valid website or profile URL."}, 400
        message = "Thank you. Your nomination has been received for private consideration."
    else:
        fields = {
            "name": str(payload.get("name", "")).strip()[:160],
            "email": str(payload.get("email", "")).strip()[:254],
            "profession": str(payload.get("profession", "")).strip()[:200],
            "reason": str(payload.get("reason", "")).strip()[:500],
        }
        if not all(fields.values()) or not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", fields["email"]):
            return {"error": "Please complete all fields with a valid email address."}, 400
        message = "Thank you. Your access request has been received for private consideration."
    try:
        save_submission(kind, fields)
    except (OSError, ValueError, json.JSONDecodeError, ImportError):
        app.logger.exception("Could not save %s", kind)
        return {"error": "The submission could not be saved. Please try again later."}, 500
    except RuntimeError:
        app.logger.exception("Submission storage is not configured")
        return {"error": "Submissions are temporarily unavailable. Please try again later."}, 503
    except Exception:
        app.logger.exception("Database error saving %s", kind)
        return {"error": "The submission could not be saved. Please try again later."}, 503
    return {"message": message}, 201


@app.post("/api/nomination")
def submit_nomination():
    return submit_form("nomination")


@app.post("/api/access-request")
def submit_access_request():
    return submit_form("access_request")


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def site(path: str):
    token = request.cookies.get("unknown_access", "")
    valid, nonce = valid_grant(token)
    # A browser refresh is a document navigation. The initial document consumes
    # the grant; its CSS, scripts, images, and form requests remain usable.
    is_document = not path or path == "index.html"
    seen = request.cookies.get("unknown_seen", "")
    authorized = valid and (not is_document or seen != nonce)
    if not authorized:
        return gate()
    if is_document:
        response = make_response(render_template("index.html"))
        response.set_cookie("unknown_seen", nonce, httponly=True,
                            secure=request.is_secure or bool(os.environ.get("VERCEL")),
                            samesite="Lax", max_age=3600, path="/")
        return response
    public = ROOT / "public"
    target = (public / path).resolve() if path else public / "index.html"
    if not target.is_relative_to(public.resolve()) or not target.is_file():
        abort(404)
    return send_from_directory(public, target.relative_to(public).as_posix())


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")), debug=False)
