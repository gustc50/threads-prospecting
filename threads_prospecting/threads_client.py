"""Thin wrapper around Meta's Threads API (graph.threads.net).

Docs: https://developers.facebook.com/docs/threads

Using this requires a Meta developer app with Threads API access, and a
user access token with `threads_basic` (required for every call),
`threads_manage_replies` (posting replies) and `threads_keyword_search`
(searching posts beyond your own) — the last one is a restricted
permission Meta has to approve for your app case by case. Field/param
names here follow the API as of this writing; check Meta's docs if a
call starts failing after a platform update.
"""

from __future__ import annotations

import re
import time
from typing import Any, Callable

import requests

GRAPH_BASE = "https://graph.threads.net/v1.0"
TIMEOUT = 20

# Meta recommends waiting for a media container to finish processing before
# publishing it; poll its status_code instead of guessing a fixed delay.
CONTAINER_POLL_INTERVAL = 3
CONTAINER_MAX_WAIT = 60

_TOKEN_RE = re.compile(r"access_token=[^&\s]+")


def _redact(text: str) -> str:
    """Strip the access token out of error text before it reaches the browser."""
    return _TOKEN_RE.sub("access_token=***", text)


class ThreadsAPIError(RuntimeError):
    """Raised for any failure talking to the Threads API."""


class ThreadsClient:
    """Calls the Threads API to search public posts and publish replies."""

    def __init__(
        self,
        access_token: str,
        user_id: str = "me",
        session: requests.Session | None = None,
        sleep_fn: Callable[[float], None] = time.sleep,
    ):
        if not access_token:
            raise ThreadsAPIError(
                "Token de acesso do Threads não configurado (aba Prospecção)."
            )
        self.access_token = access_token
        self.user_id = user_id or "me"
        self._session = session or requests.Session()
        self._sleep = sleep_fn

    def _request(self, method: str, path: str, params: dict[str, Any]) -> dict:
        url = f"{GRAPH_BASE}/{path}"
        params = {**params, "access_token": self.access_token}
        try:
            response = self._session.request(method, url, params=params, timeout=TIMEOUT)
        except requests.exceptions.RequestException as exc:
            raise ThreadsAPIError(
                f"Falha de conexão com a API do Threads: {_redact(str(exc))}"
            ) from exc

        if response.status_code >= 400:
            message = response.text
            try:
                message = response.json().get("error", {}).get("message", message)
            except ValueError:
                pass
            raise ThreadsAPIError(
                f"Erro da API do Threads ({response.status_code}): {_redact(message)}"
            )

        return response.json()

    def search_keyword(self, query: str, limit: int = 25) -> list[dict]:
        """Search recent public Threads posts matching `query`.

        Requires the restricted `threads_keyword_search` permission.
        """
        data = self._request(
            "GET",
            "keyword_search",
            {
                "q": query,
                "search_type": "RECENT",
                "fields": "id,text,username,permalink,timestamp",
                "limit": limit,
            },
        )
        return data.get("data", [])

    def _wait_until_container_ready(self, container_id: str) -> None:
        """Poll a media container until Meta finishes processing it.

        Publishing a container that isn't FINISHED yet is a common source of
        failures, so this blocks (with a bounded wait) instead of publishing
        immediately after creation.
        """
        waited = 0
        while waited < CONTAINER_MAX_WAIT:
            data = self._request("GET", container_id, {"fields": "status_code"})
            status = data.get("status_code")
            if status == "FINISHED":
                return
            if status == "ERROR":
                raise ThreadsAPIError(
                    "O Threads não conseguiu processar o post (status_code=ERROR)."
                )
            self._sleep(CONTAINER_POLL_INTERVAL)
            waited += CONTAINER_POLL_INTERVAL

        raise ThreadsAPIError(
            "Tempo esgotado esperando o Threads processar o post antes de publicar."
        )

    def publish_reply(self, reply_to_id: str, text: str) -> str:
        """Publish `text` as a reply to `reply_to_id`. Returns the new post id.

        Threads publishing is a two-step process: create a media container,
        wait for it to finish processing, then publish it.
        """
        container = self._request(
            "POST",
            f"{self.user_id}/threads",
            {"media_type": "TEXT", "text": text, "reply_to_id": reply_to_id},
        )
        self._wait_until_container_ready(container["id"])
        published = self._request(
            "POST",
            f"{self.user_id}/threads_publish",
            {"creation_id": container["id"]},
        )
        return published["id"]
