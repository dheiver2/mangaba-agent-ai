#!/usr/bin/env bash
# Case híbrido: drag_coordinates em mapa — tiles do OpenStreetMap não são elementos
# DOM clicáveis; pan de mapa só funciona com arrasto por coordenada (com passos
# intermediários, senão o mapa ignora o movimento). Abre o Chromium. 3–5 min.
# Pré-requisito: modelo multimodal no perfil [llm.vision] do config.toml.
cd "$(dirname "$0")/../.." || exit 1

.venv/bin/python main.py --max-steps 8 --prompt "Execute EXATAMENTE estes 6 passos, um por vez:
1. browser_use com action go_to_url e url https://www.openstreetmap.org/#map=13/-9.4906/-35.8317
2. browser_use com action wait e seconds 4
3. browser_use com action visual_query e goal 'Que cidade ou região aparece no centro do mapa?'
4. browser_use com action drag_coordinates com x 640, y 300, x2 340 e y2 300
5. browser_use com action visual_query e goal 'O mapa se deslocou para leste? Que região aparece agora no centro?'
6. terminate com status success
Não clique em nada, não use click_element, não role a página."
