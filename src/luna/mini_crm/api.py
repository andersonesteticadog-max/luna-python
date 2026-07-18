import json
import re
import urllib.parse
from datetime import datetime, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from luna.config import CRM_BEARER
from luna.mini_crm.db import conectar, inicializar

ABERTURA = 9
FECHAMENTO = 18
PASSO_MIN = 30


def ep_servicos():
    conn = conectar()
    linhas = conn.execute("SELECT nome, preco, duracao_min FROM servicos").fetchall()
    conn.close()
    return 200, {"servicos": [dict(linha) for linha in linhas]}


def horarios_disponiveis(data, duracao_min, ocupados):
    """Mesma logica de intervalos do horarios_agenda.py do portfolio: gera
    candidatos a cada PASSO_MIN dentro do expediente e descarta os que
    colidem com algum agendamento existente (considerando a duracao dele)."""
    abertura = datetime.strptime(f"{data} {ABERTURA:02d}:00", "%Y-%m-%d %H:%M")
    fechamento = datetime.strptime(f"{data} {FECHAMENTO:02d}:00", "%Y-%m-%d %H:%M")

    livres = []
    candidato = abertura
    while candidato + timedelta(minutes=duracao_min) <= fechamento:
        fim_candidato = candidato + timedelta(minutes=duracao_min)
        conflito = any(candidato < fim_oc and inicio_oc < fim_candidato
                        for inicio_oc, fim_oc in ocupados)
        if not conflito:
            livres.append(candidato.strftime("%H:%M"))
        candidato += timedelta(minutes=PASSO_MIN)
    return livres


def ep_agenda(params):
    data = params.get("data", [None])[0]
    if not data or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", data):
        return 400, {"erro": "informe o parametro data no formato AAAA-MM-DD"}
    try:
        duracao_min = int(params.get("duracao_min", ["60"])[0])
    except ValueError:
        return 400, {"erro": "duracao_min precisa ser um numero"}

    conn = conectar()
    linhas = conn.execute(
        "SELECT a.data_hora, s.duracao_min AS duracao "
        "FROM agendamentos a JOIN servicos s ON s.id = a.servico_id "
        "WHERE a.status != 'Cancelado' AND substr(a.data_hora, 1, 10) = ?",
        (data,),
    ).fetchall()
    conn.close()

    ocupados = []
    for linha in linhas:
        inicio = datetime.strptime(linha["data_hora"], "%Y-%m-%d %H:%M")
        ocupados.append((inicio, inicio + timedelta(minutes=linha["duracao"])))

    livres = horarios_disponiveis(data, duracao_min, ocupados)
    return 200, {"data": data, "duracao_min": duracao_min, "horarios_livres": livres}


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, obj):
        corpo = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(corpo)

    def _autorizado(self):
        return self.headers.get("Authorization") == f"Bearer {CRM_BEARER}"

    def do_GET(self):
        rota = urllib.parse.urlparse(self.path)
        if rota.path == "/health":
            return self._send(200, {"ok": True})
        if not self._autorizado():
            return self._send(401, {"erro": "nao autorizado"})

        params = urllib.parse.parse_qs(rota.query)
        if rota.path == "/servicos":
            codigo, corpo = ep_servicos()
            return self._send(codigo, corpo)
        if rota.path == "/agenda":
            codigo, corpo = ep_agenda(params)
            return self._send(codigo, corpo)
        return self._send(404, {"erro": "rota nao encontrada"})

    def log_message(self, *args):
        pass


def main():
    inicializar()
    print("mini-CRM rodando em http://127.0.0.1:8095 (Ctrl+C pra parar)")
    ThreadingHTTPServer(("127.0.0.1", 8095), Handler).serve_forever()


if __name__ == "__main__":
    main()
