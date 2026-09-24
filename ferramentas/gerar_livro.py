"""Gera docs/index.html, o livro da marca, a partir do contrato e da pasta docs/.

Valores, tabelas e a lista de arquivos vêm do contrato e dos próprios arquivos;
nada é redigitado. Fontes embutidas; sem scripts; sem requisições externas.
Uso: python3 ferramentas/gerar_livro.py
"""
import base64
import html
import json
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
LIVRO = RAIZ / "docs"
C = json.loads((RAIZ / "contrato" / "brand-spec.json").read_text())
sys.path.insert(0, "/root/.claude/plugins/cache/enniolopes/branding-studio/3.1.0/scripts")
try:
    from color_tools import wcag_ratio
except ImportError:  # cálculo WCAG 2.x local, idêntico
    def _l(h):
        c = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
        c = [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
        return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]

    def wcag_ratio(a, b):
        x, y = sorted([_l(a), _l(b)], reverse=True)
        return (x + 0.05) / (y + 0.05)

T = C["visual"]["tokens"]["color"]
e = html.escape


def resolver(ref):
    m = re.fullmatch(r"\{color\.(.+)\}", ref)
    if not m:
        return ref
    no = T
    for p in m.group(1).split("."):
        no = no[p]
    return resolver(no["$value"])


def token(ref):
    m = re.fullmatch(r"\{color\.(.+)\}", ref)
    no = T
    for p in m.group(1).split("."):
        no = no[p]
    return no


def fonte64(nome):
    return base64.b64encode((LIVRO / "fontes" / nome).read_bytes()).decode()


def titulo_arquivo(p):
    txt = p.read_text(errors="ignore") if p.suffix in (".svg", ".html") else ""
    m = re.search(r"<title[^>]*>(.*?)</title>", txt, re.S)
    if m:
        return html.unescape(m.group(1)).strip()
    nomes = {
        "tokens.css": "Variáveis de cor, espaço e fontes para CSS",
        "tokens.json": "Variáveis de cor, espaço e raio em JSON (formato de tokens de design)",
        "componentes.css": "Componentes de marca para os modelos em HTML",
        "OFL-Newsreader.txt": "Licença SIL OFL 1.1 — Newsreader",
        "OFL-SpaceGrotesk.txt": "Licença SIL OFL 1.1 — Space Grotesk",
        "Newsreader-Variavel.woff2": "Newsreader, variável, redonda",
        "Newsreader-Variavel-Italico.woff2": "Newsreader, variável, itálica",
        "SpaceGrotesk-Variavel.woff2": "Space Grotesk, variável",
    }
    if p.name in nomes:
        return nomes[p.name]
    base = p.stem.replace("-", " ")
    return base[:1].upper() + base[1:]


# ---------------------------------------------------------------- tabelas derivadas
def linhas_cor(grupo, chaves):
    out = []
    for k in chaves:
        t = grupo[k]
        hexv = resolver(t["$value"])
        out.append((t.get("name", k), hexv))
    return out


nucleo = linhas_cor(T, ["fundo", "superficie", "texto", "decisao"])
funcionais = linhas_cor(T, ["texto_secundario", "decisao_texto", "filete_forte", "papel"])
escuro = linhas_cor(T["escuro"], ["superficie", "filete", "texto_secundario", "decisao_texto", "filete_forte"])
estados = linhas_cor(T["estado"], ["correto", "atencao", "falha", "correto_escuro", "atencao_escuro", "falha_escuro"])
papeis_cor = {
    "Palha": "fundo institucional dominante",
    "Areia": "superfícies secundárias, filetes, campo do símbolo em escala",
    "Tinta": "texto, símbolo e fundos escuros",
    "Urucum": "a decisão: uma vez por composição",
    "Tinta reduzida": "texto secundário sobre Palha, Areia e branco",
    "Urucum texto": "texto em Urucum, só sobre Palha ou branco",
    "Filete forte": "bordas de campos, botões e controles",
    "Branco papel": "documentos impressos e superfícies de produto",
    "Tinta elevada": "superfície sobre fundo Tinta",
    "Filete escuro": "filetes sobre fundo Tinta",
    "Palha reduzida": "texto secundário sobre Tinta",
    "Urucum texto sobre Tinta": "chamada ou estado em 16 px ou mais, peso 500 ou mais",
    "Filete forte escuro": "bordas de controles sobre Tinta",
}

pares = []
for p in C["visual"]["contrast_pairs"]:
    tt, bt = token(p["text"]), token(p["background"])
    fg, bg = resolver(p["text"]), resolver(p["background"])
    uso = {"body": "texto", "large": "texto grande", "ui": "bordas e formas"}[p["usage"]]
    pares.append((tt.get("name"), fg, bt.get("name"), bg, uso, wcag_ratio(fg, bg)))


def fmt(x):
    return f"{x:.2f}".replace(".", ",")


# ---------------------------------------------------------------- arquivos
GRUPOS = [
    ("logo", "Símbolo, assinaturas, carimbo e ícones"),
    ("cores", "Cores e variáveis"),
    ("fontes", "Fontes e licenças"),
    ("modelos", "Modelos editáveis em HTML"),
    ("fotografia", "Fotografia"),
    ("aplicacoes", "Aplicações de referência"),
]


def lista_arquivos():
    blocos = []
    for pasta, rotulo in GRUPOS:
        itens = sorted((LIVRO / pasta).iterdir())
        lis = "".join(
            f'<li><a href="{pasta}/{e(p.name)}" download>{e(titulo_arquivo(p))}</a>'
            f'<span>{e(p.name)}</span></li>' for p in itens if p.is_file())
        blocos.append(f'<section class="grupo-arquivos"><h3>{e(rotulo)}</h3><ul>{lis}</ul></section>')
    return "".join(blocos)


# ---------------------------------------------------------------- peças
def fig(src, alt, legenda, classe=""):
    return (f'<figure class="{classe}"><img src="{src}" alt="{e(alt)}">'
            f'<figcaption>{legenda}</figcaption></figure>')


def regra(titulo, faca, porque, variacao=""):
    v = f'<p class="variacao"><span>Variação</span>{variacao}</p>' if variacao else ""
    return (f'<div class="regra"><h4>{titulo}</h4><p class="faca">{faca}</p>'
            f'<p class="porque"><span>Por quê</span>{porque}</p>{v}</div>')


def tabela(cabecas, linhas, classe=""):
    th = "".join(f"<th>{c}</th>" for c in cabecas)
    trs = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in l) + "</tr>" for l in linhas)
    return f'<table class="{classe}"><thead><tr>{th}</tr></thead><tbody>{trs}</tbody></table>'


def amostra(nome, hexv, papel, escura=False):
    cor_txt = "#F6F1E7" if escura else "#221F1A"
    return (f'<div class="amostra" style="background:{hexv};color:{cor_txt}">'
            f'<b>{e(nome)}</b><span class="dado">{hexv}</span><span>{e(papel)}</span></div>')


V = C["verbal"]
S = C["strategy"]
D = C["creative_direction"]
L = C["visual"]["logo"]
TY = C["visual"]["typography"]
A = C["architecture"]
G = C["governance"]

