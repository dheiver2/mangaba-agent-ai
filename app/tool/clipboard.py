"""Área de transferência do sistema (pbcopy/pbpaste) — ponte com apps do usuário."""

import asyncio
import shutil

from app.tool.base import BaseTool, ToolResult

_PREVIEW = 3000


class Clipboard(BaseTool):
    name: str = "clipboard"
    description: str = (
        "Lê (paste) ou escreve (copy) a área de transferência do sistema — jeito "
        "rápido de trocar texto com apps abertos do usuário (colar num campo, "
        "receber algo que o usuário copiou)."
    )
    parameters: dict = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["copy", "paste"],
                "description": "copy: coloca 'text' no clipboard; paste: retorna o conteúdo atual",
            },
            "text": {"type": "string", "description": "Texto a copiar (para 'copy')"},
        },
        "required": ["action"],
    }

    async def execute(self, action: str, text: str = "", **kwargs) -> ToolResult:
        if not shutil.which("pbcopy"):
            return ToolResult(error="pbcopy/pbpaste indisponíveis (exige macOS)")

        if action == "copy":
            if not text:
                return ToolResult(error="'copy' exige 'text'")
            proc = await asyncio.create_subprocess_exec(
                "pbcopy", stdin=asyncio.subprocess.PIPE
            )
            await proc.communicate(text.encode("utf-8"))
            return ToolResult(output=f"Copiados {len(text)} caracteres para o clipboard")

        if action == "paste":
            proc = await asyncio.create_subprocess_exec(
                "pbpaste", stdout=asyncio.subprocess.PIPE
            )
            out, _ = await proc.communicate()
            content = out.decode("utf-8", errors="replace")
            if not content:
                return ToolResult(output="Clipboard vazio")
            preview = content[:_PREVIEW] + (
                "… (truncado)" if len(content) > _PREVIEW else ""
            )
            return ToolResult(output=f"Clipboard ({len(content)} chars):\n{preview}")

        return ToolResult(error=f"Ação desconhecida: {action}")
