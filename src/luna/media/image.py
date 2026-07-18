import base64
import mimetypes


def preparar_imagem(caminho_arquivo):
    """Le uma imagem do disco e devolve ela no formato de 'content block' que
    a API da Anthropic entende - a Claude ve a imagem direto, sem precisar
    de nenhum servico externo descrevendo ela antes."""
    tipo, _ = mimetypes.guess_type(caminho_arquivo)
    if tipo is None:
        tipo = "image/jpeg"
    with open(caminho_arquivo, "rb") as f:
        dados = base64.standard_b64encode(f.read()).decode("utf-8")
    return {
        "type": "image",
        "source": {"type": "base64", "media_type": tipo, "data": dados},
    }
