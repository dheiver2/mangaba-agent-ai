#!/usr/bin/env bash
# Case multimodal: transcreve áudio e gera ata. ~1-2 min.
# Gere um áudio de teste antes (macOS):
#   say -v Luciana -o workspace/reuniao.wav --data-format=LEI16@16000 "Sua fala aqui"
# Para imagens, troque o passo 1 por:
#   describe_image com image_path workspace/foto.png e prompt 'sua pergunta'
cd "$(dirname "$0")/../.." || exit 1

.venv/bin/python main.py --max-steps 6 --prompt "Execute EXATAMENTE estes 3 passos, um por vez:
1. transcribe_audio com audio_path workspace/reuniao.wav
2. str_replace_editor com command create, path workspace/ata.md e file_text contendo a transcrição do passo 1 formatada como ata breve
3. terminate com status success
Não use outras ferramentas."
