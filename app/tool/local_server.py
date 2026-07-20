"""Servidor HTTP local para publicar arquivos do workspace (estilo deploy)."""

import functools
import http.server
import threading

from app.config import config
from app.tool.base import BaseTool, ToolResult
from app.tool.gateway_media import _resolve

# registro global: sobrevive a re-instanciações do tool no mesmo processo
_SERVERS: dict[int, "http.server.ThreadingHTTPServer"] = {}


class _QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):  # sem ruído no stdout do agente
        pass


class LocalServer(BaseTool):
    name: str = "local_server"
    description: str = (
        "Publica uma pasta (padrão: o workspace) num servidor HTTP local — útil "
        "para 'deployar' um site/relatório HTML gerado e abri-lo no navegador, ou "
        "para testar downloads. Ações: start (retorna a URL), stop, status."
    )
    parameters: dict = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["start", "stop", "status"],
                "description": "start: sobe o servidor; stop: derruba; status: lista ativos",
            },
            "port": {
                "type": "integer",
                "description": "Porta TCP (padrão 8700)",
            },
            "dir": {
                "type": "string",
                "description": "Pasta a servir (padrão: workspace; relativo cai no workspace)",
            },
        },
        "required": ["action"],
    }

    async def execute(
        self, action: str, port: int = 8700, dir: str = "", **kwargs
    ) -> ToolResult:
        try:
            port = int(port)
        except (TypeError, ValueError):
            return ToolResult(error=f"Porta inválida: {port!r}")

        if action == "status":
            if not _SERVERS:
                return ToolResult(output="Nenhum servidor local ativo")
            lines = [
                f"  http://localhost:{p} → {srv.RequestHandlerClass.directory}"
                for p, srv in _SERVERS.items()
            ]
            return ToolResult(output="Servidores ativos:\n" + "\n".join(lines))

        if action == "stop":
            srv = _SERVERS.pop(port, None)
            if not srv:
                return ToolResult(output=f"Nenhum servidor na porta {port}")
            srv.shutdown()
            srv.server_close()
            return ToolResult(output=f"Servidor da porta {port} derrubado")

        if action == "start":
            if port in _SERVERS:
                return ToolResult(
                    output=f"Já ativo: http://localhost:{port}"
                )
            root = _resolve(dir) if dir else config.workspace_root
            if not root.is_dir():
                return ToolResult(error=f"Pasta não encontrada: {root}")
            handler = functools.partial(_QuietHandler, directory=str(root))
            handler.directory = str(root)  # p/ o status
            try:
                srv = http.server.ThreadingHTTPServer(("127.0.0.1", port), handler)
            except OSError as e:
                return ToolResult(error=f"Porta {port} indisponível: {e}")
            threading.Thread(target=srv.serve_forever, daemon=True).start()
            _SERVERS[port] = srv
            return ToolResult(
                output=f"Servindo {root} em http://localhost:{port} (use 'stop' ao terminar)"
            )

        return ToolResult(error=f"Ação desconhecida: {action}")
