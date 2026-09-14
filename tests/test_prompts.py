import pytest

from threads_prospecting.prompts import SYSTEM_PROMPT_POST, SYSTEM_PROMPT_REPLY, render


def test_render_fills_all_placeholders():
    result = render(
        SYSTEM_PROMPT_POST,
        NICHO="finanças pessoais",
        TOM="descontraído",
        PUBLICO="freelancers",
    )
    assert "{{" not in result
    assert "finanças pessoais" in result
    assert "descontraído" in result
    assert "freelancers" in result


def test_render_missing_placeholder_raises():
    with pytest.raises(KeyError):
        render(SYSTEM_PROMPT_REPLY, NOME_DA_CONTA="Conta", NICHO="tema")
