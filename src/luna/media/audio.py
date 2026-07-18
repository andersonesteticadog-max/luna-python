import httpx

from luna.config import GROQ_API_KEY


def transcrever(caminho_arquivo):
    with open(caminho_arquivo, "rb") as f:
        resposta = httpx.post(
            "https://api.groq.com/openai/v1/audio/transcriptions",
            headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
            files={"file": f},
            data={"model": "whisper-large-v3", "language": "pt"},
            timeout=60,
        )
    resposta.raise_for_status()
    return resposta.json()["text"]
