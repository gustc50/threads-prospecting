"""Bridges the Claude generator and the Threads API: search for candidate
posts by keyword, let the LLM decide whether/what to reply, and optionally
publish that reply for real.
"""

from __future__ import annotations

from .client import LLMClient
from .config import AccountConfig
from .generator import generate_prospect_reply
from .threads_client import ThreadsClient


def find_leads(
    threads: ThreadsClient,
    account: AccountConfig,
    keywords: list[str],
    llm_client: LLMClient | None = None,
    limit_per_keyword: int = 10,
) -> list[dict]:
    """Search `keywords` on Threads and have the LLM draft a reply for each
    post found. Nothing is published here — see `publish_lead_reply`."""
    seen_ids: set[str] = set()
    leads: list[dict] = []

    for keyword in keywords:
        for post in threads.search_keyword(keyword, limit=limit_per_keyword):
            post_id = post.get("id")
            if not post_id or post_id in seen_ids:
                continue
            seen_ids.add(post_id)

            reply = generate_prospect_reply(account, post.get("text", ""), client=llm_client)
            leads.append({"post": post, "reply": reply, "skip": reply is None})

    return leads


def publish_lead_reply(threads: ThreadsClient, post_id: str, text: str) -> str:
    """Publish `text` as a reply to `post_id`. Returns the new post's id."""
    return threads.publish_reply(post_id, text)


def run_prospecting(
    threads: ThreadsClient,
    account: AccountConfig,
    keywords: list[str],
    llm_client: LLMClient | None = None,
    limit_per_keyword: int = 10,
) -> list[dict]:
    """Full pipeline, fully automatic: search, generate, and publish.

    Every non-skipped lead has its reply published immediately, with no
    human review in between. Prefer `find_leads` + `publish_lead_reply`
    when you want a review step first.
    """
    leads = find_leads(
        threads, account, keywords, llm_client=llm_client, limit_per_keyword=limit_per_keyword
    )
    for lead in leads:
        if lead["skip"]:
            continue
        lead["published_id"] = publish_lead_reply(threads, lead["post"]["id"], lead["reply"])
    return leads
