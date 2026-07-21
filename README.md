# Luna

Agente de IA para WhatsApp de um pet shop, reconstruído do zero em Python
puro a partir de um workflow em produção no n8n. O objetivo não foi só
replicar o comportamento, mas reconstruir cada peça entendendo o que
estava por baixo do no-code: loop de tool-use escrito à mão, integração
HTTP própria, banco de dados, memória de conversa e pré-processamento de
mídia.

Luna atende clientes de um pet shop pelo WhatsApp: informa preços,
consulta horários livres, agenda e cancela serviços, reconhece clientes
antigos e entende texto, áudio e imagem.

## Arquitetura

Nenhum framework de agente (LangChain, CrewAI, etc.) — o loop de tool-use
é escrito à mão sobre a API oficial da Anthropic, pra deixar explícito o
que normalmente fica escondido: mandar a conversa pro modelo, checar se
ele pediu uma ferramenta, executar a função Python correspondente,
devolver o resultado, repetir até ele responder em texto.

```
WhatsApp (Evolution API)
        │  webhook (messages.upsert)
        ▼
  whatsapp.py ──► filtra grupo/próprio número, dedup por id
        │
        ├─► audio/imagem → src/luna/media/  (transcrição / visão nativa)
        │
        ▼
  src/luna/agent.py  (loop de tool-use)
        │
        ├─► src/luna/tools/  ──HTTP──►  mini_crm.py  (CRM próprio, SQLite)
        │
        ▼
  resposta dividida em frases → "enviada" de volta ao cliente
```

O CRM de produção real só é acessível de dentro da rede interna do
servidor onde a Luna roda de verdade — por isso este projeto inclui um
**mini-CRM local** (`mini_crm.py`), um serviço HTTP próprio com SQLite que
imita a forma do CRM real. A Luna conversa com ele por `httpx`, nunca toca
o banco diretamente — mesma separação agente/API que existe em produção.

A integração com o WhatsApp roda contra um **webhook simulado**
(`simular_whatsapp.py` no lugar do WhatsApp de verdade): o formato do
payload segue o padrão documentado da Evolution API, mas o envio de
mensagens ainda é *fake* (só imprime no terminal) até haver uma instância
real conectada.

## O que a Luna faz

- Consulta os serviços e preços do pet shop
- Consulta horários livres numa data (considerando a duração de cada serviço)
- Reconhece clientes antigos pelo telefone (nome, pets, últimos agendamentos)
- Agenda um serviço — sempre mostrando um resumo e esperando confirmação
  explícita antes de gravar
- Cancela um agendamento existente (mesma regra de confirmação); remarcar é
  simplesmente cancelar o antigo e agendar de novo, sem ferramenta separada
- Entende áudio (transcrito via Groq Whisper) e imagem (visão nativa da
  Claude) além de texto puro
- Lembra da conversa entre mensagens (por contato) e divide respostas longas
  em várias mensagens sequenciais, como no WhatsApp real

## Estrutura

```
cli.py                 # testa o agente no terminal, sem WhatsApp
mini_crm.py             # sobe o CRM local (SQLite)
whatsapp.py              # sobe o webhook que recebe mensagens
simular_whatsapp.py      # simula o WhatsApp mandando payloads pro webhook
prompts/system_prompt.md # personalidade e regras da Luna
src/luna/
├── agent.py             # loop de tool-use
├── memory.py             # memória de conversa por contato
├── config.py              # variáveis de ambiente
├── tools/                 # ferramentas do agente + schemas pra API da Anthropic
├── media/                 # transcrição de áudio e leitura de imagem
├── mini_crm/               # CRM local (SQLite + http.server)
└── whatsapp/                # webhook + cliente da Evolution API
```

## Como rodar

Requer Python 3, uma chave da Anthropic e uma chave da Groq (transcrição
de áudio).

```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env   # preencha ANTHROPIC_API_KEY, GROQ_API_KEY, CRM_BEARER
```

**Testar só o agente**, sem CRM nem WhatsApp:
```
python cli.py
```

**Testar o fluxo completo** (precisa de dois terminais):
```
python mini_crm.py     # terminal 1 - CRM local
python whatsapp.py     # terminal 2 - webhook
python simular_whatsapp.py   # terminal 3 - simula mensagens chegando
```

## Autor

Anderson