css = f"""
@font-face {{ font-family: "Newsreader"; src: url(data:font/woff2;base64,{fonte64('Newsreader-Variavel.woff2')}) format("woff2"); font-weight: 200 800; font-style: normal; }}
@font-face {{ font-family: "Newsreader"; src: url(data:font/woff2;base64,{fonte64('Newsreader-Variavel-Italico.woff2')}) format("woff2"); font-weight: 200 800; font-style: italic; }}
@font-face {{ font-family: "Space Grotesk"; src: url(data:font/woff2;base64,{fonte64('SpaceGrotesk-Variavel.woff2')}) format("woff2"); font-weight: 300 700; }}
:root {{
  --palha: #F6F1E7; --areia: #E7DFD0; --tinta: #221F1A; --urucum: #B4602F;
  --reduzida: #686157; --urucum-texto: #A85626; --filete-forte: #8E887F;
  --tinta-elevada: #2D2A24; --filete-escuro: #3B3731; --palha-reduzida: #BCB8AE;
  --inst: "Newsreader", Georgia, serif; --sis: "Space Grotesk", Arial, sans-serif;
  --m: clamp(20px, 6.6vw, 96px);
}}
* {{ box-sizing: border-box; }}
html {{ -webkit-font-smoothing: antialiased; scroll-behavior: smooth; }}
body {{ margin: 0; background: var(--palha); color: var(--tinta); font: 400 17px/1.55 var(--sis); }}
a {{ color: inherit; text-underline-offset: 3px; text-decoration-thickness: 1px; }}
img {{ max-width: 100%; display: block; }}
.dado {{ font-variant-numeric: tabular-nums; }}
.rotulo {{ font: 500 12px/1.3 var(--sis); letter-spacing: .09em; text-transform: uppercase; color: var(--reduzida); margin: 0; }}
.escuro {{ background: var(--tinta); color: var(--palha); }}
.escuro .rotulo {{ color: var(--palha-reduzida); }}
h1, h2, h3 {{ font-family: var(--inst); font-weight: 400; font-variation-settings: "opsz" 72; margin: 0; letter-spacing: -.012em; text-wrap: balance; }}
h4 {{ font: 600 17px/1.3 var(--sis); margin: 0 0 8px; }}
p {{ margin: 0 0 14px; max-width: 66ch; }}

/* capa */
.capa {{ position: relative; overflow: hidden; min-height: 100vh; padding: 40px var(--m) 48px; display: flex; flex-direction: column; }}
.capa .campo {{ position: absolute; width: min(1100px, 120vw); right: -18%; top: 8%; }}
.capa > :not(.campo) {{ position: relative; }}
.capa .marca {{ height: 64px; width: auto; margin: -16px 0 0 -20px; align-self: flex-start; }}
.capa h1 {{ font-size: clamp(64px, 11vw, 176px); line-height: .9; margin-top: auto; max-width: 7em; letter-spacing: -.024em; }}
.capa .sub {{ font-size: 20px; margin: 32px 0 56px; max-width: 32em; color: var(--palha-reduzida); }}
.indice {{ display: grid; grid-template-columns: repeat(4, minmax(0,1fr)); column-gap: 24px; border-top: 1px solid var(--palha); padding-top: 14px; list-style: none; margin: 0; padding-left: 0; counter-reset: s; }}
.indice li {{ font-size: 15px; padding: 3px 0; }}
.indice a {{ text-decoration: none; }}
.indice span {{ font-variant-numeric: tabular-nums; color: var(--palha-reduzida); display: inline-block; width: 2.2em; }}

/* seções */
section.s {{ padding: 120px var(--m) 96px; border-top: 1px solid var(--areia); }}
.s-cab {{ display: grid; grid-template-columns: repeat(12, minmax(0,1fr)); column-gap: 24px; margin-bottom: 64px; }}
.s-cab .rotulo {{ grid-column: 1 / 4; padding-top: 18px; }}
.s-cab h2 {{ grid-column: 4 / 13; font-size: clamp(44px, 5.6vw, 84px); line-height: 1; }}
.s-cab .abre {{ grid-column: 4 / 11; font-size: 20px; line-height: 1.5; margin-top: 28px; }}
.corpo-s {{ display: grid; grid-template-columns: repeat(12, minmax(0,1fr)); column-gap: 24px; row-gap: 56px; }}
.col-cheia {{ grid-column: 1 / -1; }}
.col-texto {{ grid-column: 4 / 11; }}
.col-esq {{ grid-column: 1 / 7; }}
.col-dir {{ grid-column: 7 / 13; }}
.regras {{ grid-column: 4 / 13; display: grid; grid-template-columns: repeat(2, minmax(0,1fr)); column-gap: 48px; row-gap: 40px; }}
.regra {{ border-top: 1px solid var(--tinta); padding-top: 14px; }}
.regra .faca {{ font-size: 17px; margin-bottom: 10px; }}
.regra .porque, .regra .variacao {{ font-size: 14.5px; color: var(--reduzida); margin-bottom: 8px; }}
.regra .porque span, .regra .variacao span {{ display: block; font: 500 11px/1.3 var(--sis); letter-spacing: .09em; text-transform: uppercase; margin-bottom: 2px; }}

/* explicação */
.tese {{ font-family: var(--inst); font-size: clamp(56px, 9vw, 150px); line-height: .92; letter-spacing: -.024em; font-variation-settings: "opsz" 72; margin: 0; max-width: 8.5em; }}
.cadeia {{ grid-column: 1 / -1; display: grid; grid-template-columns: repeat(4, minmax(0,1fr)); column-gap: 24px; }}
.cadeia div {{ border-top: 1px solid var(--tinta); padding-top: 14px; }}
.cadeia p {{ font-size: 16px; }}

/* símbolo */
.painel-simbolo {{ grid-column: 1 / -1; display: grid; grid-template-columns: 1.3fr 1fr; column-gap: 24px; align-items: stretch; }}
.construcao {{ background: #fff; border: 1px solid var(--areia); padding: 48px; }}
.construcao svg {{ width: 100%; height: auto; display: block; }}
.construcao .cota {{ font: 500 11px var(--sis); fill: var(--reduzida); letter-spacing: .06em; }}
.variantes {{ display: grid; grid-template-columns: 1fr 1fr; gap: 0; }}
.variantes figure {{ margin: 0; padding: 36px; display: flex; flex-direction: column; justify-content: space-between; gap: 20px; min-height: 240px; }}
.variantes img {{ width: 44%; }}
.variantes figcaption {{ font-size: 13px; color: inherit; opacity: .85; }}
.fundo-palha {{ background: var(--palha); border: 1px solid var(--areia); }}
.fundo-branco {{ background: #fff; border: 1px solid var(--areia); }}
.fundo-tinta {{ background: var(--tinta); color: var(--palha); }}
.fundo-urucum {{ background: var(--areia); }}
.assinaturas-grade {{ grid-column: 1 / -1; display: grid; grid-template-columns: 1.4fr 1fr 1fr; gap: 24px; align-items: stretch; }}
.assinaturas-grade figure {{ margin: 0; background: #fff; border: 1px solid var(--areia); padding: 32px; display: flex; flex-direction: column; justify-content: space-between; gap: 24px; }}
.assinaturas-grade figure.escura {{ background: var(--tinta); border-color: var(--tinta); color: var(--palha); }}
.assinaturas-grade figcaption {{ font-size: 13px; color: var(--reduzida); }}
.assinaturas-grade figure.escura figcaption {{ color: var(--palha-reduzida); }}
.assinaturas-grade figure.escura figcaption b {{ color: var(--palha); }}
table {{ width: 100%; border-collapse: collapse; font-size: 15px; }}
th {{ text-align: left; font: 500 11px/1.3 var(--sis); letter-spacing: .09em; text-transform: uppercase; color: var(--reduzida); padding: 0 16px 10px 0; border-bottom: 1px solid var(--tinta); }}
td {{ padding: 12px 16px 12px 0; border-bottom: 1px solid var(--areia); vertical-align: top; }}
td .chip {{ display: inline-block; width: 14px; height: 14px; border-radius: 3px; vertical-align: -2px; margin-right: 8px; border: 1px solid rgba(0,0,0,.12); }}

/* cor */
.campo-cor {{ grid-column: 1 / -1; display: grid; grid-template-columns: 62fr 20fr 14fr 4fr; min-height: 380px; }}
.campo-cor > div {{ padding: 24px; display: flex; flex-direction: column; justify-content: flex-end; gap: 4px; font-size: 14px; }}
.campo-cor b {{ font: 400 34px/1 var(--inst); font-variation-settings: "opsz" 48; }}
.amostras {{ display: grid; grid-template-columns: repeat(4, minmax(0,1fr)); gap: 0; }}
.amostra {{ padding: 20px; min-height: 150px; display: flex; flex-direction: column; justify-content: flex-end; gap: 2px; font-size: 13.5px; border: 1px solid rgba(34,31,26,.08); }}
.amostra b {{ font-weight: 600; font-size: 15px; }}

/* tipografia */
.especime {{ grid-column: 1 / -1; display: grid; grid-template-columns: 1fr 1fr; column-gap: 24px; }}
.especime > div {{ border-top: 1px solid var(--tinta); padding-top: 18px; }}
.especime .grande-inst {{ font: 400 176px/.9 var(--inst); font-variation-settings: "opsz" 72; letter-spacing: -.03em; margin: 24px 0 18px; }}
.especime .grande-sis {{ font: 500 176px/.9 var(--sis); letter-spacing: -.04em; margin: 24px 0 18px; }}
.especime .alfabeto {{ font-size: 22px; line-height: 1.35; word-break: break-all; margin: 0 0 12px; max-width: none; }}
.especime .alfabeto.inst {{ font-family: var(--inst); font-variation-settings: "opsz" 24; }}
.hierarquia {{ grid-column: 1 / -1; border-top: 1px solid var(--tinta); }}
.hierarquia > div {{ display: grid; grid-template-columns: 3fr 9fr; column-gap: 24px; padding: 22px 0; border-bottom: 1px solid var(--areia); align-items: baseline; }}
.hierarquia .nome-papel {{ font-size: 14px; }}
.hierarquia .nome-papel span {{ display: block; color: var(--reduzida); font-size: 13px; margin-top: 4px; }}

/* gramática */
.dispositivos {{ grid-column: 1 / -1; display: grid; grid-template-columns: repeat(2, minmax(0,1fr)); column-gap: 24px; row-gap: 56px; }}
.dispositivo .visual {{ background: #fff; border: 1px solid var(--areia); height: 280px; position: relative; overflow: hidden; margin-bottom: 20px; }}
.barra {{ display: inline-block; width: 57px; height: 24px; border-radius: 99px; background: var(--urucum); }}
.reg-demo {{ position: absolute; left: 40px; right: 40px; bottom: 40px; display: grid; grid-template-columns: repeat(4, auto); justify-content: start; column-gap: 36px; border-top: 1px solid var(--tinta); padding-top: 12px; }}
.reg-demo span {{ display: block; font: 500 10.5px var(--sis); letter-spacing: .09em; text-transform: uppercase; color: var(--reduzida); }}
.reg-demo b {{ font-weight: 400; font-size: 14px; font-variant-numeric: tabular-nums; }}

/* falhas */
.falhas {{ grid-column: 1 / -1; display: grid; grid-template-columns: repeat(3, minmax(0,1fr)); column-gap: 24px; row-gap: 48px; }}
.falha .quadro {{ height: 220px; border: 1px solid var(--areia); background: #fff; position: relative; overflow: hidden; margin-bottom: 16px; }}
.falha h4::before {{ content: "Não: "; color: var(--reduzida); font-weight: 500; }}
.falha p {{ font-size: 15px; }}

/* fotografia */
.fotos {{ grid-column: 1 / -1; display: grid; grid-template-columns: repeat(2, minmax(0,1fr)); column-gap: 24px; row-gap: 40px; }}
.fotos figure {{ margin: 0; }}
.fotos .f-grande {{ grid-column: 1 / -1; }}
.fotos img {{ width: 100%; aspect-ratio: 3 / 2; object-fit: cover; }}
.fotos .f-grande img {{ aspect-ratio: 21 / 9; object-position: 50% 8%; }}

/* aplicações */
.aplic {{ padding: 120px var(--m) 96px; border-top: 1px solid var(--areia); }}
.aplic .par {{ display: grid; grid-template-columns: 1fr 1fr; column-gap: 24px; margin-bottom: 72px; align-items: start; }}
.aplic figure {{ margin: 0; }}
.aplic figure img {{ width: 100%; box-shadow: 0 0 0 1px rgba(34,31,26,.08); }}
figcaption {{ font-size: 14px; color: var(--reduzida); margin-top: 12px; max-width: 60ch; }}
figcaption b {{ color: var(--tinta); font-weight: 600; }}
.aplic .inteira {{ margin-bottom: 72px; }}
.aplic .tres {{ display: grid; grid-template-columns: 1fr 1fr 1fr; column-gap: 24px; margin-bottom: 72px; align-items: start; }}
.aplic .celular {{ display: grid; grid-template-columns: 1fr 1fr 2fr; column-gap: 24px; margin-bottom: 72px; align-items: start; }}

/* linguagem */
.frases {{ grid-column: 1 / -1; display: grid; grid-template-columns: 1fr 1fr; column-gap: 24px; }}
.frases > div {{ border-top: 1px solid var(--tinta); padding-top: 16px; }}
.frases .grande {{ font: 400 52px/1.02 var(--inst); font-variation-settings: "opsz" 72; letter-spacing: -.015em; margin: 16px 0 16px; }}
.antes-depois {{ grid-column: 1 / -1; border-top: 1px solid var(--tinta); }}
.antes-depois > div {{ display: grid; grid-template-columns: 3fr 4.5fr 4.5fr; column-gap: 24px; padding: 20px 0; border-bottom: 1px solid var(--areia); }}
.antes-depois .nao {{ color: var(--reduzida); text-decoration: line-through; text-decoration-thickness: 1px; }}
.antes-depois .sim {{ font-weight: 500; }}
.vocab {{ display: flex; flex-wrap: wrap; gap: 8px 24px; margin: 0; padding: 0; list-style: none; font-size: 16px; }}
.boiler {{ font-size: 17px; border-left: 1px solid var(--tinta); padding-left: 20px; }}

/* arquitetura */
.decisao-nome {{ grid-column: 1 / -1; display: grid; grid-template-columns: repeat(4, minmax(0,1fr)); column-gap: 24px; }}
.decisao-nome > div {{ border-top: 1px solid var(--tinta); padding-top: 14px; }}
.decisao-nome .ex {{ font-size: 14px; color: var(--reduzida); }}

/* arquivos */
.arquivos {{ grid-column: 1 / -1; display: grid; grid-template-columns: repeat(2, minmax(0,1fr)); column-gap: 48px; row-gap: 48px; }}
.grupo-arquivos h3 {{ font: 500 26px/1.1 var(--inst); font-variation-settings: "opsz" 36; margin-bottom: 14px; }}
.grupo-arquivos ul {{ list-style: none; margin: 0; padding: 0; border-top: 1px solid var(--tinta); }}
.grupo-arquivos li {{ display: grid; grid-template-columns: 1fr auto; column-gap: 16px; padding: 9px 0; border-bottom: 1px solid var(--areia); font-size: 14.5px; }}
.grupo-arquivos li span {{ font-size: 12.5px; color: var(--reduzida); font-variant-numeric: tabular-nums; }}

footer.fim {{ padding: 72px var(--m) 56px; display: grid; grid-template-columns: repeat(12, minmax(0,1fr)); column-gap: 24px; }}
footer.fim img {{ grid-column: 1 / 4; height: 64px; width: auto; margin: -16px 0 0 -20px; }}
footer.fim p {{ grid-column: 5 / 12; font-size: 15px; color: var(--palha-reduzida); }}

@media (max-width: 900px) {{
  .s-cab, .corpo-s {{ display: block; }}
  .s-cab h2 {{ margin-top: 12px; }}
  .corpo-s > * + * {{ margin-top: 48px; }}
  .fotos, .regras, .cadeia, .painel-simbolo, .assinaturas-grade, .especime, .dispositivos, .falhas, .frases, .decisao-nome, .arquivos, .aplic .par, .aplic .tres, .aplic .celular, .indice {{ grid-template-columns: 1fr; row-gap: 32px; }}
  .amostras {{ grid-template-columns: 1fr 1fr; }}
  .campo-cor {{ min-height: 240px; }}
  .campo-cor b {{ font-size: 22px; }}
  .especime .grande-inst, .especime .grande-sis {{ font-size: 110px; }}
  .hierarquia > div, .antes-depois > div {{ grid-template-columns: 1fr; row-gap: 6px; }}
  .capa .campo {{ width: 118vw; right: auto; left: 22vw; top: 40px; }}
  .capa h1 {{ margin-top: 380px; }}
  section.s, .aplic {{ padding-top: 72px; padding-bottom: 56px; }}
  table {{ font-size: 13.5px; }}
  .variantes figure {{ min-height: 180px; padding: 24px; }}
  footer.fim {{ display: block; }}
  footer.fim p {{ margin-top: 24px; }}
}}
@media print {{
  @page {{ size: A4; margin: 14mm 14mm 16mm; }}
  body {{ font-size: 10pt; background: #fff; -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
  .construcao, .dispositivo .visual, .falha .quadro, .assinaturas-grade figure {{ border-color: var(--areia); }}
  @page :first {{ margin: 0; }}
  .capa {{ height: 297mm; min-height: 0; page-break-after: always; padding: 16mm 16mm 14mm; }}
  .capa .campo {{ width: 200mm; right: -60mm; top: -8mm; }}
  .capa h1 {{ font-size: 64pt; }}
  .capa .sub {{ font-size: 12pt; margin: 8mm 0 12mm; }}
  .indice {{ grid-template-columns: repeat(3, 1fr); }}
  .indice li {{ font-size: 9pt; }}
  section.s, .aplic {{ padding: 0; border: 0; page-break-before: always; }}
  .s-cab {{ margin-bottom: 10mm; }}
  .s-cab h2 {{ font-size: 34pt; }}
  .regra, .falha, figure, .dispositivo, tr, .grupo-arquivos li {{ break-inside: avoid; }}
  .aplic .par, .aplic .tres, .aplic .celular {{ margin-bottom: 10mm; }}
  a {{ text-decoration: none; }}
  .indice a::after {{ content: ""; }}
}}
"""

