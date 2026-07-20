import httpx

from luna.config import CRM_URL, CRM_BEARER

_headers = {"Authorization": f"Bearer {CRM_BEARER}"}


def listar_servicos():
    resposta = httpx.get(f"{CRM_URL}/servicos", headers=_headers, timeout=10)
    resposta.raise_for_status()
    return resposta.json()


def consultar_cliente(telefone):
    resposta = httpx.get(
        f"{CRM_URL}/cliente", params={"telefone": telefone}, headers=_headers, timeout=10,
    )
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


def agendar(cliente_nome, cliente_telefone, pet_nome, servico_nome, data_hora, pet_porte=None):
    # Sem raise_for_status: um 400 aqui e um erro de negocio esperado
    # (telefone invalido, servico ambiguo, data no passado) que o agente
    # precisa LER e reagir, nao uma falha pra estourar excecao.
    resposta = httpx.post(
        f"{CRM_URL}/agendar",
        json={
            "cliente_nome": cliente_nome,
            "cliente_telefone": cliente_telefone,
            "pet_nome": pet_nome,
            "pet_porte": pet_porte,
            "servico_nome": servico_nome,
            "data_hora": data_hora,
        },
        headers=_headers,
        timeout=10,
    )
    return resposta.json()


def cancelar(cliente_telefone, data_hora):
    # Mesmo motivo do agendar: sem raise_for_status, um 400 aqui e' um erro
    # de negocio esperado (agendamento nao existe, ja foi cancelado) que o
    # agente precisa ler e reagir, nao uma falha pra estourar excecao.
    resposta = httpx.post(
        f"{CRM_URL}/cancelar",
        json={"cliente_telefone": cliente_telefone, "data_hora": data_hora},
        headers=_headers,
        timeout=10,
    )
    return resposta.json()


TOOL_FUNCTIONS = {
    "listar_servicos": listar_servicos,
    "consultar_cliente": consultar_cliente,
    "consultar_agenda": consultar_agenda,
    "agendar": agendar,
    "cancelar": cancelar,
}
