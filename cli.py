import sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, "src")

from luna.agent import executar_turno
from luna.media.image import preparar_imagem
from luna.memory import carregar, salvar
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
    mensagens = carregar()
    print("=== Luna (modo teste) === (Ctrl+C pra sair)")
    if mensagens:
        print(f"(retomando conversa anterior, {len(mensagens)} mensagens)")
    print()
    while True:
        texto = input("Voce: ").strip()
        if not texto:
            continue

        # /imagem <caminho> [pergunta] - so pra testar sem WhatsApp de verdade
        # ainda (Fase 5). No sistema real, isso vira automatico: o tipo de
        # mensagem chega pronto no webhook.
        if texto.startswith("/imagem "):
            resto = texto[len("/imagem "):].strip()
            caminho, _, pergunta = resto.partition(" ")
            pergunta = pergunta.strip() or "Descreva o que voce ve nessa imagem."
            try:
                bloco_imagem = preparar_imagem(caminho)
            except OSError as e:
                print(f"[erro ao ler a imagem: {e}]\n")
                continue
            conteudo = [bloco_imagem, {"type": "text", "text": pergunta}]
        else:
            conteudo = texto

        mensagens.append({"role": "user", "content": conteudo})
        resposta = executar_turno(mensagens, TOOLS_SCHEMA, TOOL_FUNCTIONS, SYSTEM)
        mensagens.append({"role": "assistant", "content": resposta})
        salvar(mensagens)
        print(f"Luna: {resposta}\n")


if __name__ == "__main__":
    main()
