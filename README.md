# threads-prospecting

Gera posts e respostas de comentários para o Threads usando a API da Claude,
a partir de um contexto de conta configurável (nicho, tom de voz e público-alvo).

## Setup

### Windows (mais fácil)

Dê dois cliques em `iniciar.bat`. Ele cria o ambiente virtual, instala as
dependências, cria `.env` e `account.yaml` a partir dos modelos (abrindo o
Bloco de Notas para você preencher na primeira execução) e mostra um menu
para gerar posts ou respostas sem precisar digitar comandos.

### Manual (Windows/macOS/Linux)

```bash
pip install -r requirements.txt
cp .env.example .env       # preencha ANTHROPIC_API_KEY
cp account.example.yaml account.yaml   # ajuste nicho/tom/publico/nome_da_conta
```

## Uso

Gerar um post sobre um tema:

```bash
python -m threads_prospecting.cli post --topic "reserva de emergência"
```

Gerar uma resposta a um comentário:

```bash
python -m threads_prospecting.cli reply --comment "Amei esse post!"
```

Se o comentário for hostil, ofensivo ou spam, o comando imprime `SKIP` em vez
de gerar uma resposta.

## Estrutura

- `threads_prospecting/prompts.py` — os dois templates de system prompt
  (geração de post e geração de resposta) com placeholders `{{NICHO}}`,
  `{{TOM}}`, `{{PUBLICO}}` e `{{NOME_DA_CONTA}}`.
- `threads_prospecting/config.py` — carrega o contexto da conta de um YAML.
- `threads_prospecting/client.py` — chamada à API da Claude.
- `threads_prospecting/generator.py` — `generate_post` e `generate_reply`,
  que preenchem os templates e aplicam os limites de caracteres do Threads.
- `threads_prospecting/cli.py` — interface de linha de comando.

## Testes

```bash
pip install pytest
pytest
```

Os testes usam um cliente falso (sem chamadas de rede) para validar o
preenchimento dos templates e o comportamento de `generate_post`/`generate_reply`.
