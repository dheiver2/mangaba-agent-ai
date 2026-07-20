"""Síntese de voz local (macOS `say`) — voz para relatórios e avisos."""

import asyncio
import shutil
import time

from app.config import config
from app.tool.base import BaseTool, ToolResult


class TextToSpeech(BaseTool):
    name: str = "text_to_speech"
    description: str = (
        "Converte texto em áudio falado (síntese de voz local do macOS) e salva "
        ".aiff no workspace — bom para resumos audíveis e notificações faladas. "
        "Vozes PT-BR: 'Luciana' (padrão) e 'Joana'."
    )
    parameters: dict = {
        "type": "object",
        "properties": {
            "text": {"type": "string", "description": "Texto a falar (até ~2000 chars)"},
            "voice": {
                "type": "string",
                "description": "Voz do sistema (padrão: Luciana, PT-BR)",
            },
            "play": {
                "type": "boolean",
                "description": "true: também toca o áudio nos alto-falantes (padrão false)",
            },
        },
        "required": ["text"],
    }

    async def execute(
        self, text: str, voice: str = "Luciana", play: bool = False, **kwargs
    ) -> ToolResult:
        if not shutil.which("say"):
            return ToolResult(
                error="Comando 'say' indisponível (síntese de voz exige macOS)"
            )
        text = text.strip()
        if not text:
            return ToolResult(error="Texto vazio")
        text = text[:2000]

        dest = config.workspace_root / f"fala_{time.strftime('%Y%m%d_%H%M%S')}.aiff"
        dest.parent.mkdir(parents=True, exist_ok=True)
        proc = await asyncio.create_subprocess_exec(
            "say", "-v", voice, "-o", str(dest), text,
            stderr=asyncio.subprocess.PIPE,
        )
        _, err = await proc.communicate()
        if proc.returncode != 0:
            return ToolResult(
                error=f"say falhou (voz '{voice}' existe?): {err.decode()[:200]}"
            )

        if play:
            await asyncio.create_subprocess_exec("afplay", str(dest))

        size = dest.stat().st_size
        return ToolResult(
            output=f"Áudio gerado ({size} bytes, voz {voice}): {dest}"
            + (" — tocando agora" if play else "")
        )