SECOES = [
    ("porque", "Por que a marca é assim"),
    ("simbolo", "Símbolo e assinaturas"),
    ("cor", "Cor"),
    ("tipografia", "Tipografia"),
    ("gramatica", "Gramática"),
    ("urucum", "Uma decisão em Urucum"),
    ("aplicacoes", "Aplicações"),
    ("linguagem", "Linguagem"),
    ("arquitetura", "Produtos e parceiros"),
    ("selo", "Selo e carimbo"),
    ("imagem", "Imagem, ícones, dados e movimento"),
    ("decide", "Quem decide"),
    ("arquivos", "Arquivos"),
]
indice = "".join(f'<li><a href="#{k}"><span>{i:02d}</span>{t}</a></li>' for i, (k, t) in enumerate(SECOES, 1))


def cab(n, chave, titulo, abre=""):
    a = f'<p class="abre">{abre}</p>' if abre else ""
    return f'<div class="s-cab"><p class="rotulo">{n:02d} · {dict(SECOES)[chave]}</p><h2>{titulo}</h2>{a}</div>'


def regras_de(lista):
    return "".join(f'<div class="regra"><p class="faca">{e(r)}</p></div>' for r in lista)


# construção do símbolo, desenhada a partir da mesma geometria dos masters
BARRAS = [(0, 23.5, 81, 34), (125.5, 0, 34, 81), (204, 23.5, 81, 34), (23.5, 102, 34, 81), (102, 125.5, 81, 34),
          (227.5, 102, 34, 81), (0, 227.5, 81, 34), (125.5, 204, 34, 81), (204, 227.5, 81, 34)]
