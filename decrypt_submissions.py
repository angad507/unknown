"""Decrypt local or downloaded UNKNOWN submission text files to standard output."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", type=Path, help="Encrypted submissions .txt file")
    args = parser.parse_args()
    key = os.environ.get("SUBMISSIONS_ENCRYPTION_KEY", "").strip()
    if not key:
        parser.error("Set SUBMISSIONS_ENCRYPTION_KEY in .env or the environment first.")
    try:
        cipher = Fernet(key.encode("ascii"))
    except (ValueError, UnicodeEncodeError):
        parser.error("SUBMISSIONS_ENCRYPTION_KEY is not a valid Fernet key.")

    output = []
    try:
        for line_number, token in enumerate(args.file.read_bytes().splitlines(), 1):
            if not token.strip():
                continue
            try:
                output.append(json.loads(cipher.decrypt(token).decode("utf-8")))
            except (InvalidToken, UnicodeDecodeError, json.JSONDecodeError) as exc:
                parser.error(f"Could not decrypt line {line_number}; check the file and key ({exc}).")
    except OSError as exc:
        parser.error(f"Could not read the encrypted file: {exc}")
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
