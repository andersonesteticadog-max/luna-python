import httpx

from luna.config import CRM_URL, CRM_BEARER

_headers = {"Authorization": f"Bearer {CRM_BEARER}"}


def listar_servicos():
    resposta = httpx.get(f"{CRM_URL}/servicos", headers=_headers, timeout=10)
    resposta.raise_for_status()
    return resposta.json()


def consultar_agenda(data, duracao_min=60):
    resposta = httpx.get(
        f"{CRM_URL}/agenda",
        params={"data": data, "duracao_min": duracao_min},
        headers=_headers,
        timeout=10,
    )
    resposta.raise_for_status()
    return resposta.json()


TOOL_FUNCTIONS = {
    "listar_servicos": listar_servicos,
    "consultar_agenda": consultar_agenda,
}