m = 95
guias = "".join(f'<line x1="{m + x}" y1="0" x2="{m + x}" y2="{285 + 2 * m}" stroke="#E7DFD0" stroke-width="1"/>' for x in (0, 95, 190, 285))
guias += "".join(f'<line x1="0" y1="{m + y}" x2="{285 + 2 * m}" y2="{m + y}" stroke="#E7DFD0" stroke-width="1"/>' for y in (0, 95, 190, 285))
barras_svg = "".join(
    f'<rect x="{m + x}" y="{m + y}" width="{w}" height="{h}" rx="17" fill="{"#B4602F" if i == 4 else "#221F1A"}"/>'
    for i, (x, y, w, h) in enumerate(BARRAS))
construcao = f'''<svg viewBox="0 0 {285 + 2 * m} {285 + 2 * m}" role="img" aria-label="Construção do símbolo: malha de três por três células, barras de 81 por 34 unidades com raio 17, alternando horizontais e verticais; a barra central, horizontal, em Urucum; respiro de uma célula em volta.">
<rect x="0.5" y="0.5" width="{285 + 2 * m - 1}" height="{285 + 2 * m - 1}" fill="none" stroke="#8E887F" stroke-dasharray="4 4"/>
{guias}{barras_svg}
<text x="{m + 4}" y="{m - 10}" class="cota">1 CÉLULA = 1/3 DO SÍMBOLO</text>
<text x="{m + 4}" y="{285 + m + 22}" class="cota">BARRA 81 × 34 · RAIO 17</text>
<text x="10" y="18" class="cota">RESPIRO: 1 CÉLULA</text>
</svg>'''


def mini(simbolo, fundo, extra=""):
    return f'<div class="quadro" style="background:{fundo}">{extra}{simbolo}</div>'


falhas = [
    ("Duas decisões em Urucum",
     '<div style="position:absolute;left:28px;top:28px;right:28px"><span class="barra"></span><p style="font:400 30px/1.05 var(--inst);margin:18px 0 0;color:#A85626">Três frentes</p><p style="font-size:13px;margin:10px 0 0;color:#A85626">01 · 02 · 03</p></div>',
     "Quando tudo é decisão, nada é. O leitor perde o ponto para onde a peça quer levá-lo. Escolha o único elemento que pede ação ou decide; o resto fica em Tinta."),
    ("Urucum como campo",
     '<div style="position:absolute;inset:0;background:#B4602F"></div><p style="position:absolute;left:28px;bottom:24px;font:400 30px/1.05 var(--inst);color:#F6F1E7;margin:0">Refinar tecnologia</p>',
     "O Urucum em área grande vira clima laranja e aproxima a marca de centros de inovação que já usam laranja como campo. Ele perde a função de sinal. Campo é Palha, branco ou Tinta."),
    ("Símbolo girado, espelhado ou reordenado",
     '<img src="logo/simbolo.svg" alt="" style="position:absolute;width:120px;left:50%;top:50%;margin:-60px 0 0 -60px;transform:rotate(90deg)">',
     "Girado, o centro vira vertical e a alternância das barras se inverte: é outro desenho. A malha só é reconhecível na posição do master."),
    ("Símbolo como textura",
     '<div style="position:absolute;inset:-10px;background-image:url(logo/simbolo-mono.svg);background-size:54px;opacity:.16"></div>',
     "Repetido, o símbolo deixa de assinar e vira papel de parede; também dilui a raridade que faz dele uma marca. Use-o uma vez, no máximo em escala de campo."),
    ("Cadeado para dizer soberania",
     '<svg viewBox="0 0 120 120" style="position:absolute;width:96px;left:50%;top:50%;margin:-48px 0 0 -48px"><rect x="28" y="54" width="64" height="48" rx="6" fill="none" stroke="#221F1A" stroke-width="4"/><path d="M42 54V40a18 18 0 0 1 36 0v14" fill="none" stroke="#221F1A" stroke-width="4"/></svg>',
     "Soberania aqui é colaborar sob controle: política, revogação, origem e prova. O cadeado diz só \"trancado\" e puxa a marca para a estética de cibersegurança. Mostre o estado com rótulo."),
    ("Rede de pontos para dizer federação",
     '<svg viewBox="0 0 300 200" style="position:absolute;inset:0;width:100%;height:100%"><g stroke="#8E887F" stroke-width="1"><line x1="40" y1="50" x2="150" y2="100"/><line x1="150" y1="100" x2="260" y2="40"/><line x1="150" y1="100" x2="220" y2="170"/><line x1="40" y1="50" x2="80" y2="160"/><line x1="80" y1="160" x2="150" y2="100"/><line x1="260" y1="40" x2="220" y2="170"/></g><g fill="#221F1A"><circle cx="40" cy="50" r="6"/><circle cx="150" cy="100" r="8"/><circle cx="260" cy="40" r="6"/><circle cx="220" cy="170" r="6"/><circle cx="80" cy="160" r="6"/></g></svg>',
     "Uma rede sem rótulos não diz quem decide nem o que circula, e é o clichê da categoria. Desenhe a linhagem como trilha entre entidades nomeadas, com direção e data."),
]
falhas_html = "".join(f'<div class="falha">{mini(q, "#fff")}<h4>{t}</h4><p>{p}</p></div>' for t, q, p in falhas)

antes_depois = [
    ("Prova antes de superlativo", "Somos referência em soluções de IA de ponta.", "Três secretarias analisaram dados de saúde juntas por doze semanas; nenhuma linha saiu de casa."),
    ("Concreto antes de abstração", "Impulsionamos a transformação digital do setor público.", "Instalamos um nó em cada secretaria; a consulta vai até o dado e só o agregado autorizado volta."),
    ("Brasileiro sem folclore", "Inspirados na sabedoria ancestral da peneira indígena.", "Urupema é a peneira de fibra trançada: uma malha que decide o que passa. É o nosso método."),
    ("Acesso sem paternalismo", "Democratizamos a tecnologia para os menos favorecidos.", "Formação de dez meses com projeto real e entrevistas marcadas, com prioridade para quem está fora do mercado."),
    ("Promessa condicionada a mecanismo", "Plataforma 100% segura e soberana.", "Cada autorização é explícita, tem validade e pode ser revogada; toda execução deixa registro assinado."),
]
ad_html = "".join(f'<div><p class="rotulo" style="padding-top:3px">{a}</p><p class="nao">{b}</p><p class="sim">{c}</p></div>' for a, b, c in antes_depois)

