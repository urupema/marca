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
  --papel-fundo: var(--color-background);
  --papel-superficie: var(--color-surface);
  --papel-texto: var(--color-text);
  --papel-texto-secundario: var(--color-text-secondary);
  --papel-decisao: var(--color-decision);
  --papel-decisao-texto: var(--color-decision-text);
  --papel-filete: var(--color-surface);
  --papel-filete-forte: var(--color-rule-strong);
  --papel-simbolo: var(--color-text);
}}

.escuro, [data-tema="escuro"] {{
  --papel-fundo: var(--color-dark-background);
  --papel-superficie: var(--color-dark-surface);
  --papel-texto: var(--color-dark-text);
  --papel-texto-secundario: var(--color-dark-text-secondary);
  --papel-decisao-texto: var(--color-dark-decision-text);
  --papel-filete: var(--color-dark-rule);
  --papel-filete-forte: var(--color-dark-rule-strong);
  --papel-simbolo: var(--color-dark-text);
  --color-state-ok: var(--color-state-ok-dark);
  --color-state-warning: var(--color-state-warning-dark);
  --color-state-failure: var(--color-state-failure-dark);
}}
"""
(RAIZ / "docs" / "cores").mkdir(parents=True, exist_ok=True)
(RAIZ / "docs" / "cores" / "tokens.css").write_text(css)
(RAIZ / "docs" / "cores" / "tokens.json").write_text(json.dumps(tokens, ensure_ascii=False, indent=2) + "\n")
print("tokens.css e tokens.json gerados")
