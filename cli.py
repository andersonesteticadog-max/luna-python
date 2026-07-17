import sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, "src")

from luna.agent import executar_turno

SYSTEM = "Voce e um assistente de pet shop. Use a ferramenta disponivel quando precisar saber horarios livres."

# FAKE - so pra testar o mecanismo de tool-use. Na Fase 2 isso vira uma
# chamada http de verdade pro mini-CRM (src/luna/tools/crm.py).
TOOLS_SCHEMA = [
    {
        "name": "consultar_horarios_livres",
        "description": "Consulta os horarios livres do pet shop numa data. Retorna uma lista de horarios no formato HH:MM.",
        "input_schema": {
            "type": "object",
            "properties": {
                "data": {"type": "string", "description": "Data no formato AAAA-MM-DD"},
            },
            "required": ["data"],
        },
    },
]


def consultar_horarios_livres(data):
    print(f"    [ferramenta chamada: consultar_horarios_livres(data={data!r})]")
    return ["09:00", "10:30", "14:00"]


TOOL_FUNCTIONS = {"consultar_horarios_livres": consultar_horarios_livres}


def main():
    mensagens = []
    print("=== Luna (modo teste) === (Ctrl+C pra sair)\n")
    while True:
        texto = input("Voce: ").strip()
        if not texto:
            continue
        mensagens.append({"role": "user", "content": texto})
        resposta = executar_turno(mensagens, TOOLS_SCHEMA, TOOL_FUNCTIONS, SYSTEM)
        mensagens.append({"role": "assistant", "content": resposta})
        print(f"Luna: {resposta}\n")


if __name__ == "__main__":
    main()
