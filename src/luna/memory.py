import json
import os

PASTA = "conversas"


def carregar(contato):
    caminho = os.path.join(PASTA, f"{contato}.json")
    if not os.path.exists(caminho):
        return []
    with open(caminho, "r", encoding="utf-8") as f:
        return json.load(f)


def salvar(contato, mensagens):
    os.makedirs(PASTA, exist_ok=True)
    caminho = os.path.join(PASTA, f"{contato}.json")
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(mensagens, f, indent=2, ensure_ascii=False)