tom = V["tone_by_moment"]
tom_nomes = {"institucional_e_editais": "Institucional e editais", "produto_e_operacao": "Produto e operação",
             "educacao_e_trabalho": "Educação e trabalho", "pdi_e_comercial": "PD&I e comercial", "incidente": "Incidente"}
tom_html = tabela(["Momento", "Como soa"], [(tom_nomes[k], e(v[:1].upper() + v[1:])) for k, v in tom.items()])

principios_verbais = "".join(regra(e(p["name"]), e(p["rule"]), {
    "Prova antes de superlativo": "A marca promete prova; um superlativo sem fonte é a contradição mais visível que ela pode cometer.",
    "Concreto antes de abstração": "Os públicos técnicos e públicos confiam no que conseguem verificar; abstração soa como a categoria inteira.",
    "Brasileiro sem folclore": "A origem do nome é método, não cenário; exotizá-la afasta ciência e governo.",
    "Acesso sem paternalismo": "Quem estuda e quem recebe infraestrutura é agente; linguagem de caridade tira essa agência.",
    "Promessa condicionada a mecanismo": "Soberano, verificado e auditável são afirmações técnicas; sem mecanismo, viram propaganda.",
}[p["name"]]) for p in V["principles"])

cores_tabela = tabela(["Cor", "Hex", "Papel"], [
    (f'<span class="chip" style="background:{h}"></span>{e(n)}', f'<span class="dado">{h}</span>', e(papeis_cor.get(n, "")))
    for n, h in nucleo + funcionais + escuro])
estados_tabela = tabela(["Estado", "Hex", "Onde"], [
    (f'<span class="chip" style="background:{h}"></span>{e(n)}', f'<span class="dado">{h}</span>',
     "sobre Tinta" if "Tinta" in n else "sobre Palha e branco") for n, h in estados])
pares_tabela = tabela(["Texto ou forma", "Fundo", "Uso", "Contraste"], [
    (f'<span class="chip" style="background:{fg}"></span>{e(tn)}', f'<span class="chip" style="background:{bg}"></span>{e(bn)}',
     u, f'<span class="dado">{fmt(r)} : 1</span>') for tn, fg, bn, bg, u, r in pares])

papeis_tipo = TY["roles"]
nomes_papel = {"monumental": "Monumental", "exibicao": "Exibição", "titulo": "Título", "corpo": "Corpo",
               "apoio": "Apoio", "rotulo": "Rótulo", "dado": "Dado"}
amostras_tipo = {
    "monumental": '<span style="font:400 96px/.92 var(--inst);font-variation-settings:\'opsz\' 72;letter-spacing:-.024em">Bem comum.</span>',
    "exibicao": '<span style="font:400 56px/1 var(--inst);font-variation-settings:\'opsz\' 72;letter-spacing:-.012em">O dado fica na origem</span>',
    "titulo": '<span style="font:500 32px/1.1 var(--inst);font-variation-settings:\'opsz\' 36">A análise vai até o dado</span>',
    "corpo": '<span style="font-size:17px">Cada participante mantém sua base no próprio ambiente. As consultas conjuntas rodam no local de origem.</span>',
    "apoio": '<span style="font-size:15px;color:var(--reduzida)">Versão do nó 2.4.1 · atualizada em 24 set 2026</span>',
    "rotulo": '<span class="rotulo">Política · Origem · Evidência</span>',
    "dado": '<span class="dado" style="font-size:22px;font-weight:500">99,94% · 46 de 64 · IU-RT-2026-007</span>',
}
hier = "".join(f'<div><p class="nome-papel">{nomes_papel[k]}<span>{e(v)}</span></p>{amostras_tipo[k]}</div>' for k, v in papeis_tipo.items())

