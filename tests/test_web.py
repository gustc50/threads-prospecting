import pytest

from threads_prospecting import web


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(web, "ACCOUNT_PATH", tmp_path / "account.yaml")
    monkeypatch.setattr(web, "ENV_PATH", tmp_path / ".env")
    web.app.config.update(TESTING=True)
    return web.app.test_client()


def test_index_serves_html(client):
    res = client.get("/")
    assert res.status_code == 200
    assert b"Threads Prospecting" in res.data


def test_get_config_defaults_when_no_files(client):
    res = client.get("/api/config")
    data = res.get_json()

    assert data["api_key_set"] is False
    assert data["account"] == {"nicho": "", "tom": "", "publico": "", "nome_da_conta": ""}


def test_save_config_rejects_missing_fields(client):
    res = client.post("/api/config", json={"account": {"nicho": "financas"}})

    assert res.status_code == 400
    assert "tom" in res.get_json()["error"]


def test_save_config_writes_files_and_masks_key_afterwards(client):
    res = client.post(
        "/api/config",
        json={
            "account": {
                "nicho": "financas pessoais",
                "tom": "descontraido",
                "publico": "freelancers",
                "nome_da_conta": "Financas Sem Enrolacao",
            },
            "api_key": "sk-test-fake",
        },
    )
    assert res.status_code == 200

    data = client.get("/api/config").get_json()
    assert data["api_key_set"] is True
    assert data["account"]["nicho"] == "financas pessoais"
    assert web.ENV_PATH.read_text() == "ANTHROPIC_API_KEY=sk-test-fake\n"


def test_api_post_requires_topic(client):
    res = client.post("/api/post", json={"topic": "  "})
    assert res.status_code == 400


def test_api_post_requires_account_config_first(client):
    res = client.post("/api/post", json={"topic": "reserva de emergencia"})
    assert res.status_code == 400
    assert "Configure a conta" in res.get_json()["error"]


def test_api_post_returns_generated_text(client, monkeypatch):
    web._write_account(
        {
            "nicho": "financas",
            "tom": "descontraido",
            "publico": "freelancers",
            "nome_da_conta": "Conta",
        }
    )
    monkeypatch.setattr(web, "generate_post", lambda account, topic: f"post sobre {topic}")

    res = client.post("/api/post", json={"topic": "reserva de emergencia"})

    assert res.status_code == 200
    assert res.get_json() == {"post": "post sobre reserva de emergencia"}


def test_api_reply_reports_skip(client, monkeypatch):
    web._write_account(
        {
            "nicho": "financas",
            "tom": "descontraido",
            "publico": "freelancers",
            "nome_da_conta": "Conta",
        }
    )
    monkeypatch.setattr(web, "generate_reply", lambda account, comment: None)

    res = client.post("/api/reply", json={"comment": "comentario ofensivo"})

    assert res.status_code == 200
    assert res.get_json() == {"reply": None, "skip": True}
