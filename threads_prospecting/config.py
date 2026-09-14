"""Account context used to fill in the prompt templates."""

from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass
class AccountConfig:
    nicho: str
    tom: str
    publico: str
    nome_da_conta: str


def load_account_config(path: str | Path) -> AccountConfig:
    """Load an :class:`AccountConfig` from a YAML file.

    Expected shape:

        nicho: "..."
        tom: "..."
        publico: "..."
        nome_da_conta: "..."
    """
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}

    required = ("nicho", "tom", "publico", "nome_da_conta")
    missing = [key for key in required if not data.get(key)]
    if missing:
        raise ValueError(f"Missing required fields in {path}: {', '.join(missing)}")

    return AccountConfig(
        nicho=data["nicho"],
        tom=data["tom"],
        publico=data["publico"],
        nome_da_conta=data["nome_da_conta"],
    )
