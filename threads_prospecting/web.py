"""Local web UI for generating Threads posts and replies.

Runs a Flask server bound to 127.0.0.1 only and opens the default browser
automatically, so the whole flow (account config, API key, post/reply
generation) happens in the browser instead of editing files by hand.
"""

from __future__ import annotations

import os
import threading
import webbrowser
from pathlib import Path

import yaml
from flask import Flask, jsonify, request

from .client import MissingAPIKeyError
from .config import load_account_config
from .generator import generate_post, generate_reply

BASE_DIR = Path(__file__).resolve().parent.parent
ACCOUNT_PATH = BASE_DIR / "account.yaml"
ENV_PATH = BASE_DIR / ".env"

ACCOUNT_FIELDS = ("nicho", "tom", "publico", "nome_da_conta")

app = Flask(__name__)


def _empty_account() -> dict:
    return {field: "" for field in ACCOUNT_FIELDS}


def _read_account() -> dict:
    if not ACCOUNT_PATH.exists():
        return _empty_account()
    try:
        account = load_account_config(ACCOUNT_PATH)
    except ValueError:
        return _empty_account()
    return {field: getattr(account, field) for field in ACCOUNT_FIELDS}


def _write_account(data: dict) -> None:
    ACCOUNT_PATH.write_text(
        yaml.safe_dump(
            {field: (data.get(field) or "").strip() for field in ACCOUNT_FIELDS},
            allow_unicode=True,
            sort_keys=False,
        ),
        encoding="utf-8",
    )


def _read_api_key() -> str:
    if not ENV_PATH.exists():
        return ""
    for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        if line.startswith("ANTHROPIC_API_KEY="):
            return line.split("=", 1)[1].strip()
    return ""


def _write_api_key(api_key: str) -> None:
    lines = []
    found = False
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
            if line.startswith("ANTHROPIC_API_KEY="):
                lines.append(f"ANTHROPIC_API_KEY={api_key}")
                found = True
            else:
                lines.append(line)
    if not found:
        lines.append(f"ANTHROPIC_API_KEY={api_key}")
    ENV_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    os.environ["ANTHROPIC_API_KEY"] = api_key


@app.get("/")
def index():
    from flask import render_template

    return render_template("index.html")


@app.get("/api/config")
def get_config():
    return jsonify({"account": _read_account(), "api_key_set": bool(_read_api_key())})


@app.post("/api/config")
def save_config():
    payload = request.get_json(silent=True) or {}
    account = payload.get("account") or {}

    missing = [field for field in ACCOUNT_FIELDS if not (account.get(field) or "").strip()]
    if missing:
        return jsonify({"error": f"Preencha todos os campos: {', '.join(missing)}."}), 400

    _write_account(account)

    api_key = (payload.get("api_key") or "").strip()
    if api_key:
        _write_api_key(api_key)

    return jsonify({"ok": True})


@app.post("/api/post")
def api_post():
    payload = request.get_json(silent=True) or {}
    topic = (payload.get("topic") or "").strip()
    if not topic:
        return jsonify({"error": "Informe um tema para o post."}), 400

    try:
        account = load_account_config(ACCOUNT_PATH)
        return jsonify({"post": generate_post(account, topic)})
    except FileNotFoundError:
        return jsonify({"error": "Configure a conta na aba Configurações antes de gerar um post."}), 400
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except MissingAPIKeyError as exc:
        return jsonify({"error": str(exc)}), 400


@app.post("/api/reply")
def api_reply():
    payload = request.get_json(silent=True) or {}
    comment = (payload.get("comment") or "").strip()
    if not comment:
        return jsonify({"error": "Cole o comentário que deseja responder."}), 400

    try:
        account = load_account_config(ACCOUNT_PATH)
        reply = generate_reply(account, comment)
        return jsonify({"reply": reply, "skip": reply is None})
    except FileNotFoundError:
        return jsonify({"error": "Configure a conta na aba Configurações antes de gerar uma resposta."}), 400
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except MissingAPIKeyError as exc:
        return jsonify({"error": str(exc)}), 400


def main() -> None:
    port = int(os.environ.get("PORT", "8765"))
    url = f"http://127.0.0.1:{port}/"

    threading.Timer(1.25, lambda: webbrowser.open(url)).start()
    app.run(host="127.0.0.1", port=port, debug=False, use_reloader=False)


if __name__ == "__main__":
    main()
