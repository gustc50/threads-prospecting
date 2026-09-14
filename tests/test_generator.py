from threads_prospecting.config import AccountConfig
from threads_prospecting.generator import (
    POST_CHAR_LIMIT,
    REPLY_CHAR_LIMIT,
    generate_post,
    generate_reply,
)


class FakeClient:
    def __init__(self, response: str):
        self.response = response
        self.last_call = None

    def complete(self, system_prompt: str, user_message: str) -> str:
        self.last_call = (system_prompt, user_message)
        return self.response


ACCOUNT = AccountConfig(
    nicho="finanças pessoais",
    tom="descontraído",
    publico="freelancers",
    nome_da_conta="Finanças Sem Enrolação",
)


def test_generate_post_returns_client_output():
    client = FakeClient("Ninguém te ensinou a guardar dinheiro? Nem eu, até quebrar a cara.")
    post = generate_post(ACCOUNT, "reserva de emergência", client=client)

    assert post == client.response
    system_prompt, user_message = client.last_call
    assert "finanças pessoais" in system_prompt
    assert user_message == "reserva de emergência"


def test_generate_post_is_truncated_to_char_limit():
    client = FakeClient("x" * (POST_CHAR_LIMIT + 50))
    post = generate_post(ACCOUNT, "topico", client=client)
    assert len(post) == POST_CHAR_LIMIT


def test_generate_reply_returns_none_on_skip():
    client = FakeClient("SKIP")
    assert generate_reply(ACCOUNT, "comentário ofensivo", client=client) is None


def test_generate_reply_returns_text_and_uses_account_name():
    client = FakeClient("Valeu demais pelo carinho!")
    reply = generate_reply(ACCOUNT, "Amei esse post!", client=client)

    assert reply == client.response
    system_prompt, user_message = client.last_call
    assert "Finanças Sem Enrolação" in system_prompt
    assert user_message == "Amei esse post!"


def test_generate_reply_is_truncated_to_char_limit():
    client = FakeClient("y" * (REPLY_CHAR_LIMIT + 50))
    reply = generate_reply(ACCOUNT, "comentário", client=client)
    assert len(reply) == REPLY_CHAR_LIMIT
