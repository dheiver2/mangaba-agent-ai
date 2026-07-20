"""Geração de PDF a partir de texto/markdown leve (reportlab)."""

import time

from app.config import config
from app.tool.base import BaseTool, ToolResult
from app.tool.gateway_media import _resolve


class TextToPdf(BaseTool):
    name: str = "text_to_pdf"
    description: str = (
        "Gera um PDF formatado a partir de texto simples ou markdown leve "
        "(títulos com #, ## e listas com -). Ideal para entregar relatórios e "
        "resumos como arquivo. Para layouts complexos use python_execute com "
        "reportlab direto."
    )
    parameters: dict = {
        "type": "object",
        "properties": {
            "text": {"type": "string", "description": "Conteúdo do documento"},
            "title": {"type": "string", "description": "Título da capa (opcional)"},
            "dest": {
                "type": "string",
                "description": "Arquivo .pdf de saída (padrão: relatorio_<timestamp>.pdf no workspace)",
            },
        },
        "required": ["text"],
    }

    async def execute(
        self, text: str, title: str = "", dest: str = "", **kwargs
    ) -> ToolResult:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib.units import cm
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

        if not text.strip():
            return ToolResult(error="Texto vazio")

        out = (
            _resolve(dest)
            if dest
            else config.workspace_root / f"relatorio_{time.strftime('%Y%m%d_%H%M%S')}.pdf"
        )
        out.parent.mkdir(parents=True, exist_ok=True)

        styles = getSampleStyleSheet()
        story = []
        if title:
            story += [Paragraph(title, styles["Title"]), Spacer(1, 0.5 * cm)]

        def _esc(s: str) -> str:
            return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

        for raw in text.splitlines():
            line = raw.rstrip()
            if not line.strip():
                story.append(Spacer(1, 0.25 * cm))
            elif line.startswith("## "):
                story.append(Paragraph(_esc(line[3:]), styles["Heading2"]))
            elif line.startswith("# "):
                story.append(Paragraph(_esc(line[2:]), styles["Heading1"]))
            elif line.lstrip().startswith(("- ", "* ")):
                story.append(
                    Paragraph("• " + _esc(line.lstrip()[2:]), styles["Normal"])
                )
            else:
                story.append(Paragraph(_esc(line), styles["Normal"]))

        try:
            SimpleDocTemplate(str(out), pagesize=A4).build(story)
        except Exception as e:
            return ToolResult(error=f"Falha ao gerar PDF: {e}")

        return ToolResult(
            output=f"PDF gerado: {out} ({out.stat().st_size} bytes)"
        )
