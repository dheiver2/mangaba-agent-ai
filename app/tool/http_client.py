"""Requisições HTTP diretas (APIs REST) e download de arquivos."""

import json

from app.tool.base import BaseTool, ToolResult
from app.tool.gateway_media import _resolve

_PREVIEW = 3000


class HttpRequest(BaseTool):
    name: str = "http_request"
    description: str = (
        "Faz uma requisição HTTP (GET/POST/PUT/PATCH/DELETE) a uma API ou URL, com "
        "headers e corpo JSON opcionais. Com 'save_to', baixa o corpo da resposta "
        "para um arquivo do workspace (relatórios, imagens, CSVs). Use para APIs "
        "REST; para páginas HTML prefira fetch_url ou o navegador."
    )
    parameters: dict = {
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "URL completa (http/https)"},
            "method": {
                "type": "string",
                "enum": ["GET", "POST", "PUT", "PATCH", "DELETE"],
                "description": "Método HTTP (padrão GET)",
            },
            "headers": {
                "type": "object",
                "description": "Headers extras, ex. {\"Authorization\": \"Bearer ...\"}",
            },
            "body": {
                "type": "string",
                "description": "Corpo da requisição. Se for JSON válido, é enviado como application/json",
            },
            "save_to": {
                "type": "string",
                "description": "Caminho de destino para salvar a resposta (relativo cai no workspace)",
            },
        },
        "required": ["url"],
    }

    async def execute(
        self,
        url: str,
        method: str = "GET",
        headers: dict | None = None,
        body: str = "",
        save_to: str = "",
        **kwargs,
    ) -> ToolResult:
        import requests

        if not url.startswith(("http://", "https://")):
            return ToolResult(error=f"URL inválida (precisa de http/https): {url}")
        if isinstance(headers, str):
            try:
                headers = json.loads(headers)
            except json.JSONDecodeError:
                return ToolResult(error="'headers' deve ser um objeto JSON")

        kwargs_req: dict = {"headers": headers or {}, "timeout": 60}
        if body:
            try:
                kwargs_req["json"] = json.loads(body)
            except json.JSONDecodeError:
                kwargs_req["data"] = body

        try:
            resp = requests.request(method.upper(), url, stream=bool(save_to), **kwargs_req)
        except requests.RequestException as e:
            return ToolResult(error=f"Requisição falhou: {e}")

        ctype = resp.headers.get("content-type", "?")
        if save_to:
            dest = _resolve(save_to)
            dest.parent.mkdir(parents=True, exist_ok=True)
            size = 0
            with open(dest, "wb") as fh:
                for chunk in resp.iter_content(chunk_size=65536):
                    fh.write(chunk)
                    size += len(chunk)
            return ToolResult(
                output=f"HTTP {resp.status_code} — {size} bytes ({ctype}) salvos em {dest}"
            )

        text = resp.text or ""
        preview = text[:_PREVIEW] + ("… (truncado)" if len(text) > _PREVIEW else "")
        return ToolResult(
            output=f"HTTP {resp.status_code} ({ctype}, {len(text)} chars):\n{preview}"
        )
