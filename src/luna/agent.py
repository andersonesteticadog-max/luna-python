import anthropic

from luna.config import ANTHROPIC_API_KEY

MODEL = "claude-haiku-4-5-20251001"
MAX_PASSOS = 5

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


def executar_turno(mensagens, tools_schema, tool_functions, system):
    """Manda a conversa pro Claude. Enquanto ele pedir pra usar uma
    ferramenta, executa a funcao Python correspondente e manda o resultado
    de volta, ate ele decidir responder em texto (ou estourar MAX_PASSOS)."""
    for _ in range(MAX_PASSOS):
        try:
            resposta = client.messages.create(
                model=MODEL,
                max_tokens=1024,
                system=system,
                messages=mensagens,
                tools=tools_schema,
            )
        except anthropic.APIError as e:
            return f"[erro ao falar com a IA: {e}]"

        if resposta.stop_reason != "tool_use":
            return "".join(b.text for b in resposta.content if b.type == "text")

        # .model_dump() converte os objetos do SDK (TextBlock, ToolUseBlock)
        # em dict puro. Sem isso, "mensagens" fica com objetos que ate
        # funcionam aqui dentro, mas quebram na hora de salvar em JSON.
        mensagens.append({
            "role": "assistant",
            "content": [bloco.model_dump() for bloco in resposta.content],
        })

        resultados = []
        for bloco in resposta.content:
            if bloco.type != "tool_use":
                continue
            resultados.append({
                "type": "tool_result",
                "tool_use_id": bloco.id,
                "content": str(_chamar_ferramenta(bloco, tool_functions)),
            })
        mensagens.append({"role": "user", "content": resultados})

    return "[a IA nao concluiu apos varias chamadas de ferramenta seguidas]"


def _chamar_ferramenta(bloco, tool_functions):
    funcao = tool_functions.get(bloco.name)
    if funcao is None:
        return f"erro: ferramenta '{bloco.name}' nao existe"
    try:
        return funcao(**bloco.input)
    except Exception as e:
        return f"erro ao executar '{bloco.name}': {e}"
