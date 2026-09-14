import pytest

from threads_prospecting.config import load_account_config


def test_load_account_config(tmp_path):
    config_path = tmp_path / "account.yaml"
    config_path.write_text(
        """
        nicho: "finanças pessoais"
        tom: "descontraído"
        publico: "freelancers"
        nome_da_conta: "Finanças Sem Enrolação"
        """
    )

    account = load_account_config(config_path)

    assert account.nicho == "finanças pessoais"
    assert account.tom == "descontraído"
    assert account.publico == "freelancers"
    assert account.nome_da_conta == "Finanças Sem Enrolação"


def test_load_account_config_missing_field_raises(tmp_path):
    config_path = tmp_path / "account.yaml"
    config_path.write_text('nicho: "finanças pessoais"\n')

    with pytest.raises(ValueError):
        load_account_config(config_path)
