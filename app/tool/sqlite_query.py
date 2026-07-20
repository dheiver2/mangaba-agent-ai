"""Consultas SQL em bancos SQLite, com importação opcional de CSV."""

import csv
import sqlite3

from app.tool.base import BaseTool, ToolResult
from app.tool.gateway_media import _resolve

_MAX_ROWS = 100


class SqliteQuery(BaseTool):
    name: str = "sqlite_query"
    description: str = (
        "Executa SQL em um banco SQLite do workspace (SELECT, CREATE, INSERT...). "
        "Com 'csv_import', carrega antes um CSV como tabela — jeito rápido de "
        "analisar dados tabulares com SQL sem escrever Python. O banco padrão é "
        "workspace/dados.db."
    )
    parameters: dict = {
        "type": "object",
        "properties": {
            "sql": {"type": "string", "description": "Comando SQL a executar"},
            "db_path": {
                "type": "string",
                "description": "Arquivo .db/.sqlite (padrão: dados.db no workspace)",
            },
            "csv_import": {
                "type": "string",
                "description": "CSV a importar antes da consulta; vira tabela com o nome do arquivo",
            },
        },
        "required": ["sql"],
    }

    async def execute(
        self, sql: str, db_path: str = "dados.db", csv_import: str = "", **kwargs
    ) -> ToolResult:
        db = _resolve(db_path)
        db.parent.mkdir(parents=True, exist_ok=True)

        try:
            con = sqlite3.connect(db)
        except sqlite3.Error as e:
            return ToolResult(error=f"Não abriu o banco {db}: {e}")

        try:
            if csv_import:
                src = _resolve(csv_import)
                if not src.is_file():
                    return ToolResult(error=f"CSV não encontrado: {src}")
                table = src.stem.replace("-", "_").replace(" ", "_")
                with open(src, newline="", encoding="utf-8", errors="replace") as fh:
                    reader = csv.reader(fh)
                    header = next(reader, None)
                    if not header:
                        return ToolResult(error=f"CSV vazio: {src}")
                    cols = ", ".join(f'"{c.strip()}"' for c in header)
                    ph = ", ".join("?" for _ in header)
                    con.execute(f'DROP TABLE IF EXISTS "{table}"')
                    con.execute(f'CREATE TABLE "{table}" ({cols})')
                    n = 0
                    for row in reader:
                        row = (row + [""] * len(header))[: len(header)]
                        con.execute(f'INSERT INTO "{table}" VALUES ({ph})', row)
                        n += 1
                    con.commit()

            cur = con.execute(sql)
            if cur.description:  # consulta com resultado
                cols = [d[0] for d in cur.description]
                rows = cur.fetchmany(_MAX_ROWS)
                more = cur.fetchone() is not None
                lines = ["\t".join(cols)]
                lines += ["\t".join("" if v is None else str(v) for v in r) for r in rows]
                tail = "\n… (mais linhas; refine com LIMIT)" if more else ""
                out = f"{len(rows)} linha(s):\n" + "\n".join(lines) + tail
            else:
                con.commit()
                out = f"OK — {cur.rowcount if cur.rowcount >= 0 else 0} linha(s) afetada(s)"
            if csv_import:
                out = f"CSV importado como tabela '{table}' ({n} linhas).\n" + out
            return ToolResult(output=out)
        except sqlite3.Error as e:
            return ToolResult(error=f"Erro SQL: {e}")
        finally:
            con.close()
