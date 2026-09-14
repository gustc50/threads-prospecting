from threads_prospecting.config import AccountConfig
from threads_prospecting.prospecting import find_leads, publish_lead_reply, run_prospecting

ACCOUNT = AccountConfig(
    nicho="contabilidade para autônomos",
    tom="descontraído",
    publico="freelancers",
    nome_da_conta="Finanças Sem Enrolação",
)


class FakeLLMClient:
    """Returns SKIP for posts containing 'spam', otherwise a canned reply."""

    def complete(self, system_prompt, user_message):
        if "spam" in user_message:
            return "SKIP"
        return f"Posso te ajudar com isso! Me chama."


class FakeThreadsClient:
    def __init__(self, posts_by_keyword):
        self.posts_by_keyword = posts_by_keyword
        self.published = []

    def search_keyword(self, query, limit=25):
        return self.posts_by_keyword.get(query, [])

    def publish_reply(self, reply_to_id, text):
        self.published.append((reply_to_id, text))
        return f"published-{reply_to_id}"


def test_find_leads_marks_skip_and_dedupes_across_keywords():
    threads = FakeThreadsClient(
        {
            "contador": [
                {"id": "1", "text": "preciso de um contador urgente"},
                {"id": "2", "text": "isso aqui é spam"},
            ],
            "abrir empresa": [
                {"id": "1", "text": "preciso de um contador urgente"},  # duplicate id
                {"id": "3", "text": "como faço para abrir empresa?"},
            ],
        }
    )

    leads = find_leads(threads, ACCOUNT, ["contador", "abrir empresa"], llm_client=FakeLLMClient())

    assert [lead["post"]["id"] for lead in leads] == ["1", "2", "3"]
    assert leads[0]["skip"] is False
    assert leads[1]["skip"] is True
    assert leads[1]["reply"] is None
    assert threads.published == []


def test_publish_lead_reply_delegates_to_client():
    threads = FakeThreadsClient({})
    published_id = publish_lead_reply(threads, "post-1", "resposta")

    assert published_id == "published-post-1"
    assert threads.published == [("post-1", "resposta")]


def test_run_prospecting_publishes_non_skipped_leads():
    threads = FakeThreadsClient(
        {
            "contador": [
                {"id": "1", "text": "preciso de um contador urgente"},
                {"id": "2", "text": "isso aqui é spam"},
            ]
        }
    )

    leads = run_prospecting(threads, ACCOUNT, ["contador"], llm_client=FakeLLMClient())

    assert leads[0]["published_id"] == "published-1"
    assert "published_id" not in leads[1]
    assert threads.published == [("1", "Posso te ajudar com isso! Me chama.")]
