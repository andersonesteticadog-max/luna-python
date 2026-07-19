import re


def dividir_em_frases(texto):
    """Quebra a resposta da Luna em frases, pra mandar como varias mensagens
    sequenciais no WhatsApp (mais natural que um bloco so de texto) -
    mesma ideia do no de split que ja existia no n8n."""
    frases = re.split(r"(?<=[.!?])\s+", texto.strip())
    return [f for f in frases if f]


def enviar_mensagem(numero, texto):
    """FAKE por enquanto: so imprime o que seria enviado. Quando tivermos uma
    instancia real da Evolution API, isso vira uma chamada httpx pra
    POST {EVOLUTION_URL}/message/sendText/{instance} (com o numero e cada
    frase no corpo, uma chamada por frase)."""
    for frase in dividir_em_frases(texto):
        print(f"[WhatsApp -> {numero}]: {frase}")
