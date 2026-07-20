"""Edição básica de imagens (Pillow) — evidências, anexos, thumbnails."""

from app.tool.base import BaseTool, ToolResult
from app.tool.gateway_media import _resolve


class ImageEdit(BaseTool):
    name: str = "image_edit"
    description: str = (
        "Operações básicas em imagens locais: info (dimensões/formato), resize, "
        "crop, rotate e convert (png/jpg/webp). Para ENTENDER o conteúdo de uma "
        "imagem use describe_image; esta ferramenta só transforma o arquivo."
    )
    parameters: dict = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["info", "resize", "crop", "rotate", "convert"],
                "description": "Operação a aplicar",
            },
            "image_path": {"type": "string", "description": "Imagem de origem"},
            "dest": {
                "type": "string",
                "description": "Arquivo de saída (padrão: sufixo _editado; a extensão define o formato em 'convert')",
            },
            "width": {"type": "integer", "description": "Largura alvo para 'resize'"},
            "height": {
                "type": "integer",
                "description": "Altura alvo para 'resize' (omitida = mantém proporção)",
            },
            "box": {
                "type": "array",
                "items": {"type": "integer"},
                "description": "Retângulo [esq, topo, dir, base] para 'crop'",
            },
            "degrees": {
                "type": "integer",
                "description": "Graus anti-horários para 'rotate' (90/180/270...)",
            },
        },
        "required": ["action", "image_path"],
    }

    async def execute(
        self,
        action: str,
        image_path: str,
        dest: str = "",
        width: int | None = None,
        height: int | None = None,
        box: list | None = None,
        degrees: int | None = None,
        **kwargs,
    ) -> ToolResult:
        from PIL import Image

        src = _resolve(image_path)
        if not src.is_file():
            return ToolResult(error=f"Imagem não encontrada: {src}")

        try:
            im = Image.open(src)
            im.load()
        except Exception as e:
            return ToolResult(error=f"Arquivo não é imagem legível: {e}")

        if action == "info":
            return ToolResult(
                output=(
                    f"{src.name}: {im.width}x{im.height} px, formato {im.format}, "
                    f"modo {im.mode}, {src.stat().st_size} bytes"
                )
            )

        try:
            if action == "resize":
                if not width and not height:
                    return ToolResult(error="'resize' exige width e/ou height")
                w = int(width) if width else round(im.width * int(height) / im.height)
                h = int(height) if height else round(im.height * int(width) / im.width)
                im = im.resize((w, h), Image.LANCZOS)
            elif action == "crop":
                if not box or len(box) != 4:
                    return ToolResult(error="'crop' exige box=[esq, topo, dir, base]")
                im = im.crop(tuple(int(v) for v in box))
            elif action == "rotate":
                if degrees is None:
                    return ToolResult(error="'rotate' exige 'degrees'")
                im = im.rotate(int(degrees), expand=True)
            elif action == "convert":
                if not dest:
                    return ToolResult(
                        error="'convert' exige 'dest' com a nova extensão (ex. foto.webp)"
                    )
            else:
                return ToolResult(error=f"Ação desconhecida: {action}")

            out = _resolve(dest) if dest else src.with_stem(src.stem + "_editado")
            out.parent.mkdir(parents=True, exist_ok=True)
            if out.suffix.lower() in (".jpg", ".jpeg") and im.mode in ("RGBA", "P"):
                im = im.convert("RGB")  # JPEG não tem alfa
            im.save(out)
            return ToolResult(
                output=f"{action} OK → {out} ({im.width}x{im.height}, {out.stat().st_size} bytes)"
            )
        except Exception as e:
            return ToolResult(error=f"Falha em '{action}': {e}")
