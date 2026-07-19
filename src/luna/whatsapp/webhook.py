import base64
import json
import os
import tempfile
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from luna.agent import executar_turno
from luna.media.audio import transcrever
from luna.media.image import preparar_imagem
from luna.memory import carregar, salvar
from luna.prompt import carregar_system_prompt
from luna.tools.crm import TOOL_FUNCTIONS
from luna.tools.schemas import TOOLS_SCHEMA
from luna.whatsapp.evolution import enviar_mensagem

SYSTEM = carregar_system_prompt()

# Guarda os ids de mensagem ja processados nesta execucao, pra nao responder
# duas vezes se a Evolution reenviar o mesmo evento de webhook. Por
# precaucao - nao confirmamos que isso acontece na pratica, mas e barato
# de evitar. So dura enquanto o processo estiver rodando (nao precisa
# sobreviver a um restart pra essa fase).
IDS_PROCESSADOS = set()


def _salvar_base64_temp(b64, sufixo):
    dados = base64.b64decode(b64)
    fd, caminho = tempfile.mkstemp(suffix=sufixo)
    with os.fdopen(fd, "wb") as f:
        f.write(dados)
    return caminho


def extrair_conteudo(data):
    """Le o payload da Evolution API e devolve o conteudo pronto pra Luna:
    texto direto pro caso simples, ou o resultado do preprocessamento de
    audio/imagem (Fase 4) - a Luna nunca ve audio/imagem cru, so texto."""
    tipo = data.get("messageType")
    mensagem = data.get("message", {})

    if tipo == "conversation":
        return mensagem.get("conversation")

    if tipo == "audioMessage":
        caminho = _salvar_base64_temp(data["base64"], ".ogg")
        try:
            return transcrever(caminho)
        finally:
            os.remove(caminho)

    if tipo == "imageMessage":
        caminho = _salvar_base64_temp(data["base64"], ".jpg")
        try:
            bloco_imagem = preparar_imagem(caminho)
        finally:
            os.remove(caminho)
        legenda = mensagem.get("imageMessage", {}).get("caption")
        return [bloco_imagem, {"type": "text", "text": legenda or "Descreva o que voce ve nessa imagem."}]

    return None


def processar_mensagem(data):
    key = data["key"]
    if key["remoteJid"].endswith("@g.us"):
        return  # ignora mensagem de grupo
    if key["fromMe"]:
        return  # ignora mensagem enviada pelo proprio numero do negocio
    if key["id"] in IDS_PROCESSADOS:
        return  # webhook duplicado, ja respondemos essa
    IDS_PROCESSADOS.add(key["id"])

    conteudo = extrair_conteudo(data)
    if conteudo is None:
        return

    numero = key["remoteJid"].split("@")[0]
    mensagens = carregar(numero)
    mensagens.append({"role": "user", "content": conteudo})
    resposta = executar_turno(mensagens, TOOLS_SCHEMA, TOOL_FUNCTIONS, SYSTEM)
    mensagens.append({"role": "assistant", "content": resposta})
    salvar(numero, mensagens)

    enviar_mensagem(numero, resposta)


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        if urllib.parse.urlparse(self.path).path != "/webhook":
            self.send_response(404)
            self.end_headers()
            return

        tamanho = int(self.headers.get("Content-Length", 0))
        try:
            payload = json.loads(self.rfile.read(tamanho) or b"{}")
        except json.JSONDecodeError:
            self.send_response(400)
            self.end_headers()
            return

        if payload.get("event") == "messages.upsert":
            processar_mensagem(payload["data"])

        self.send_response(200)
        self.end_headers()

    def log_message(self, *args):
        pass


def main():
    print("Webhook da Luna rodando em http://127.0.0.1:8096/webhook (Ctrl+C pra parar)")
    ThreadingHTTPServer(("127.0.0.1", 8096), Handler).serve_forever()


if __name__ == "__main__":
    main()
