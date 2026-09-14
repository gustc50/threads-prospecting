# threads-prospecting

Gera posts e respostas de comentários para o Threads usando a API da Claude,
e faz prospecção ativa: busca posts públicos por palavra-chave, deixa a LLM
decidir se vale a pena responder e o que dizer, e publica a resposta de
verdade via API oficial do Threads. Tudo por uma interface web local — sem
editar arquivos na mão.

## Setup

### Windows (mais fácil)

Dê dois cliques em `iniciar.bat`. Ele cria o ambiente virtual, instala as
dependências e abre automaticamente `http://127.0.0.1:8765` no seu navegador
padrão. Configure tudo pela interface (abas **Configurações** e
**Prospecção**). Para encerrar, feche a janela do terminal que abriu junto.

### Manual (Windows/macOS/Linux)

```bash
pip install -r requirements.txt
python -m threads_prospecting.web
```

Isso abre a mesma interface web em `http://127.0.0.1:8765`. A porta pode ser
trocada com a variável de ambiente `PORT`.

## Interface web

- **Configurações** — chave da API da Claude (`ANTHROPIC_API_KEY`), nicho/tema,
  tom de voz, público-alvo e nome da conta. Salva em `account.yaml` e `.env`.
- **Gerar post** — informe um tema e receba um post pronto para colar no
  Threads (com botão de copiar).
- **Gerar resposta** — cole um comentário recebido na sua conta e receba a
  resposta sugerida (ou um aviso de "SKIP" quando o comentário for hostil/spam).
- **Prospecção** — a parte "ponte entre a LLM e o Threads":
  1. Salve o token de acesso e o ID de conta do Threads.
  2. Informe palavras-chave (ex: "preciso de contador, abrir empresa") e
     clique em **Buscar leads**. O sistema busca posts públicos recentes com
     essas palavras via `keyword_search` da API do Threads.
  3. Para cada post encontrado, a LLM decide se é um lead relevante (ou
     retorna "SKIP") e escreve uma resposta usando o contexto da conta.
  4. Por padrão os resultados ficam para revisão: edite o texto se quiser e
     clique em **Publicar resposta** post a post. Marque a caixa
     **"Publicar automaticamente, sem revisar antes"** para o modo 100%
     autônomo, em que a própria LLM decide e publica tudo sem parar para
     aprovação humana.

### Pré-requisitos para a aba Prospecção

A busca e a publicação usam a API oficial do Threads (`graph.threads.net`),
que exige:

- Um app registrado no [Meta for Developers](https://developers.facebook.com/docs/threads)
  com acesso à Threads API.
- Um token de acesso de usuário com as permissões `threads_basic`
  (obrigatória para qualquer chamada), `threads_manage_replies` (para
  publicar respostas) e a permissão **restrita** `threads_keyword_search`
  (para buscar por palavra-chave) — essa última precisa ser aprovada pela
  Meta caso a caso, não vem liberada por padrão.

Publicar uma resposta demora alguns segundos: a Meta processa o post
assincronamente antes de deixar publicar, então o botão "Publicar" (ou a
busca com o modo automático ligado) fica aguardando até ~60s por resposta
antes de dar erro de timeout.

**Atenção:** publicar respostas automaticamente em posts de estranhos, em
volume, pode ser interpretado pela Meta como comportamento automatizado/spam
e violar os termos da plataforma, além do risco de a própria conta ser
suspensa. Use o modo de revisão manual (padrão) enquanto valida o tom das
respostas, e ative o modo 100% automático com moderação.

## Linha de comando (opcional)

Quem preferir usar via terminal ainda pode, depois de configurar `account.yaml`
e `.env` (veja `account.example.yaml` e `.env.example`):

```bash
python -m threads_prospecting.cli post --topic "reserva de emergência"
python -m threads_prospecting.cli reply --comment "Amei esse post!"
```

A prospecção (busca + publicação) só está disponível pela interface web por
enquanto.

## Estrutura

- `threads_prospecting/prompts.py` — os três templates de system prompt
  (post, resposta a comentário próprio e resposta de prospecção) com
  placeholders `{{NICHO}}`, `{{TOM}}`, `{{PUBLICO}}` e `{{NOME_DA_CONTA}}`.
- `threads_prospecting/config.py` — carrega o contexto da conta de um YAML.
- `threads_prospecting/client.py` — chamada à API da Claude.
- `threads_prospecting/generator.py` — `generate_post`, `generate_reply` e
  `generate_prospect_reply`, que preenchem os templates e aplicam os limites
  de caracteres do Threads.
- `threads_prospecting/threads_client.py` — cliente da API oficial do
  Threads (`graph.threads.net`): busca por palavra-chave e publicação de
  respostas.
- `threads_prospecting/prospecting.py` — a ponte entre a LLM e o Threads:
  busca leads, gera as respostas e (opcionalmente) publica automaticamente.
- `threads_prospecting/web.py` — servidor Flask local (interface web) que
  abre o navegador automaticamente.
- `threads_prospecting/templates/` e `threads_prospecting/static/` — HTML,
  CSS e JS da interface web.
- `threads_prospecting/cli.py` — interface de linha de comando (post/reply).

## Testes

```bash
pip install pytest
pytest
```

Os testes usam um cliente de LLM falso e uma sessão HTTP falsa (sem chamadas
de rede reais) para validar templates, geração de post/resposta, o cliente
do Threads e o pipeline de prospecção.
