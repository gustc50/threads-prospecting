"""Local web UI for generating Threads posts/replies and running prospecting.

Runs a Flask server bound to 127.0.0.1 only and opens the default browser
automatically, so the whole flow (account config, API keys, post/reply
generation, and searching+replying to leads on Threads) happens in the
browser instead of editing files or the command line by hand.
"""

from __future__ import annotations

import os
import threading
import webbrowser
from pathlib import Path

import yaml
from flask import Flask, jsonify, render_template, request

from .client import MissingAPIKeyError
from .config import load_account_config
from .generator import generate_post, generate_reply
from .prospecting import find_leads, publish_lead_reply, run_prospecting
from .threads_client import ThreadsAPIError, ThreadsClient

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


def _read_env(name: str) -> str:
    """Read a single KEY=value entry from the .env file."""
    if not ENV_PATH.exists():
        return ""
    prefix = f"{name}="
    for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        if line.startswith(prefix):
            return line[len(prefix):].strip()
    return ""


def _write_env(name: str, value: str) -> None:
    """Set (or replace) a single KEY=value entry in the .env file."""
    prefix = f"{name}="
    lines = []
    found = False
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
            if line.startswith(prefix):
                lines.append(f"{name}={value}")
                found = True
            else:
                lines.append(line)
    if not found:
        lines.append(f"{name}={value}")
    ENV_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    os.environ[name] = value


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/config")
def get_config():
    return jsonify(
        {"account": _read_account(), "api_key_set": bool(_read_env("ANTHROPIC_API_KEY"))}
    )


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
        _write_env("ANTHROPIC_API_KEY", api_key)

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


@app.get("/api/threads-config")
def get_threads_config():
    return jsonify(
        {
            "user_id": _read_env("THREADS_USER_ID"),
            "token_set": bool(_read_env("THREADS_ACCESS_TOKEN")),
        }
    )


@app.post("/api/threads-config")
def save_threads_config():
    payload = request.get_json(silent=True) or {}
    user_id = (payload.get("user_id") or "").strip()
    token = (payload.get("token") or "").strip()

    if user_id:
        _write_env("THREADS_USER_ID", user_id)
    if token:
        _write_env("THREADS_ACCESS_TOKEN", token)

    return jsonify({"ok": True})


def _load_threads_client() -> ThreadsClient:
    token = _read_env("THREADS_ACCESS_TOKEN")
    user_id = _read_env("THREADS_USER_ID") or "me"
    return ThreadsClient(access_token=token, user_id=user_id)


@app.post("/api/prospect/search")
def api_prospect_search():
    payload = request.get_json(silent=True) or {}
    keywords = [k.strip() for k in (payload.get("keywords") or []) if k.strip()]
    auto_publish = bool(payload.get("auto_publish"))

    if not keywords:
        return jsonify({"error": "Informe ao menos uma palavra-chave."}), 400

    try:
        account = load_account_config(ACCOUNT_PATH)
    except FileNotFoundError:
        return jsonify({"error": "Configure a conta na aba Configurações antes de prospectar."}), 400
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    try:
        threads = _load_threads_client()
        pipeline = run_prospecting if auto_publish else find_leads
        leads = pipeline(threads, account, keywords)
    except (ThreadsAPIError, MissingAPIKeyError) as exc:
        return jsonify({"error": str(exc)}), 400

    return jsonify({"leads": leads})


@app.post("/api/prospect/publish")
def api_prospect_publish():
    payload = request.get_json(silent=True) or {}
    post_id = (payload.get("post_id") or "").strip()
    text = (payload.get("text") or "").strip()
    if not post_id or not text:
        return jsonify({"error": "post_id e text são obrigatórios."}), 400

    try:
        threads = _load_threads_client()
        published_id = publish_lead_reply(threads, post_id, text)
    except ThreadsAPIError as exc:
        return jsonify({"error": str(exc)}), 400

    return jsonify({"published_id": published_id})


def main() -> None:
    port = int(os.environ.get("PORT", "8765"))
    url = f"http://127.0.0.1:{port}/"

    threading.Timer(1.25, lambda: webbrowser.open(url)).start()
    app.run(host="127.0.0.1", port=port, debug=False, use_reloader=False)


if __name__ == "__main__":
    main()
