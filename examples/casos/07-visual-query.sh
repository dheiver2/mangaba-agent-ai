#!/usr/bin/env bash
# Case híbrido: visual_query — o agente "olha" a página renderizada (screenshot →
# [llm.vision]) e responde uma pergunta sobre ela. Útil quando o DOM não conta a
# história toda (layout, banners, estado visual). Abre o Chromium. 2–4 min.
# Pré-requisito: modelo multimodal no perfil [llm.vision] do config.toml.
cd "$(dirname "$0")/../.." || exit 1

.venv/bin/python main.py --max-steps 6 --prompt "Execute EXATAMENTE estes 4 passos, um por vez:
1. browser_use com action go_to_url e url https://www.wikipedia.org
2. browser_use com action visual_query e goal 'Descreva o que aparece no centro da página: logotipo, idiomas listados e onde fica a caixa de busca'
3. str_replace_editor com command create, path workspace/visual-query-wikipedia.md e file_text contendo a descrição do passo 2
4. terminate com status success
Não role a página, não clique em nada, não use extract_content."
