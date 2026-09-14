"""Generate Threads posts and comment replies using the prompt templates."""

from .client import ClaudeClient, LLMClient
from .config import AccountConfig
from .prompts import SYSTEM_PROMPT_POST, SYSTEM_PROMPT_REPLY, render

POST_CHAR_LIMIT = 500
REPLY_CHAR_LIMIT = 280


def generate_post(account: AccountConfig, topic: str, client: LLMClient | None = None) -> str:
    """Generate an original Threads post about `topic` for the given account."""
    client = client or ClaudeClient()
    system_prompt = render(
        SYSTEM_PROMPT_POST,
        NICHO=account.nicho,
        TOM=account.tom,
        PUBLICO=account.publico,
    )
    post = client.complete(system_prompt, topic)
    return post[:POST_CHAR_LIMIT]


def generate_reply(
    account: AccountConfig, comment: str, client: LLMClient | None = None
) -> str | None:
    """Generate a reply to `comment`, or None if the comment should be skipped."""
    client = client or ClaudeClient()
    system_prompt = render(
        SYSTEM_PROMPT_REPLY,
        NOME_DA_CONTA=account.nome_da_conta,
        NICHO=account.nicho,
        TOM=account.tom,
    )
    reply = client.complete(system_prompt, comment)
    if reply.strip() == "SKIP":
        return None
    return reply[:REPLY_CHAR_LIMIT]
