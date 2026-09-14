import pytest
import requests

from threads_prospecting.threads_client import ThreadsAPIError, ThreadsClient


class FakeResponse:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload
        self.text = str(payload)

    def json(self):
        return self._payload


class FakeSession:
    def __init__(self, responses):
        self.responses = responses
        self.calls = []

    def request(self, method, url, params=None, timeout=None):
        self.calls.append((method, url, params))
        return self.responses.pop(0)


def test_missing_token_raises_clean_error():
    with pytest.raises(ThreadsAPIError):
        ThreadsClient(access_token="")


def test_search_keyword_returns_posts():
    session = FakeSession(
        [FakeResponse(200, {"data": [{"id": "1", "text": "preciso de um contador"}]})]
    )
    client = ThreadsClient(access_token="tok", session=session)

    posts = client.search_keyword("contador")

    assert posts == [{"id": "1", "text": "preciso de um contador"}]
    method, url, params = session.calls[0]
    assert method == "GET"
    assert url.endswith("/keyword_search")
    assert params["q"] == "contador"
    assert params["access_token"] == "tok"


def test_publish_reply_two_step_flow():
    session = FakeSession(
        [
            FakeResponse(200, {"id": "container-1"}),
            FakeResponse(200, {"id": "published-1"}),
        ]
    )
    client = ThreadsClient(access_token="tok", user_id="123", session=session)

    published_id = client.publish_reply("post-1", "Posso ajudar com isso!")

    assert published_id == "published-1"
    assert len(session.calls) == 2
    first_method, first_url, first_params = session.calls[0]
    assert first_url.endswith("/123/threads")
    assert first_params["reply_to_id"] == "post-1"
    second_method, second_url, second_params = session.calls[1]
    assert second_url.endswith("/123/threads_publish")
    assert second_params["creation_id"] == "container-1"


def test_error_response_raises_with_message():
    session = FakeSession([FakeResponse(400, {"error": {"message": "token inválido"}})])
    client = ThreadsClient(access_token="tok", session=session)

    with pytest.raises(ThreadsAPIError, match="token inválido"):
        client.search_keyword("qualquer coisa")


def test_connection_failure_raises_clean_error_not_a_traceback():
    class BrokenSession:
        def request(self, method, url, params=None, timeout=None):
            raise requests.exceptions.ConnectionError("boom")

    client = ThreadsClient(access_token="tok", session=BrokenSession())

    with pytest.raises(ThreadsAPIError, match="Falha de conexão"):
        client.search_keyword("contador")


def test_connection_failure_does_not_leak_access_token():
    class BrokenSession:
        def request(self, method, url, params=None, timeout=None):
            raise requests.exceptions.ConnectionError(
                f"boom while calling {url}?access_token=super-secret-token"
            )

    client = ThreadsClient(access_token="super-secret-token", session=BrokenSession())

    with pytest.raises(ThreadsAPIError) as exc_info:
        client.search_keyword("contador")

    assert "super-secret-token" not in str(exc_info.value)
