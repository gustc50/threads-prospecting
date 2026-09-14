# threads-prospecting

Gera posts e respostas de comentários para o Threads usando a API da Claude,
a partir de um contexto de conta configurável (nicho, tom de voz e público-alvo).
Tudo é feito por uma interface web local — sem editar arquivos na mão.

## Setup

### Windows (mais fácil)

Dê dois cliques em `iniciar.bat`. Ele cria o ambiente virtual, instala as
dependências e abre automaticamente `http://127.0.0.1:8765` no seu navegador
padrão. Configure a chave da API e a conta na aba **Configurações**; depois
use as abas **Gerar post** e **Gerar resposta**. Para encerrar, feche a
janela do terminal que abriu junto.

### Manual (Windows/macOS/Linux)

```bash
pip install -r requirements.txt
python -m threads_prospecting.web
```

Isso abre a mesma interface web em `http://127.0.0.1:8765`. A porta pode ser
trocada com a variável de ambiente `PORT`.

## Interface web

- **Configurações** — chave da API (`ANTHROPIC_API_KEY`), nicho/tema, tom de
  voz, público-alvo e nome da conta. Salva em `account.yaml` e `.env` no
  próprio diretório do projeto.
- **Gerar post** — informe um tema e receba um post pronto para colar no
  Threads (com botão de copiar).
- **Gerar resposta** — cole um comentário recebido e receba a resposta
  sugerida (ou um aviso de "SKIP" quando o comentário for hostil/spam).

## Linha de comando (opcional)

Quem preferir usar via terminal ainda pode, depois de configurar `account.yaml`
e `.env` (veja `account.example.yaml` e `.env.example`):

```bash
python -m threads_prospecting.cli post --topic "reserva de emergência"
python -m threads_prospecting.cli reply --comment "Amei esse post!"
```

## Estrutura

- `threads_prospecting/prompts.py` — os dois templates de system prompt
  (geração de post e geração de resposta) com placeholders `{{NICHO}}`,
  `{{TOM}}`, `{{PUBLICO}}` e `{{NOME_DA_CONTA}}`.
- `threads_prospecting/config.py` — carrega o contexto da conta de um YAML.
- `threads_prospecting/client.py` — chamada à API da Claude.
- `threads_prospecting/generator.py` — `generate_post` e `generate_reply`,
  que preenchem os templates e aplicam os limites de caracteres do Threads.
- `threads_prospecting/web.py` — servidor Flask local (interface web) que
  abre o navegador automaticamente.
- `threads_prospecting/templates/` e `threads_prospecting/static/` — HTML,
  CSS e JS da interface web.
- `threads_prospecting/cli.py` — interface de linha de comando (opcional).

## Testes

```bash
pip install pytest
pytest
```

Os testes usam um cliente falso (sem chamadas de rede) para validar o
preenchimento dos templates e o comportamento de `generate_post`/`generate_reply`.
