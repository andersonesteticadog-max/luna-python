import sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, "src")

from luna.agent import executar_turno
from luna.media.audio import transcrever
from luna.media.image import preparar_imagem
from luna.memory import carregar, salvar
from luna.prompt import carregar_system_prompt
from luna.tools.schemas import TOOLS_SCHEMA
from luna.tools.crm import TOOL_FUNCTIONS

SYSTEM = carregar_system_prompt()
CONTATO_TESTE = "cli-teste"


def main():
    mensagens = carregar(CONTATO_TESTE)
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
        # /audio <caminho> - so pra testar sem WhatsApp de verdade ainda
        # (Fase 5). No sistema real, isso vira automatico: audio chega no
        # webhook, e' transcrito, e so o texto resultante chega na Luna -
        # ela nunca "ouve" o audio, so le o texto.
        elif texto.startswith("/audio "):
            caminho = texto[len("/audio "):].strip()
            try:
                texto_transcrito = transcrever(caminho)
            except OSError as e:
                print(f"[erro ao ler o audio: {e}]\n")
                continue
            print(f"(audio transcrito: \"{texto_transcrito}\")")
            conteudo = texto_transcrito
        else:
            conteudo = texto

        mensagens.append({"role": "user", "content": conteudo})
        resposta = executar_turno(mensagens, TOOLS_SCHEMA, TOOL_FUNCTIONS, SYSTEM)
        mensagens.append({"role": "assistant", "content": resposta})
        salvar(CONTATO_TESTE, mensagens)
        print(f"Luna: {resposta}\n")


if __name__ == "__main__":
    main()
