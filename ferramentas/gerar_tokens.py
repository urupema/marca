"""Gera docs/cores/tokens.css e tokens.json a partir do contrato.

O contrato é a fonte; estes arquivos nunca são editados à mão.
Uso: python3 ferramentas/gerar_tokens.py
"""
import json
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
contrato = json.loads((RAIZ / "contrato" / "brand-spec.json").read_text())
tokens = contrato["visual"]["tokens"]


def achatar(no, prefixo=()):
    for chave, valor in no.items():
        if isinstance(valor, dict) and "$value" in valor:
            yield prefixo + (chave,), valor
        elif isinstance(valor, dict):
            yield from achatar(valor, prefixo + (chave,))


def resolver(valor):
    m = re.fullmatch(r"\{(.+)\}", valor)
    if not m:
        return valor
    no = tokens
    for parte in m.group(1).split("."):
        no = no[parte]
    return resolver(no["$value"])


def var(caminho):
    return "--" + "-".join(caminho).replace("_", "-")


linhas = []
for caminho, t in achatar(tokens):
    nome = f"  /* {t['name']} */" if "name" in t else ""
    linhas.append(f"  {var(caminho)}: {resolver(t['$value'])};{nome}")

css = f"""/* Instituto Urupema — tokens de marca. Gerado a partir do contrato; não editar à mão. */
@font-face {{ font-family: "Newsreader"; src: url("../fontes/Newsreader-Variavel.woff2") format("woff2-variations"); font-weight: 200 800; font-style: normal; font-display: swap; }}
@font-face {{ font-family: "Newsreader"; src: url("../fontes/Newsreader-Variavel-Italico.woff2") format("woff2-variations"); font-weight: 200 800; font-style: italic; font-display: swap; }}
@font-face {{ font-family: "Space Grotesk"; src: url("../fontes/SpaceGrotesk-Variavel.woff2") format("woff2-variations"); font-weight: 300 700; font-style: normal; font-display: swap; }}

:root {{
{chr(10).join(linhas)}
  --fonte-institucional: "Newsreader", Georgia, serif;
  --fonte-sistema: "Space Grotesk", Arial, sans-serif;

  /* papéis em uso: trocam juntos no modo escuro */
  --papel-fundo: var(--color-fundo);
  --papel-superficie: var(--color-superficie);
  --papel-texto: var(--color-texto);
  --papel-texto-secundario: var(--color-texto-secundario);
  --papel-decisao: var(--color-decisao);
  --papel-decisao-texto: var(--color-decisao-texto);
  --papel-filete: var(--color-superficie);
  --papel-filete-forte: var(--color-filete-forte);
  --papel-simbolo: var(--color-texto);
}}

.escuro, [data-tema="escuro"] {{
  --papel-fundo: var(--color-escuro-fundo);
  --papel-superficie: var(--color-escuro-superficie);
  --papel-texto: var(--color-escuro-texto);
  --papel-texto-secundario: var(--color-escuro-texto-secundario);
  --papel-decisao-texto: var(--color-escuro-decisao-texto);
  --papel-filete: var(--color-escuro-filete);
  --papel-filete-forte: var(--color-escuro-filete-forte);
  --papel-simbolo: var(--color-escuro-texto);
  --color-estado-correto: var(--color-estado-correto-escuro);
  --color-estado-atencao: var(--color-estado-atencao-escuro);
  --color-estado-falha: var(--color-estado-falha-escuro);
}}
"""
(RAIZ / "docs" / "cores").mkdir(parents=True, exist_ok=True)
(RAIZ / "docs" / "cores" / "tokens.css").write_text(css)
(RAIZ / "docs" / "cores" / "tokens.json").write_text(json.dumps(tokens, ensure_ascii=False, indent=2) + "\n")
print("tokens.css e tokens.json gerados")
