import json
import re
import unicodedata
import urllib.parse
from datetime import datetime, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from luna.config import CRM_BEARER
from luna.mini_crm.db import conectar, inicializar

ABERTURA = 9
FECHAMENTO = 18
PASSO_MIN = 30
STOP_WORDS = {"e", "de", "com", "para", "pra", "o", "a", "do", "da"}


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


def normalizar(texto):
    texto = unicodedata.normalize("NFD", (texto or "").strip().lower())
    return "".join(c for c in texto if unicodedata.category(c) != "Mn")


def tokenizar(texto):
    return [t for t in re.split(r"[^a-z0-9]+", normalizar(texto)) if t and t not in STOP_WORDS]


def buscar_servico(nome_busca, porte=None):
    """Mesmo algoritmo do agendador_servicos.py do portfolio: casa por nome
    exato primeiro, senao por sobreposicao de palavras, desempatando por
    porte quando ambiguo. So que agora os servicos vem do SQLite."""
    conn = conectar()
    servicos = [dict(s) for s in conn.execute(
        "SELECT id, nome, preco, duracao_min FROM servicos").fetchall()]
    conn.close()

    consulta = set(tokenizar(nome_busca))
    if not consulta:
        return "nao_encontrado", None

    for s in servicos:
        if normalizar(s["nome"]) == normalizar(nome_busca):
            return "ok", s

    pontuados = []
    for s in servicos:
        palavras = set(tokenizar(s["nome"]))
        sobreposicao = len(consulta & palavras)
        if sobreposicao:
            pontuados.append((sobreposicao, -len(palavras - consulta), s))

    if not pontuados:
        return "nao_encontrado", None

    pontuados.sort(key=lambda item: (item[0], item[1]), reverse=True)
    melhor = pontuados[0][:2]
    vencedores = [s for p in pontuados if p[:2] == melhor for s in [p[2]]]

    if len(vencedores) > 1 and porte:
        por_porte = [v for v in vencedores if normalizar(porte) in tokenizar(v["nome"])]
        if por_porte:
            vencedores = por_porte

    if len(vencedores) == 1:
        return "ok", vencedores[0]
    return "ambiguo", [v["nome"] for v in vencedores]


def ep_cliente(params):
    telefone = re.sub(r"\D", "", (params.get("telefone", [None])[0] or ""))
    if not telefone:
        return 400, {"erro": "informe o parametro telefone"}

    conn = conectar()
    cliente = conn.execute(
        "SELECT id, nome, telefone FROM clientes WHERE telefone = ?", (telefone,)
    ).fetchone()
    if not cliente:
        conn.close()
        return 200, {"encontrado": False}

    pets = conn.execute(
        "SELECT nome, especie, porte, raca FROM pets WHERE cliente_id = ?", (cliente["id"],)
    ).fetchall()
    agendamentos = conn.execute(
        "SELECT a.data_hora, a.status, s.nome AS servico "
        "FROM agendamentos a JOIN servicos s ON s.id = a.servico_id "
        "WHERE a.cliente_id = ? ORDER BY a.data_hora DESC LIMIT 5",
        (cliente["id"],),
    ).fetchall()
    conn.close()

    return 200, {
        "encontrado": True,
        "cliente": {"nome": cliente["nome"], "telefone": cliente["telefone"]},
        "pets": [dict(p) for p in pets],
        "ultimos_agendamentos": [dict(a) for a in agendamentos],
    }


def validar_telefone(telefone):
    digitos = re.sub(r"\D", "", telefone or "")
    return digitos if 10 <= len(digitos) <= 11 else None


def validar_data_hora(texto):
    try:
        dh = datetime.strptime(texto, "%Y-%m-%d %H:%M")
    except ValueError:
        return None, "formato invalido, use AAAA-MM-DD HH:MM"
    if dh < datetime.now():
        return None, "essa data/hora ja passou"
    return dh, None


def ep_agendar(body):
    obrigatorios = ["cliente_nome", "cliente_telefone", "pet_nome", "servico_nome", "data_hora"]
    faltando = [c for c in obrigatorios if not body.get(c)]
    if faltando:
        return 400, {"ok": False, "erro": f"faltam campos: {', '.join(faltando)} - NAO foi agendado"}

    telefone = validar_telefone(body["cliente_telefone"])
    if not telefone:
        return 400, {"ok": False, "erro": "telefone invalido (informe DDD + numero) - NAO foi agendado"}

    dh, erro = validar_data_hora(body["data_hora"])
    if erro:
        return 400, {"ok": False, "erro": f"{erro} - NAO foi agendado"}

    tipo, resultado = buscar_servico(body["servico_nome"], body.get("pet_porte"))
    if tipo == "ambiguo":
        return 400, {"ok": False, "erro": "servico ambiguo - NAO foi agendado", "opcoes": resultado}
    if tipo == "nao_encontrado":
        return 400, {"ok": False,
                     "erro": f"servico '{body['servico_nome']}' nao existe - NAO foi agendado"}

    conn = conectar()
    cliente = conn.execute("SELECT id FROM clientes WHERE telefone = ?", (telefone,)).fetchone()
    if cliente:
        cliente_id = cliente["id"]
    else:
        cur = conn.execute("INSERT INTO clientes (nome, telefone) VALUES (?, ?)",
                            (body["cliente_nome"], telefone))
        cliente_id = cur.lastrowid

    pet = conn.execute("SELECT id FROM pets WHERE cliente_id = ? AND nome = ?",
                        (cliente_id, body["pet_nome"])).fetchone()
    if pet:
        pet_id = pet["id"]
    else:
        cur = conn.execute("INSERT INTO pets (cliente_id, nome, porte) VALUES (?, ?, ?)",
                            (cliente_id, body["pet_nome"], body.get("pet_porte")))
        pet_id = cur.lastrowid

    cur = conn.execute(
        "INSERT INTO agendamentos (cliente_id, pet_id, servico_id, data_hora, status) "
        "VALUES (?, ?, ?, ?, 'Agendado')",
        (cliente_id, pet_id, resultado["id"], dh.strftime("%Y-%m-%d %H:%M")),
    )
    agendamento_id = cur.lastrowid
    conn.commit()
    conn.close()

    return 200, {"ok": True, "agendamento_id": agendamento_id, "servico": resultado["nome"],
                 "preco": resultado["preco"], "data_hora": dh.strftime("%Y-%m-%d %H:%M")}


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
        if rota.path == "/cliente":
            codigo, corpo = ep_cliente(params)
            return self._send(codigo, corpo)
        return self._send(404, {"erro": "rota nao encontrada"})

    def do_POST(self):
        if not self._autorizado():
            return self._send(401, {"erro": "nao autorizado"})
        tamanho = int(self.headers.get("Content-Length", 0))
        try:
            body = json.loads(self.rfile.read(tamanho) or b"{}")
        except json.JSONDecodeError:
            return self._send(400, {"erro": "json invalido"})

        if urllib.parse.urlparse(self.path).path == "/agendar":
            codigo, corpo = ep_agendar(body)
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
