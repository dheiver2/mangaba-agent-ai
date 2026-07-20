"""Compactação e extração de arquivos (zip/tar) no workspace."""

import tarfile
import zipfile

from app.tool.base import BaseTool, ToolResult
from app.tool.gateway_media import _resolve


class Archive(BaseTool):
    name: str = "archive"
    description: str = (
        "Compacta arquivos/pastas em .zip, extrai .zip/.tar.gz/.tgz, ou lista o "
        "conteúdo de um pacote sem extrair. Caminhos relativos são resolvidos "
        "contra o workspace."
    )
    parameters: dict = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["zip", "unzip", "list"],
                "description": "zip: compacta 'sources' em 'dest'; unzip: extrai 'archive_path' em 'dest'; list: lista 'archive_path'",
            },
            "sources": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Arquivos/pastas a compactar (para 'zip')",
            },
            "archive_path": {
                "type": "string",
                "description": "Pacote existente (para 'unzip'/'list')",
            },
            "dest": {
                "type": "string",
                "description": "Destino: o .zip a criar, ou a pasta de extração (padrão: workspace)",
            },
        },
        "required": ["action"],
    }

    async def execute(
        self,
        action: str,
        sources: list | None = None,
        archive_path: str = "",
        dest: str = "",
        **kwargs,
    ) -> ToolResult:
        try:
            if action == "zip":
                if not sources:
                    return ToolResult(error="'zip' exige a lista 'sources'")
                if isinstance(sources, str):
                    sources = [sources]
                out = _resolve(dest or "arquivo.zip")
                out.parent.mkdir(parents=True, exist_ok=True)
                count = 0
                with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
                    for src in sources:
                        p = _resolve(src)
                        if p.is_file():
                            zf.write(p, p.name)
                            count += 1
                        elif p.is_dir():
                            for f in sorted(p.rglob("*")):
                                if f.is_file():
                                    zf.write(f, f.relative_to(p.parent))
                                    count += 1
                        else:
                            return ToolResult(error=f"Não encontrado: {p}")
                size = out.stat().st_size
                return ToolResult(
                    output=f"Compactados {count} arquivo(s) em {out} ({size} bytes)"
                )

            if not archive_path:
                return ToolResult(error=f"'{action}' exige 'archive_path'")
            pkg = _resolve(archive_path)
            if not pkg.is_file():
                return ToolResult(error=f"Pacote não encontrado: {pkg}")

            is_tar = pkg.suffixes[-2:] == [".tar", ".gz"] or pkg.suffix in (".tgz", ".tar")

            if action == "list":
                if is_tar:
                    with tarfile.open(pkg) as tf:
                        names = tf.getnames()
                else:
                    with zipfile.ZipFile(pkg) as zf:
                        names = zf.namelist()
                shown = "\n".join(f"  {n}" for n in names[:100])
                extra = f" (+{len(names) - 100} omitidos)" if len(names) > 100 else ""
                return ToolResult(output=f"{len(names)} entrada(s){extra}:\n{shown}")

            if action == "unzip":
                target = _resolve(dest) if dest else _resolve(pkg.stem)
                target.mkdir(parents=True, exist_ok=True)
                if is_tar:
                    with tarfile.open(pkg) as tf:
                        tf.extractall(target, filter="data")
                        n = len(tf.getnames())
                else:
                    with zipfile.ZipFile(pkg) as zf:
                        zf.extractall(target)
                        n = len(zf.namelist())
                return ToolResult(output=f"Extraídas {n} entrada(s) em {target}")

            return ToolResult(error=f"Ação desconhecida: {action}")
        except (zipfile.BadZipFile, tarfile.TarError) as e:
            return ToolResult(error=f"Pacote corrompido ou formato não suportado: {e}")
