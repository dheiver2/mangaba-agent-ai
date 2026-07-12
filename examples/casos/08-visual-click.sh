#!/usr/bin/env bash
# Case híbrido: visual_click — clicar num elemento descrito em linguagem natural,
# sem índice DOM. O modelo de visão localiza o alvo no screenshot e devolve as
# coordenadas; o clique é feito pelo mouse do Playwright. Abre o Chromium. 2–4 min.
# Pré-requisito: modelo multimodal no perfil [llm.vision] do config.toml.
cd "$(dirname "$0")/../.." || exit 1

.venv/bin/python main.py --max-steps 8 --prompt "Execute EXATAMENTE estes 5 passos, um por vez:
1. browser_use com action go_to_url e url https://www.wikipedia.org
2. browser_use com action visual_click e goal 'o link do idioma Português na lista ao redor do logotipo'
3. browser_use com action wait e seconds 3
4. browser_use com action visual_query e goal 'Qual é o título principal da página agora? Estamos na Wikipédia em português?'
5. terminate com status success
Não use click_element nem índices DOM — o objetivo é testar o clique por visão."
