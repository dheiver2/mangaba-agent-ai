"""Auto-agendamento: o agente enfileira tarefas futuras na fila do Operator.

Não importa fila.py (que importa o agente — ciclo); replica o formato
de arquivo .task que `fila.py run` consome (cron a cada hora).
"""

import time

from app.config import config
from app.tool.base import BaseTool, ToolResult

_FILA = config.workspace_root / "fila"


class ScheduleTask(BaseTool):
    name: str = "schedule_task"
    description: str = (
        "Agenda uma tarefa para execução futura enfileirando-a na fila do Operator "
        "(processada pelo cron de `fila.py run`). Use quando o pedido tiver uma "
        "parte que deva rodar depois/de novo (follow-up, monitoramento, relatório "
        "recorrente). Ações: add (enfileira 'prompt') e list (mostra a fila)."
    )
    parameters: dict = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["add", "list"],
                "description": "add: enfileira; list: estado da fila",
            },
            "prompt": {
                "type": "string",
                "description": "Instrução completa e autocontida da tarefa futura (para 'add')",
            },
        },
        "required": ["action"],
    }

    async def execute(self, action: str, prompt: str = "", **kwargs) -> ToolResult:
        for sub in ("", "concluidas", "falhas"):
            (_FILA / sub).mkdir(parents=True, exist_ok=True)

        if action == "add":
            if not prompt.strip():
                return ToolResult(error="'add' exige um 'prompt' não-vazio")
            nome = f"{int(time.time() * 1000)}.task"
            (_FILA / nome).write_text(prompt.strip(), encoding="utf-8")
            return ToolResult(
                output=(
                    f"Tarefa enfileirada como {nome}. Será executada na próxima "
                    "passada do processador da fila (fila.py run)."
                )
            )

        if action == "list":
            pend = sorted(_FILA.glob("*.task"))
            done = len(list((_FILA / "concluidas").glob("*.task")))
            fail = len(list((_FILA / "falhas").glob("*.task")))
            lines = [
                f"  • {p.name}: {p.read_text(encoding='utf-8')[:80]}" for p in pend[:20]
            ]
            body = "\n".join(lines) if lines else "  (vazia)"
            return ToolResult(
                output=f"Pendentes: {len(pend)}\n{body}\nConcluídas: {done} · Falhas: {fail}"
            )

        return ToolResult(error=f"Ação desconhecida: {action}")
