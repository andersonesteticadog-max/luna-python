import base64
import sys
import time
import uuid

import httpx

sys.stdout.reconfigure(encoding="utf-8")

WEBHOOK_URL = "http://127.0.0.1:8096/webhook"
NUMERO_TESTE = "5511999999999"


def _base_data(from_me=False, grupo=False):
    remote = f"{NUMERO_TESTE}@{'g.us' if grupo else 's.whatsapp.net'}"
    return {
        "key": {"remoteJid": remote, "fromMe": from_me, "id": uuid.uuid4().hex},
        "pushName": "Cliente Teste",
        "messageTimestamp": int(time.time()),
    }


def payload_texto(texto):
    data = _base_data()
    data["messageType"] = "conversation"
    data["message"] = {"conversation": texto}
    return {"event": "messages.upsert", "instance": "luna-teste", "data": data}


def payload_audio(caminho):
    with open(caminho, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
    data = _base_data()
    data["messageType"] = "audioMessage"
    data["message"] = {"audioMessage": {}}
    data["base64"] = b64
    return {"event": "messages.upsert", "instance": "luna-teste", "data": data}


def payload_imagem(caminho, legenda=""):
    with open(caminho, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
    data = _base_data()
    data["messageType"] = "imageMessage"
    data["message"] = {"imageMessage": {"caption": legenda}}
    data["base64"] = b64
    return {"event": "messages.upsert", "instance": "luna-teste", "data": data}


def main():
    print("=== Simulador de webhook do WhatsApp === (Ctrl+C pra sair)")
    print("Manda payloads no formato da Evolution API pro whatsapp.py, que precisa")
    print("estar rodando em outro terminal. As respostas da Luna aparecem la, nao aqui.\n")
    print("Comandos: texto normal | /audio <caminho> | /imagem <caminho> [legenda]\n")

    while True:
        texto = input("Voce (simulando WhatsApp): ").strip()
        if not texto:
            continue

        if texto.startswith("/audio "):
            caminho = texto[len("/audio "):].strip()
            try:
                payload = payload_audio(caminho)
            except OSError as e:
                print(f"[erro ao ler o audio: {e}]\n")
                continue
        elif texto.startswith("/imagem "):
            resto = texto[len("/imagem "):].strip()
            caminho, _, legenda = resto.partition(" ")
            try:
                payload = payload_imagem(caminho, legenda.strip())
            except OSError as e:
                print(f"[erro ao ler a imagem: {e}]\n")
                continue
        else:
            payload = payload_texto(texto)

        resposta = httpx.post(WEBHOOK_URL, json=payload, timeout=60)
        print(f"[webhook respondeu {resposta.status_code} - veja a resposta da Luna no outro terminal]\n")


if __name__ == "__main__":
    main()
