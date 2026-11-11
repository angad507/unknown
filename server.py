from __future__ import annotations

import hmac
import json
import os
import secrets
import threading
from pathlib import Path
from datetime import datetime, timezone

from flask import Flask, abort, make_response, redirect, request, send_from_directory
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")
PASSWORD = os.environ.get("SITE_PASSWORD", "")
SESSION_SECRET = os.environ.get("SESSION_SECRET", "")
if not PASSWORD or not SESSION_SECRET:
    raise RuntimeError("Set SITE_PASSWORD and SESSION_SECRET in the local .env file.")

app = Flask(__name__, static_folder=None)
app.secret_key = SESSION_SECRET
SUBMISSIONS_FILE = ROOT / "submissions.json"
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
    """Allow one top-level page load; keep its assets/API usable until expiry."""
    valid, nonce = valid_grant(token)
    if not valid:
        return False
    grant_file = ROOT / (".grant-" + Path(nonce).name)
    try:
        fd = os.open(grant_file, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        os.close(fd)
        return True
    except FileExistsError:
        return False


def make_grant() -> str:
    import hashlib
    import time

    nonce = secrets.token_urlsafe(24)
    expires = str(int(time.time()) + 30)
    payload = f"{nonce}.{expires}"
    signature = hmac.new(SESSION_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return payload + "." + signature


def gate(message: str = ""):
    response = make_response(send_from_directory(ROOT / "public", "gate.html"))
    if message:
        response.headers["X-Gate-Message"] = message
    return response


@app.get("/gate.css")
def gate_css():
    return send_from_directory(ROOT / "public", "gate.css")


@app.post("/unlock")
def unlock():
    supplied = request.form.get("password", "")
    if not hmac.compare_digest(supplied.encode(), PASSWORD.encode()):
        return gate("The phrase was not recognised. Please try again."), 401
    response = redirect("/", code=303)
    # No persistent cookie lifetime: access ends when the browser session ends.
    response.set_cookie("unknown_access", make_grant(), httponly=True, secure=request.is_secure,
                        samesite="Lax", path="/")
    return response


@app.post("/leave")
def leave():
    response = redirect("/", code=303)
    response.delete_cookie("unknown_access", path="/")
    return response


@app.post("/api/nomination")
def submit_nomination():
    valid, _ = valid_grant(request.cookies.get("unknown_access", ""))
    if not valid:
        return {"error": "Your access has expired. Enter the password again."}, 401
    if not request.is_json:
        return {"error": "Expected a JSON submission."}, 400
    payload = request.get_json(silent=True) or {}
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
    record = {"received_at": datetime.now(timezone.utc).isoformat(), **fields}
    with SUBMISSIONS_LOCK:
        try:
            existing = json.loads(SUBMISSIONS_FILE.read_text(encoding="utf-8")) if SUBMISSIONS_FILE.exists() else []
            if not isinstance(existing, list):
                raise ValueError("Submission store must contain a JSON array.")
        except (json.JSONDecodeError, OSError, ValueError):
            app.logger.exception("Cannot read nomination store")
            return {"error": "The nomination could not be saved. Please try again later."}, 500
        existing.append(record)
        temp_file = SUBMISSIONS_FILE.with_suffix(".json.tmp")
        try:
            temp_file.write_text(json.dumps(existing, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            os.replace(temp_file, SUBMISSIONS_FILE)
        except OSError:
            app.logger.exception("Cannot write nomination store")
            return {"error": "The nomination could not be saved. Please try again later."}, 500
    return {"message": "Thank you. Your nomination has been received for private consideration."}, 201


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def site(path: str):
    token = request.cookies.get("unknown_access", "")
    # A browser refresh is a document navigation. The initial document consumes
    # the grant; its CSS, scripts, images, and form requests remain usable.
    is_document = not path or path == "index.html"
    authorized = consume_document_grant(token) if is_document else valid_grant(token)[0]
    if not authorized:
        return gate()
    public = ROOT / "public"
    target = (public / path).resolve() if path else public / "index.html"
    if not target.is_relative_to(public.resolve()) or not target.is_file():
        abort(404)
    return send_from_directory(public, target.relative_to(public).as_posix())


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", "5000")), debug=False)
