#!/usr/bin/env bash
# Case híbrido: click_coordinates em <canvas> — elemento invisível pra árvore DOM
# (click_element não funciona aqui). Gera uma página local determinística: o canvas
# começa VERMELHO e vira VERDE com a palavra CONFIRMADO ao receber um clique.
# O visual_query verifica o resultado. Abre o Chromium. 2–4 min.
# Pré-requisito: modelo multimodal no perfil [llm.vision] do config.toml.
cd "$(dirname "$0")/../.." || exit 1

mkdir -p workspace
cat > workspace/canvas-teste.html <<'HTML'
<!DOCTYPE html>
<html><body style="margin:0">
<canvas id="c" width="800" height="500"></canvas>
<script>
  const ctx = document.getElementById('c').getContext('2d');
  const draw = (cor, msg) => {
    ctx.fillStyle = cor; ctx.fillRect(0, 0, 800, 500);
    ctx.fillStyle = '#fff'; ctx.font = 'bold 48px sans-serif';
    ctx.fillText(msg, 200, 260);
  };
  draw('#c0392b', 'CLIQUE AQUI');
  document.getElementById('c').addEventListener('mousedown',
    () => draw('#27ae60', 'CONFIRMADO'));
</script>
</body></html>
HTML

.venv/bin/python main.py --max-steps 6 --prompt "Execute EXATAMENTE estes 4 passos, um por vez:
1. browser_use com action go_to_url e url file://$(pwd)/workspace/canvas-teste.html
2. browser_use com action click_coordinates com x 400 e y 250
3. browser_use com action visual_query e goal 'Qual a cor de fundo e qual palavra está escrita na tela? Responda exatamente.'
4. terminate com status success
Não use click_element (o canvas não aparece na árvore DOM), não use extract_content."
