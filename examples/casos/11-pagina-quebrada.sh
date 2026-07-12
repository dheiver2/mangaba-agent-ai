#!/usr/bin/env bash
# Case híbrido: página "quebrada" pra automação — todo o conteúdo é desenhado em
# canvas, o DOM fica vazio (extract_content não acha nada). A visão é o único
# caminho: visual_query lê o código na tela e o agente salva em arquivo.
# Abre o Chromium. 2–4 min.
# Pré-requisito: modelo multimodal no perfil [llm.vision] do config.toml.
cd "$(dirname "$0")/../.." || exit 1

mkdir -p workspace
cat > workspace/pagina-quebrada.html <<'HTML'
<!DOCTYPE html>
<html><body style="margin:0;background:#1a1a2e">
<canvas id="c" width="900" height="400"></canvas>
<script>
  const ctx = document.getElementById('c').getContext('2d');
  ctx.fillStyle = '#1a1a2e'; ctx.fillRect(0, 0, 900, 400);
  ctx.fillStyle = '#E94A12'; ctx.font = 'bold 40px monospace';
  ctx.fillText('CODIGO DE RESGATE:', 80, 160);
  ctx.fillStyle = '#fff'; ctx.font = 'bold 56px monospace';
  ctx.fillText('MANGA-2026-XK7', 80, 250);
</script>
</body></html>
HTML

.venv/bin/python main.py --max-steps 6 --prompt "Execute EXATAMENTE estes 4 passos, um por vez:
1. browser_use com action go_to_url e url file://$(pwd)/workspace/pagina-quebrada.html
2. browser_use com action visual_query e goal 'Leia e transcreva exatamente o código de resgate exibido na tela'
3. str_replace_editor com command create, path workspace/codigo-resgate.txt e file_text contendo somente o código lido no passo 2
4. terminate com status success
Não use extract_content (a página não tem texto no DOM), não clique em nada."
