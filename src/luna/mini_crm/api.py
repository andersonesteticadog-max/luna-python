import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from luna.config import CRM_BEARER
from luna.mini_crm.db import conectar, inicializar


def ep_servicos():
    conn = conectar()
    linhas = conn.execute("SELECT nome, preco, duracao_min FROM servicos").fetchall()
    conn.close()
    return {"servicos": [dict(linha) for linha in linhas]}


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
        if self.path == "/health":
            return self._send(200, {"ok": True})
        if not self._autorizado():
            return self._send(401, {"erro": "nao autorizado"})
        if self.path == "/servicos":
            return self._send(200, ep_servicos())
        return self._send(404, {"erro": "rota nao encontrada"})

    def log_message(self, *args):
        pass


def main():
    inicializar()
    print("mini-CRM rodando em http://127.0.0.1:8095 (Ctrl+C pra parar)")
    ThreadingHTTPServer(("127.0.0.1", 8095), Handler).serve_forever()


if __name__ == "__main__":
    main()
