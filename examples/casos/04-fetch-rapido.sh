#!/usr/bin/env bash
# Case rápido: mesma extração do 03, mas com fetch_url (sem navegador). ~1 min.
cd "$(dirname "$0")/../.." || exit 1

.venv/bin/python main.py --max-steps 6 --prompt "Execute EXATAMENTE estes 3 passos, um por vez:
1. fetch_url com url https://news.ycombinator.com
2. str_replace_editor com command create, path workspace/hn-rapido.md e file_text contendo os títulos das 10 primeiras notícias encontradas no conteúdo do passo 1
3. terminate com status success
Não use browser_use nem python_execute."
