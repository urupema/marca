#!/usr/bin/env bash
# Renderiza as aplicações admitidas no livro a partir dos modelos em docs/modelos.
# Uso: bash ferramentas/renderizar_aplicacoes.sh   (na raiz do repositório)
set -euo pipefail
M=docs/modelos; S=docs/aplicacoes; R="node ferramentas/render.mjs"
mkdir -p "$S"
$R $M/proposta.html .pagina        $S/proposta 1000 1200 1.6
$R $M/relatorio.html .pagina       $S/relatorio 1000 1200 1.6
$R $M/forja-evidencia.html viewport $S/forja-evidencia 1440 780 1.5
$R $M/infra-painel.html viewport   $S/infra-painel 1440 690 1.5
$R $M/site-home.html viewport      $S/site-home 1440 900 1.5
$R $M/site-home.html viewport      $S/site-celular 390 844 2
$R $M/formacao.html viewport       $S/formacao-celular 390 844 2
$R $M/certificado.html .pagina     $S/certificado 1200 900 1.6
$R $M/apresentacao.html .slide     $S/apresentacao 2000 1200 0.8
$R $M/card-social.html .card       $S/card-social 1300 1400 1
$R $M/coassinatura.html .quadro    $S/coassinatura 1600 900 1.2
$R $M/cracha.html .cracha          $S/cracha 400 500 4
$R $M/assinatura-email.html body   $S/assinatura-email 640 300 2
# PNG → JPEG de alta qualidade para peso de página
python3 - <<'PY'
from pathlib import Path
from PIL import Image
for p in Path("docs/aplicacoes").glob("*.png"):
    im = Image.open(p).convert("RGB")
    if p.stem.split("-")[0] in ("proposta", "relatorio", "certificado", "apresentacao", "card", "cracha"):
        im = im.crop((2, 2, im.width - 2, im.height - 2))  # tira a borda de antisserrilhado do quadro
    im.save(p.with_suffix(".jpg"), quality=90, optimize=True, progressive=True)
    p.unlink()
PY
