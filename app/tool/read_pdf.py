"""Leitura direta de PDFs (texto e tabelas) com cache reversível."""

from pathlib import Path

from app.config import config
from app.tool.base import BaseTool, ToolResult
from app.tool.gateway_media import _resolve

_PREVIEW = 5000


class ReadPdf(BaseTool):
    name: str = "read_pdf"
    description: str = (
        "Extrai o texto (e detecta tabelas) de um arquivo PDF local — contratos, "
        "notas fiscais, relatórios. Mais rápido e confiável que abrir o PDF por "
        "outros meios. O texto completo fica salvo em workspace/cache/."
    )
    parameters: dict = {
        "type": "object",
        "properties": {
            "pdf_path": {
                "type": "string",
                "description": "Caminho do PDF; relativo é resolvido contra o workspace",
            },
            "pages": {
                "type": "string",
                "description": "Intervalo opcional de páginas, ex. '1-3' ou '2' (padrão: todas)",
            },
        },
        "required": ["pdf_path"],
    }

    async def execute(self, pdf_path: str, pages: str = "", **kwargs) -> ToolResult:
        import pdfplumber

        path = _resolve(pdf_path)
        if not path.is_file():
            return ToolResult(error=f"PDF não encontrado: {path}")

        try:
            with pdfplumber.open(path) as pdf:
                total = len(pdf.pages)
                if pages:
                    parts = pages.split("-")
                    start = max(1, int(parts[0]))
                    end = min(total, int(parts[-1]))
                else:
                    start, end = 1, total
                chunks, n_tables = [], 0
                for i in range(start - 1, end):
                    page = pdf.pages[i]
                    chunks.append(f"--- Página {i + 1} ---\n{page.extract_text() or '(sem texto extraível)'}")
                    for tb in page.extract_tables():
                        n_tables += 1
                        linhas = ["\t".join(str(c) if c is not None else "" for c in row) for row in tb]
                        chunks.append(f"[Tabela {n_tables} da página {i + 1}]\n" + "\n".join(linhas))
        except Exception as e:
            return ToolResult(error=f"Falha ao ler PDF: {e}")

        text = "\n\n".join(chunks).strip()
        cache_dir = config.workspace_root / "cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
        saved = cache_dir / f"pdf-{path.stem}.txt"
        saved.write_text(text, encoding="utf-8")

        header = (
            f"PDF {path.name}: {total} página(s), lidas {start}-{end}, "
            f"{n_tables} tabela(s). Texto completo salvo em {saved}.\n\n"
        )
        if len(text) > _PREVIEW:
            return ToolResult(output=header + text[:_PREVIEW] + "\n[...restante no arquivo de cache...]")
        return ToolResult(output=header + text)
