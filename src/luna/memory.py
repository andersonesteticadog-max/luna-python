import json
import os

ARQUIVO = "conversa.json"


def carregar():
    if not os.path.exists(ARQUIVO):
        return []
    with open(ARQUIVO, "r", encoding="utf-8") as f:
        return json.load(f)


def salvar(mensagens):
    with open(ARQUIVO, "w", encoding="utf-8") as f:
        json.dump(mensagens, f, indent=2, ensure_ascii=False)
