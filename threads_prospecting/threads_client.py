"""Thin wrapper around Meta's Threads API (graph.threads.net).

Docs: https://developers.facebook.com/docs/threads

Using this requires a Meta developer app with Threads API access, and a
user access token with (at least) the `threads_basic`,
`threads_content_publish` and `threads_keyword_search` permissions —
keyword search in particular is a restricted permission that Meta has to
approve for your app. Field/param names here follow the API as of this
writing; check Meta's docs if a call starts failing after a platform update.
"""

from __future__ import annotations

import re
from typing import Any

import requests

GRAPH_BASE = "https://graph.threads.net/v1.0"
TIMEOUT = 20

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
    ):
        if not access_token:
            raise ThreadsAPIError(
                "Token de acesso do Threads não configurado (aba Prospecção)."
            )
        self.access_token = access_token
        self.user_id = user_id or "me"
        self._session = session or requests.Session()

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

    def publish_reply(self, reply_to_id: str, text: str) -> str:
        """Publish `text` as a reply to `reply_to_id`. Returns the new post id.

        Threads publishing is a two-step process: create a media container,
        then publish it.
        """
        container = self._request(
            "POST",
            f"{self.user_id}/threads",
            {"media_type": "TEXT", "text": text, "reply_to_id": reply_to_id},
        )
        published = self._request(
            "POST",
            f"{self.user_id}/threads_publish",
            {"creation_id": container["id"]},
        )
        return published["id"]
