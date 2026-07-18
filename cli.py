import sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, "src")

from luna.agent import executar_turno
from luna.tools.schemas import TOOLS_SCHEMA
from luna.tools.crm import TOOL_FUNCTIONS

SYSTEM = (
    "Voce e um assistente de pet shop. Use as ferramentas disponiveis quando precisar "
    "de informacao do CRM. Se o cliente informar um telefone, use consultar_cliente pra "
    "ver se ele ja e cliente antigo antes de perguntar dados que talvez ja estejam no CRM. "
    "Antes de chamar a ferramenta 'agendar', sempre mostre um resumo (servico, pet, "
    "data/hora, tutor, telefone) e espere o cliente confirmar explicitamente que esta "
    "certo - nunca chame 'agendar' sem essa confirmacao."
)


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