corpo = f"""
<header class="capa escuro">
  <img class="campo" src="logo/simbolo-campo-escuro.svg" alt="">
  <img class="marca" src="logo/assinatura-horizontal-mono-negativa.svg" alt="Instituto Urupema">
  <h1>A marca, e como usá-la</h1>
  <p class="sub">Guia do Instituto Urupema para quem desenha, imprime, programa ou escreve em nome dele. Edição de setembro de 2026.</p>
  <ol class="indice">{indice}</ol>
</header>

<section class="s" id="porque">
  <div class="s-cab"><p class="rotulo">01 · Por que a marca é assim</p></div>
  <div class="corpo-s">
    <div class="col-cheia"><h2 class="tese">{e(V["tagline"])}</h2></div>
    <div class="col-texto">
      <p>O Instituto Urupema faz pesquisa, opera infraestrutura computacional, forma pessoas e presta serviços tecnológicos. A marca existe para que tudo isso seja lido como uma só instituição de longa duração, com uma tese: tecnologia bruta entra, passa por critério e chega como valor a quem precisa.</p>
      <p>Urupema é a peneira de fibra trançada. O nome dá o método, não a ilustração: antes de qualquer coisa circular, existe uma malha de regras, permissões, origem e prova. Daí a ideia que orienta todas as decisões visuais e de texto:</p>
      <p style="font:400 40px/1.1 var(--inst);font-variation-settings:'opsz' 60;margin:28px 0 8px">{e(D["thesis"])}</p>
    </div>
    <div class="cadeia">
      <div><p class="rotulo">Posição</p><p>{e(S["position"]["statement"])}</p></div>
      <div><p class="rotulo">O que a marca precisa fazer</p><p>{e(S["brand_job"]["statement"])}</p></div>
      <div><p class="rotulo">O que deve ficar associado</p><p>{e(S["desired_meaning"])}</p></div>
      <div><p class="rotulo">Com quem fala</p><p>{e(S["audience"]["primary"])}</p></div>
    </div>
    <div class="regras" style="grid-column:1/-1">
      {"".join(regra(e(p["name"]), e(p["rule"]), {
        "Critério antes do gesto": "É a tese aplicada: a estrutura existe antes do fluxo.",
        "Uma decisão em Urucum": "Um único ponto quente faz o Urucum funcionar como sinal e mantém a marca sóbria.",
        "Estrutura legível, não rede decorativa": "Relação sem rótulo contradiz a promessa de prova.",
        "Toda peça oficial deixa registro": "A marca afirma que o que passa, passa com prova; as próprias peças precisam cumprir isso.",
        "Público como agente": "O eixo social é acesso a capacidade e trabalho, não benevolência."}[p["name"]]) for p in D["principles"])}
    </div>
  </div>
</section>

<section class="s" id="simbolo">
  {cab(2, "simbolo", "Nove barras, uma decisão", "O símbolo é uma malha de três por três barras que alternam entre horizontais e verticais, como fibras trançadas. A barra do centro, em Urucum, é a decisão dentro de uma estrutura estável.")}
  <div class="corpo-s">
    <div class="painel-simbolo">
      <div class="construcao">{construcao}</div>
      <div class="variantes">
        <figure class="fundo-palha"><img src="logo/simbolo.svg" alt="Símbolo em Tinta e Urucum"><figcaption>Tinta e Urucum, sobre Palha ou branco. A versão principal.</figcaption></figure>
        <figure class="fundo-tinta"><img src="logo/simbolo-negativa.svg" alt="Símbolo negativo em Palha e Urucum"><figcaption>Palha e Urucum, sobre Tinta.</figcaption></figure>
        <figure class="fundo-branco"><img src="logo/simbolo-mono.svg" alt="Símbolo em uma cor, Tinta"><figcaption>Uma cor: carimbo, relevo seco, gravação, fax.</figcaption></figure>
        <figure class="fundo-tinta"><img src="logo/simbolo-mono-negativa.svg" alt="Símbolo em uma cor, Palha"><figcaption>Uma cor sobre escuro: hot stamping, serigrafia.</figcaption></figure>
      </div>
    </div>
    <div class="assinaturas-grade">
      <figure><img src="logo/assinatura-horizontal.svg" alt="Assinatura horizontal"><figcaption><b>Assinatura horizontal</b> — a padrão. Largura mínima de 180 px ou 40 mm; abaixo disso, use só o símbolo.</figcaption></figure>
      <figure><img src="logo/assinatura-vertical.svg" alt="Assinatura vertical" style="width:62%"><figcaption><b>Assinatura vertical</b> — para formatos estreitos e altos: fachada, lombada, avatar de evento. Mínimo de 120 px ou 28 mm.</figcaption></figure>
      <figure class="escura"><img src="logo/forja-assinatura-negativa.svg" alt="Forja, um produto do Instituto Urupema"><figcaption><b>Assinatura de produto</b> — nome do produto sobre a linha de endosso. O símbolo aparece só na linha de endosso.</figcaption></figure>
    </div>
    <div class="regras" style="grid-column:1/-1">
      {regra("Deixe uma célula de respiro", e(L["clear_space"]), "A célula é um terço do símbolo: a mesma unidade que constrói a marca mede o espaço dela.", "Em capas e fachadas, aumente o respiro; nunca o reduza.")}
      {regra("Respeite os tamanhos mínimos", "Símbolo: " + e(L["minimum_size"]["simbolo"]) + ". Carimbo: " + e(L["minimum_size"]["carimbo"]) + ".", "Abaixo disso as barras se fundem e a alternância, que é o que se reconhece, desaparece.", "Em 16 e 32 px, use os arquivos de favicon, já alinhados à grade de pixels.")}
      {regra("Use a versão do fundo", "Tinta e Urucum sobre claro; Palha e Urucum sobre Tinta; uma cor quando a produção só tem uma tinta.", "O Urucum do centro sobre Tinta tem contraste suficiente para forma (3,6 : 1); sobre Areia, prefira a versão em Tinta.")}
      {regra("Não mexa na malha", e(L["rules"][0]), "A alternância das nove barras é o que torna o símbolo reconhecível e distinto de uma grade qualquer.")}
      {regra("Assine sem descritor fixo", e(L["rules"][3]), "O Instituto tem quatro frentes; um descritor setorial encolhe a marca-mãe.", "Quando o contexto pedir, escreva o descritor como texto, fora da assinatura: " + e(V["descriptors"]["instituto"]))}
      {regra("Escala de campo, uma vez", e(L["rules"][1]), "Recortado pelo quadro, o símbolo mostra menos do que é e ganha força; o centro inteiro garante que a decisão continua lá.", "No campo, as oito barras podem ser Areia sobre Palha ou Tinta elevada sobre Tinta. Nesse caso, a assinatura da peça é a de uma cor.")}
    </div>
  </div>
</section>

<section class="s" id="cor">
  {cab(3, "cor", "Terra como sinal, não como cenário", e(C["visual"]["palette"]["behavior"]))}
  <div class="corpo-s">
    <div class="campo-cor" role="img" aria-label="Proporção de uso: Palha domina, depois Areia, depois Tinta, e Urucum em uma faixa estreita.">
      <div style="background:var(--palha);border:1px solid var(--areia)"><b>Palha</b><span class="dado">#F6F1E7</span></div>
      <div style="background:var(--areia)"><b>Areia</b><span class="dado">#E7DFD0</span></div>
      <div style="background:var(--tinta);color:var(--palha)"><b>Tinta</b><span class="dado">#221F1A</span></div>
      <div style="background:var(--urucum);padding:24px 6px"></div>
    </div>
    <div class="col-esq"><p class="rotulo" style="margin-bottom:14px">As quatro cores da marca e as cores de apoio</p>{cores_tabela}</div>
    <div class="col-dir">
      <div class="regras" style="grid-template-columns:1fr;row-gap:28px">
        {regras_de(C["visual"]["palette"]["rules"])}
      </div>
    </div>
    <div class="col-esq"><p class="rotulo" style="margin-bottom:14px">Estados de operação — só em produto e infraestrutura</p>{estados_tabela}</div>
    <div class="col-dir"><p class="rotulo" style="margin-bottom:14px">Pares verificados (WCAG 2.x; texto pede 4,5 : 1, bordas e texto grande 3 : 1)</p>{pares_tabela}</div>
  </div>
</section>

<section class="s" id="tipografia">
  {cab(4, "tipografia", "Editorial para a casa, sistema para a operação", "Duas famílias com licença aberta (SIL OFL 1.1) e suporte completo ao português. A Newsreader fala pela instituição; a Space Grotesk opera: corpo, interface, dados, rótulos e o nome na assinatura.")}
  <div class="corpo-s">
    <div class="especime">
      <div><p class="rotulo">Newsreader · voz institucional</p><p class="grande-inst">Ág</p><p class="alfabeto inst">AaBbCcÇçDdEeÉéÊêFfGgHhIiÍíJjKkLlMmNnOoÓóÔôÕõPpQqRrSsTtUuÚúVvWwXxYyZz 0123456789</p><p style="font-size:15px;color:var(--reduzida)">{e(TY["families"][0]["use"][:1].upper() + TY["families"][0]["use"][1:])}.</p></div>
      <div><p class="rotulo">Space Grotesk · voz de sistema</p><p class="grande-sis">Ág</p><p class="alfabeto">AaBbCcÇçDdEeÉéÊêFfGgHhIiÍíJjKkLlMmNnOoÓóÔôÕõPpQqRrSsTtUuÚúVvWwXxYyZz 0123456789</p><p style="font-size:15px;color:var(--reduzida)">{e(TY["families"][1]["use"][:1].upper() + TY["families"][1]["use"][1:])}.</p></div>
    </div>
    <div class="hierarquia">{hier}</div>
    <div class="regras" style="grid-column:1/-1">
      {regras_de(TY["rules"])}
      <div class="regra"><p class="faca">Em arquivos que terceiros editam sem as fontes da marca, use Georgia no lugar da Newsreader e Arial no lugar da Space Grotesk, com os mesmos papéis.</p></div>
    </div>
  </div>
</section>

<section class="s" id="gramatica">
  {cab(5, "gramatica", "Quatro elementos fazem a família", "Poucos elementos, sempre com a mesma função, fazem uma proposta, uma tela e um certificado parecerem da mesma casa sem repetir o mesmo leiaute.")}
  <div class="corpo-s">
    <div class="dispositivos">
      <div class="dispositivo">
        <div class="visual" style="background:var(--palha);background-image:linear-gradient(var(--areia) 1px,transparent 1px),linear-gradient(90deg,var(--areia) 1px,transparent 1px);background-size:40px 40px;background-position:-1px -1px"><img src="logo/simbolo.svg" alt="" style="position:absolute;width:200px;left:50%;top:50%;margin:-100px 0 0 -100px"></div>
        {regra("Malha e célula", e(C["visual"]["composition"]["grid"]) + " " + e(C["visual"]["composition"]["rules"][0]), "A malha vem antes do fluxo: a estrutura aparece antes do conteúdo que a atravessa.", "Em capas, a própria malha do símbolo pode ser a malha da página, alinhada às margens.")}
      </div>
      <div class="dispositivo">
        <div class="visual"><span class="barra" style="position:absolute;left:40px;top:48px"></span><p style="position:absolute;left:40px;top:92px;font:400 38px/1.05 var(--inst);font-variation-settings:'opsz' 60;margin:0;max-width:12em">Liberar resultado agregado</p></div>
        {regra("Barra de decisão", e(C["visual"]["composition"]["rules"][1]), "É a barra central do símbolo tirada da marca e posta no ponto que decide: a peça inteira aponta para lá.", "Na vertical (1 : 2,4) quando o eixo da peça é vertical, como numa trilha.")}
      </div>
      <div class="dispositivo">
        <div class="visual"><p style="position:absolute;left:40px;top:40px;font:400 30px/1.1 var(--inst);margin:0;max-width:14em">Relatório técnico</p><div class="reg-demo"><div><span>Documento</span><b>Relatório técnico</b></div><div><span>Versão</span><b>2.1</b></div><div><span>Data</span><b>30 set 2026</b></div><div><span>Identificador</span><b>IU-RT-2026-007</b></div></div></div>
        {regra("Registro", e(C["visual"]["composition"]["rules"][3]) + " " + e(D["principles"][3]["rule"]), "É a proofline na forma de desenho: a peça mostra de onde vem antes de pedir confiança.", "Em telas, o registro vira a linha de evidência; em certificados, carrega o código de verificação.")}
      </div>
      <div class="dispositivo">
        <div class="visual escuro" style="background:var(--tinta)"><img src="logo/simbolo-campo-escuro.svg" alt="" style="position:absolute;width:150%;left:22%;top:-30%"></div>
        {regra("Símbolo em campo", e(L["rules"][1]), "Mostrar menos do que o todo dá força à capa e deixa a decisão como único ponto quente.", "Palha com barras Areia para peças institucionais; Tinta com barras Tinta elevada para relatórios, apresentações e crachás.")}
      </div>
    </div>
    <div class="regras" style="grid-column:1/-1">
      {regra("Alinhe, não centralize", e(C["visual"]["composition"]["rules"][2]), "Assimetria controlada é a diferença entre um documento com ponto de vista e um formulário.")}
      {regra("Um salto de escala", "O título grande é pelo menos três vezes o corpo; o resto da peça fica em dois ou três tamanhos.", "Muitos degraus pequenos obrigam o leitor a contar níveis; um salto grande ordena de uma vez.")}
    </div>
  </div>
</section>

<section class="s" id="urucum">
  {cab(6, "urucum", "Uma decisão por composição", e(D["principles"][1]["rule"]))}
  <div class="corpo-s">
    <div class="falhas">{falhas_html}</div>
  </div>
</section>

<div class="aplic" id="aplicacoes">
  {cab(7, "aplicacoes", "A mesma casa em ciência, produto, governo e sala de aula", "Peças de referência feitas com os modelos desta pasta. O conteúdo é ilustrativo; a estrutura, as proporções e os comportamentos são os da marca.")}
  <div class="par">
    {fig("aplicacoes/proposta-1.jpg", "Capa de proposta institucional com o símbolo em escala de campo como malha da página", "<b>Proposta institucional.</b> A malha do símbolo é a malha da página; a única decisão é o centro em Urucum. Assinatura em uma cor.")}
    {fig("aplicacoes/relatorio-1.jpg", "Capa escura de relatório técnico com símbolo em campo", "<b>Relatório técnico.</b> O mesmo gesto sobre Tinta: barras em Tinta elevada, centro em Urucum.")}
  </div>
  <div class="par">
    {fig("aplicacoes/proposta-2.jpg", "Página interna de proposta com escopo, tabela de cronograma, assinaturas, carimbo e registro", "<b>Miolo de proposta.</b> Rótulo à esquerda, título na voz institucional, tabela com algarismos tabulares, carimbo em uma cor e registro no pé.")}
    {fig("aplicacoes/relatorio-2.jpg", "Página de relatório com gráfico em que só a série decisiva está em Urucum, notas, referências e selo de verificação", "<b>Página de resultados.</b> Só a série que decide está em Urucum; a figura traz fonte, versão do dado e execução; o selo mostra o que foi verificado.")}
  </div>
  <div class="inteira">{fig("aplicacoes/cena-convenio.jpg", "Página de proposta impressa em papel branco sobre a mesa, com assinaturas, registro e o carimbo em relevo seco", "<b>Convênio impresso.</b> No papel, o fundo é o branco da folha; o carimbo entra em relevo seco, sem tinta.")}</div>
  <div class="inteira">{fig("aplicacoes/forja-evidencia.jpg", "Tela da Forja com linhagem da execução, autorizações dos participantes e evidência", "<b>Forja, produto digital.</b> Linhagem como trilha de entidades rotuladas; estados com rótulo; a barra de decisão marca a única ação principal. Assinatura de produto no canto.")}</div>
  <div class="inteira">{fig("aplicacoes/infra-painel.jpg", "Painel de infraestrutura em fundo Tinta com nós, uso, estados e alertas", "<b>Painel de infraestrutura, modo escuro.</b> O título diz o estado em uma frase; cores de estado só com rótulo; a decisão é aprovar a liberação.")}</div>
  <div class="celular">
    {fig("aplicacoes/site-celular.jpg", "Abertura do site no celular", "<b>Site no celular.</b>")}
    {fig("aplicacoes/formacao-celular.jpg", "Página de formação no celular", "<b>Formação.</b> Resultado de trabalho, não promessa motivacional.")}
    {fig("aplicacoes/site-home.jpg", "Abertura do site institucional no computador", "<b>Site institucional.</b> A tese em escala monumental; o símbolo recortado à direita, com o centro inteiro.")}
  </div>
  <div class="par">
    {fig("aplicacoes/certificado.jpg", "Certificado de competência com nome, projeto avaliado, competências, carimbo em Urucum e código de verificação", "<b>Certificado de competência.</b> O carimbo em Urucum é a decisão; o código permite verificar o portfólio.")}
    {fig("aplicacoes/apresentacao-1.jpg", "Capa de apresentação em fundo Tinta com símbolo em campo", "<b>Apresentação.</b> Capa em Tinta, título na voz institucional.")}
  </div>
  <div class="tres">
    {fig("aplicacoes/apresentacao-2.jpg", "Slide de conteúdo com três números e a fonte", "<b>Slide de conteúdo.</b> Um número recebe a barra de decisão.")}
    {fig("aplicacoes/card-social-1.jpg", "Card social claro de chamada de parceria", "<b>Card social</b>, 1200 × 630.")}
    {fig("aplicacoes/card-social-2.jpg", "Card social escuro de relatório", "<b>Card social</b>, versão escura.")}
  </div>
  <div class="tres">
    {fig("aplicacoes/cena-cracha.jpg", "Crachá impresso em fundo Tinta, com cordão, sobre a mesa", "<b>Crachá.</b> Nome na voz institucional, registro de acesso, símbolo em campo com o centro inteiro.")}
    {fig("aplicacoes/assinatura-email.jpg", "Assinatura de e-mail em fontes de sistema", "<b>Assinatura de e-mail.</b> Fontes de sistema, porque clientes de e-mail não carregam as da marca.")}
    <figure><img src="logo/avatar-800.png" alt="Avatar: símbolo negativo sobre Tinta" style="width:60%;border-radius:50%"><figcaption><b>Avatar</b> para redes e aplicativos, seguro para recorte circular.</figcaption></figure>
  </div>
</div>

<section class="s" id="linguagem">
  {cab(8, "linguagem", "Uma frase posiciona. Outra prova.", "A voz é sóbria, precisa, material e pública. Ela explica estruturas concretas: quem decide, o que circula, onde roda, sob quais condições, que prova fica e quem ganha capacidade.")}
  <div class="corpo-s">
    <div class="frases">
      <div><p class="rotulo">Tese — em qualquer peça institucional</p><p class="grande">{e(V["tagline"])}</p><p style="font-size:15px;color:var(--reduzida)">Posiciona a instituição inteira. Não use como parte fixa da assinatura.</p></div>
      <div><p class="rotulo">Prova — só onde há prova</p><p class="grande">{e(V["proofline"]["text"])}</p><p style="font-size:15px;color:var(--reduzida)">{e(V["proofline"]["use"])}</p></div>
    </div>
    <div class="regras" style="grid-column:1/-1">{principios_verbais}</div>
    <div class="antes-depois"><div><p class="rotulo">Princípio</p><p class="rotulo">Não escreva</p><p class="rotulo">Escreva</p></div>{ad_html}</div>
    <div class="col-esq"><p class="rotulo" style="margin-bottom:14px">Tom por momento</p>{tom_html}</div>
    <div class="col-dir">
      <p class="rotulo" style="margin-bottom:14px">Palavras da casa — quando forem verdade</p>
      <ul class="vocab">{"".join(f"<li>{e(w)}</li>" for w in V["vocabulary"]["own"])}</ul>
      <p class="rotulo" style="margin:32px 0 14px">Palavras que não usamos como muleta</p>
      <ul class="vocab" style="color:var(--reduzida)">{"".join(f"<li>{e(w)}</li>" for w in V["vocabulary"]["avoid"])}</ul>
    </div>
    <div class="col-esq"><p class="rotulo" style="margin-bottom:14px">Apresentação curta</p><p class="boiler">{e(V["boilerplates"]["curto"])}</p></div>
    <div class="col-dir"><p class="rotulo" style="margin-bottom:14px">Apresentação média</p><p class="boiler">{e(V["boilerplates"]["medio"])}</p></div>
    <div class="col-texto"><p style="font-size:15px;color:var(--reduzida)">Só escreva "ICT privada sem fins lucrativos" em peças públicas quando o estatuto do Instituto sustentar a qualificação; na dúvida, consulte o responsável pela marca.</p></div>
  </div>
</section>

<section class="s" id="arquitetura">
  {cab(9, "arquitetura", "Uma casa. Produtos com função própria.", "O Instituto é a marca-mãe e a única fonte de autoridade. Produtos podem ter nome; programas, em regra, não; componentes técnicos, nunca.")}
  <div class="corpo-s">
    <div class="decisao-nome">
      <div><p class="rotulo">Instituto</p><h4>Marca-mãe</h4><p style="font-size:15px">{e(A["rules"][0])}</p></div>
      <div><p class="rotulo">Produto</p><h4>Nome próprio, endossado</h4><p style="font-size:15px">{e(A["rules"][1])}</p><p class="ex">Hoje: Forja — {e(V["descriptors"]["forja"])}</p></div>
      <div><p class="rotulo">Programa</p><h4>Nome descritivo</h4><p style="font-size:15px">{e(A["rules"][2])}</p><p class="ex">Ex.: Trilha de engenharia de dados do Instituto Urupema</p></div>
      <div><p class="rotulo">Componente interno</p><h4>Sem nome público</h4><p style="font-size:15px">{e(A["rules"][3])}</p><p class="ex">Ex.: o módulo de políticas da Forja</p></div>
    </div>
    <div class="regras" style="grid-column:1/-1">
      {regra("Passe a iniciativa pelo teste da urupema", e(A["rules"][4]), "A marca ajuda a conter escopo; nomear o que não cabe na tese mascara dispersão.")}
      {regra("Mantenha a camada de confiança neutra", e(A["rules"][5]), "A confiança técnica depende de separar governança de interesse comercial.")}
    </div>
    <div class="col-cheia">{fig("aplicacoes/coassinatura.jpg", "Três modos de co-assinatura com parceiros: o Instituto lidera, o parceiro lidera e paridade", "<b>Co-assinatura.</b> As marcas de parceiros aqui são substitutos neutros.")}</div>
    <div class="regras" style="grid-column:1/-1">{regras_de(A["cobranding"])}</div>
  </div>
</section>

<section class="s" id="selo">
  {cab(10, "selo", "Um autentica a autoria. O outro atesta uma verificação.")}
  <div class="corpo-s">
    <div class="col-esq" style="display:flex;gap:40px;align-items:center"><img src="logo/carimbo.svg" alt="Carimbo institucional em uma cor" style="width:46%"><img src="logo/carimbo-urucum.svg" alt="Carimbo institucional em Urucum" style="width:30%"></div>
    <div class="col-dir">
      {regra("Carimbo institucional", "Use em convênios, certificados, ofícios e documentos assinados pelo Instituto, em uma cor: Tinta, ou Urucum quando for a única decisão da peça. Serve também como matriz de relevo seco.", "Ele diz quem emite o documento; não afirma que algo foi verificado.", "Diâmetro mínimo de 25 mm; em tela, 160 px.")}
    </div>
    <div class="col-esq">
      <div style="display:inline-grid;grid-template-columns:auto 1fr;column-gap:12px;border:1.5px solid var(--tinta);border-radius:4px;padding:12px 16px 12px 12px;background:var(--palha)">
        <img src="logo/simbolo-mono.svg" alt="" style="width:28px;height:28px">
        <div><div style="font-size:12px;font-weight:600;letter-spacing:.1em;text-transform:uppercase">Verificado <span style="font-weight:500;color:var(--reduzida)">· Instituto Urupema</span></div>
        <dl style="margin:6px 0 0;display:grid;grid-template-columns:max-content max-content;column-gap:12px;row-gap:1px;font-size:12.5px"><dt class="rotulo" style="font-size:10px;padding-top:2px">Objeto</dt><dd style="margin:0">Execução FJ-2048</dd><dt class="rotulo" style="font-size:10px;padding-top:2px">Regra</dt><dd style="margin:0">G-881 v4</dd><dt class="rotulo" style="font-size:10px;padding-top:2px">Evidência</dt><dd style="margin:0" class="dado">ev.forja/FJ-2048</dd></dl></div>
      </div>
    </div>
    <div class="col-dir">
      {regra("Selo de verificação", e(V["seal_rule"]), "Um selo sem cadeia de prova é exatamente a promessa vazia que a marca recusa.", "No impresso, o selo leva o identificador consultável; em telas, leva ao registro da evidência.")}
    </div>
  </div>
</section>

<section class="s" id="imagem">
  {cab(11, "imagem", "Documentar capacidade, não encenar impacto", "Fotografia de trabalho real, perto das mãos e das ferramentas, com a luz do lugar. O calor da marca vem do Urucum gráfico, nunca de um filtro na foto.")}
  <div class="corpo-s">
    <div class="fotos">
      <figure class="f-grande"><img src="fotografia/provisoria-infraestrutura.jpg" alt="Técnica conecta um cabo de rede no painel de um rack de servidores"><figcaption><b>A ação em primeiro plano.</b> Mãos, cabo e painel dizem o que acontece; o rosto concentrado confirma que é trabalho, não pose.</figcaption></figure>
      <figure><img src="fotografia/provisoria-pesquisa.jpg" alt="Pesquisador analisa gráficos no monitor, com caderno de anotações ao lado"><figcaption><b>Pessoa trabalhando, não olhando para a câmera.</b> Luz de janela, cor natural, tela legível só como forma.</figcaption></figure>
      <figure><img src="fotografia/provisoria-saude.jpg" alt="Analista de dados de saúde marca uma linha em relatório impresso"><figcaption><b>O lugar como ele é.</b> Escritório público, papel e lápis; ninguém é retratado como beneficiário.</figcaption></figure>
      <figure><img src="fotografia/provisoria-formacao.jpg" alt="Duas pessoas programam juntas em um notebook, em sala de aula"><figcaption><b>Aprender como trabalho.</b> Duas gerações diante do mesmo problema; a turma ao fundo, fora de foco.</figcaption></figure>
      <figure><img src="fotografia/provisoria-cooperacao.jpg" alt="Mãos de quatro pessoas em volta de uma mesa com documentos, um diagrama e uma assinatura"><figcaption><b>Cooperação mostrada pelo que se decide.</b> O diagrama e a assinatura, não o aperto de mãos.</figcaption></figure>
    </div>
    <div class="regras" style="grid-column:1/-1">
      <div class="regra"><h4>Fotografia</h4>{"".join(f'<p class="faca">{e(r)}</p>' for r in C["visual"]["imagery"]["rules"])}</div>
      <div class="regra"><h4>Ícones</h4>{"".join(f'<p class="faca">{e(r)}</p>' for r in C["visual"]["iconography"]["rules"])}</div>
      <div class="regra"><h4>Dados e diagramas</h4>{"".join(f'<p class="faca">{e(r)}</p>' for r in C["visual"]["data"]["rules"])}</div>
      <div class="regra"><h4>Movimento</h4>{"".join(f'<p class="faca">{e(r)}</p>' for r in C["visual"]["motion"]["rules"])}</div>
    </div>
  </div>
</section>

<section class="s" id="decide">
  {cab(12, "decide", "Quem pode mudar a marca, e como")}
  <div class="corpo-s">
    <div class="regras" style="grid-column:1/-1">
      {regra("Fonte única", "Esta pasta é a referência. Qualquer arquivo de marca fora dela é cópia; em caso de diferença, vale o que está aqui.", "Uma só fonte é o que impede a deriva entre fornecedores e equipes.")}
      {regra("Responsável", e(G["owner"]), "Alguém precisa poder dizer sim ou não sem reabrir a marca a cada peça.")}
      {regra("Mudança", e(G["change"]), "Mudanças pequenas não esperam a direção; mudanças no que é patrimônio esperam.")}
      {regra("Exceção", e(G["exceptions"]), "Exceção que se repete é sinal de regra errada, não de peça errada.")}
    </div>
  </div>
</section>

<section class="s" id="arquivos">
  {cab(13, "arquivos", "Tudo o que você precisa para produzir", "Os masters estão em SVG, com o texto convertido em contornos: não dependem de fonte instalada. Os modelos em HTML imprimem em A4 pelo navegador.")}
  <div class="corpo-s"><div class="arquivos">{lista_arquivos()}</div></div>
</section>

<footer class="fim escuro">
  <img src="logo/assinatura-horizontal-negativa.svg" alt="Instituto Urupema">
  <p>{e(V["boilerplates"]["curto"])}</p>
</footer>
"""

doc = f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Marca do Instituto Urupema</title>
<meta name="description" content="Como usar a marca do Instituto Urupema: símbolo, assinaturas, cor, tipografia, gramática, linguagem, arquitetura e arquivos.">
<link rel="icon" href="logo/favicon.svg" type="image/svg+xml">
<style>{css}</style>
</head>
<body>
{corpo}
</body>
</html>
"""
(LIVRO / "index.html").write_text(doc)
print(f"index.html: {len(doc) // 1024} KB")
