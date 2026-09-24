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


def achatar_cores(no=None):
    no = T if no is None else no
    for k, v in no.items():
        if isinstance(v, dict) and "$value" in v:
            yield k, v
        elif isinstance(v, dict):
            yield from achatar_cores(v)


def fonte64(nome):
    return base64.b64encode((LIVRO / "fontes" / nome).read_bytes()).decode()


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
# Biblioteca: cada master com suas versões; o nome é o do elemento no sistema.
# Fundo: p = Palha, b = branco, t = Tinta.
BIBLIOTECA = [
    ("Símbolo", "A marca em si. Use a versão do fundo da peça.", [
        ("Cor", "p", "simbolo.svg", []),
        ("Negativa", "t", "simbolo-negativa.svg", []),
        ("Uma cor", "b", "simbolo-mono.svg", []),
        ("Uma cor, negativa", "t", "simbolo-mono-negativa.svg", []),
    ]),
    ("Assinatura horizontal", "A assinatura padrão. Símbolo com pelo menos 44 px ou 8,5 mm de altura.", [
        ("Cor", "p", "assinatura-horizontal.svg", ["assinatura-horizontal-1200.png"]),
        ("Negativa", "t", "assinatura-horizontal-negativa.svg", ["assinatura-horizontal-negativa-1200.png"]),
        ("Uma cor", "b", "assinatura-horizontal-mono.svg", []),
        ("Uma cor, negativa", "t", "assinatura-horizontal-mono-negativa.svg", []),
    ]),
    ("Assinatura vertical", "Para formatos estreitos e altos. O mesmo mínimo do símbolo.", [
        ("Cor", "p", "assinatura-vertical.svg", []),
        ("Negativa", "t", "assinatura-vertical-negativa.svg", []),
        ("Uma cor", "b", "assinatura-vertical-mono.svg", []),
        ("Uma cor, negativa", "t", "assinatura-vertical-mono-negativa.svg", []),
    ]),
    ("Assinatura de produto", "Nome do produto sobre a linha de endosso do Instituto.", [
        ("Forja, cor", "p", "forja-assinatura.svg", []),
        ("Forja, negativa", "t", "forja-assinatura-negativa.svg", []),
    ]),
    ("Carimbo institucional", "Documentos do Instituto e matriz de relevo seco. Diâmetro mínimo de 25 mm.", [
        ("Tinta", "b", "carimbo.svg", []),
        ("Urucum", "b", "carimbo-urucum.svg", []),
        ("Negativo", "t", "carimbo-negativo.svg", []),
    ]),
    ("Símbolo em campo", "Só em escala de campo, recortado pelo quadro, com o centro inteiro.", [
        ("Sobre Palha", "p", "simbolo-campo.svg", []),
        ("Sobre Tinta", "t", "simbolo-campo-escuro.svg", []),
    ]),
    ("Ícones de tela", "Favicon ajustado à grade de pixels, ícone de aplicativo e avatar.", [
        ("Favicon", "p", "favicon.svg", ["favicon-48.png"]),
        ("Favicon para 16 e 32 px", "p", "favicon-32.svg", ["favicon-16.svg", "favicon-16.png", "favicon-32.png"]),
        ("Ícone de aplicativo", "p", "icone-app-512.png", ["icone-app-180.png"]),
        ("Avatar", "t", "avatar.svg", ["avatar-800.png"]),
    ]),
]
FONTES_LISTA = [
    ("Newsreader", "voz institucional", [("Redonda", "Newsreader-Variavel.woff2"), ("Itálica", "Newsreader-Variavel-Italico.woff2"), ("Licença", "OFL-Newsreader.txt")]),
    ("Space Grotesk", "voz de sistema", [("Variável", "SpaceGrotesk-Variavel.woff2"), ("Licença", "OFL-SpaceGrotesk.txt")]),
]
MODELOS_LISTA = [
    ("Proposta institucional", "A4, capa e miolo", "proposta.html"),
    ("Relatório técnico", "A4, capa e página de resultados", "relatorio.html"),
    ("Certificado de competência", "A4 paisagem", "certificado.html"),
    ("Apresentação", "16 : 9, capa e conteúdo", "apresentacao.html"),
    ("Card social", "1200 × 630, claro e escuro", "card-social.html"),
    ("Crachá", "54 × 86 mm", "cracha.html"),
    ("Assinatura de e-mail", "tabela para colar no cliente de e-mail", "assinatura-email.html"),
    ("Co-assinatura com parceiros", "três modos", "coassinatura.html"),
    ("Site institucional", "página inicial, tela e celular", "site-home.html"),
    ("Formação", "página de turma, celular", "formacao.html"),
    ("Forja, evidência de execução", "interface de produto", "forja-evidencia.html"),
    ("Painel de infraestrutura", "interface em modo escuro", "infra-painel.html"),
    ("Componentes", "folha de estilo dos modelos", "componentes.css"),
]
CORES_LISTA = [("Variáveis para CSS", "tokens.css"), ("Variáveis em JSON", "tokens.json")]


def _fmt(nome):
    """SVG, PNG 1200, SVG 16… — formato e, quando houver, o tamanho do arquivo."""
    base, ext = nome.rsplit(".", 1)
    fim = base.rsplit("-", 1)[-1]
    return ext.upper() + (f" {fim}" if fim.isdigit() else "")


def biblioteca():
    usados = set()
    grupos = []
    for titulo, uso, versoes in BIBLIOTECA:
        itens = []
        for rotulo, fundo, principal, extras in versoes:
            usados.update([principal, *extras])
            links = " ".join(f'<a href="logo/{f}" download>{_fmt(f)}</a>' for f in [principal, *extras])
            itens.append(f'<figure class="ativo"><div class="miniatura f-{fundo}"><img src="logo/{principal}" alt="{e(titulo)}, {e(rotulo.lower())}"></div>'
                         f'<figcaption><b>{e(rotulo)}</b><span>{links}</span></figcaption></figure>')
        grupos.append(f'<section class="grupo-ativos"><div class="cab-ativos"><h3>{e(titulo)}</h3><p>{e(uso)}</p></div>'
                      f'<div class="ativos n{len(versoes)}">{"".join(itens)}</div></section>')
    faltando = sorted(set(p.name for p in (LIVRO / "logo").iterdir()) - usados)
    assert not faltando, f"arquivos de logo fora da biblioteca: {faltando}"
    fontes = "".join(f'<li><b>{e(n)}</b><span>{e(papel)}</span><span class="links">' +
                     " ".join(f'<a href="fontes/{f}" download>{e(r)}</a>' for r, f in arqs) + '</span></li>'
                     for n, papel, arqs in FONTES_LISTA)
    modelos = "".join(f'<li><a href="modelos/{f}">{e(n)}</a><span>{e(d)}</span></li>' for n, d, f in MODELOS_LISTA)
    cores = "".join(f'<li><a href="cores/{f}" download>{e(n)}</a><span>{f}</span></li>' for n, f in CORES_LISTA)
    for pasta, lista in (("modelos", [f for _, _, f in MODELOS_LISTA]), ("fontes", [f for _, _, a in FONTES_LISTA for _, f in a]), ("cores", [f for _, f in CORES_LISTA])):
        falt = sorted(set(p.name for p in (LIVRO / pasta).iterdir()) - set(lista))
        assert not falt, f"{pasta} fora da lista: {falt}"
    return ("".join(grupos) +
            f'<div class="listas"><section><h3>Modelos editáveis</h3><p class="nota">Abra no navegador para ver; edite o HTML para usar; imprima pelo navegador em A4.</p><ul class="lista">{modelos}</ul></section>'
            f'<section><h3>Fontes</h3><p class="nota">Licença SIL OFL 1.1: uso, instalação e distribuição livres.</p><ul class="lista fontes">{fontes}</ul>'
            f'<h3 style="margin-top:48px">Cores</h3><p class="nota">As mesmas variáveis dos modelos, para sites e sistemas.</p><ul class="lista">{cores}</ul></section></div>')


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
.capa h1 {{ font-size: clamp(60px, 9.4vw, 144px); line-height: .9; margin-top: auto; max-width: 7em; letter-spacing: -.024em; }}
.capa .sub {{ font-size: 20px; margin: 32px 0 56px; max-width: 32em; color: var(--palha-reduzida); }}
.indice {{ columns: 3; column-gap: 24px; border-top: 1px solid var(--palha); padding-top: 14px; list-style: none; margin: 0; padding-left: 0; }}
.indice li {{ break-inside: avoid; }}
.indice li {{ font-size: 15px; padding: 3px 0; }}
.indice a {{ text-decoration: none; }}
.indice span {{ font-variant-numeric: tabular-nums; color: var(--palha-reduzida); display: inline-block; width: 2.2em; }}

/* seções */
section.s {{ padding: 120px var(--m) 96px; border-top: 1px solid var(--areia); }}
.s-cab {{ display: grid; grid-template-columns: repeat(12, minmax(0,1fr)); column-gap: 24px; margin-bottom: 64px; align-items: baseline; }}
.s-cab .rotulo {{ grid-column: 1 / 4; }}
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
.cadeia p.rotulo {{ font-size: 12px; margin-bottom: 10px; }}

/* símbolo */
.painel-simbolo {{ grid-column: 1 / -1; display: grid; grid-template-columns: 7fr 5fr; column-gap: 48px; align-items: start; }}
.construcao {{ background: #fff; border: 1px solid var(--areia); padding: 40px; }}
.construcao svg {{ width: 100%; height: auto; display: block; }}
.construcao .cota {{ font: 500 10.5px var(--sis); fill: var(--reduzida); letter-spacing: .04em; font-variant-numeric: tabular-nums; }}
.construcao .cota-l line {{ stroke: var(--reduzida); stroke-width: .8; }}
.construcao .eixo {{ stroke: var(--urucum); stroke-width: .6; stroke-dasharray: 2 3; opacity: .55; }}
.construcao .guia {{ stroke: var(--reduzida); stroke-width: .6; }}
.construcao .moldura {{ stroke: var(--filete-forte); stroke-dasharray: 3 4; stroke-width: .8; }}
.construcao .limite {{ stroke: var(--areia); stroke-width: 1; }}
.leitura ol {{ list-style: none; margin: 16px 0 0; padding: 0; border-top: 1px solid var(--tinta); counter-reset: l; }}
.leitura li {{ padding: 14px 0; border-bottom: 1px solid var(--areia); font-size: 16px; }}
.leitura li b {{ display: block; font-weight: 600; margin-bottom: 2px; }}
.nota {{ font-size: 13.5px; color: var(--reduzida); margin-top: 14px; }}
.palco {{ aspect-ratio: 4 / 3; display: flex; align-items: center; justify-content: center; }}
.palco img {{ width: 34%; }}
.f-p {{ background: var(--palha); box-shadow: inset 0 0 0 1px var(--areia); }}
.f-b {{ background: #fff; box-shadow: inset 0 0 0 1px var(--areia); }}
.f-t {{ background: var(--tinta); }}
.variantes {{ grid-column: 1 / -1; display: grid; grid-template-columns: repeat(4, minmax(0,1fr)); column-gap: 24px; }}
.variantes figure, .assinaturas-grade figure {{ margin: 0; }}
.variantes figcaption, .assinaturas-grade figcaption {{ font-size: 14px; color: var(--reduzida); margin-top: 14px; }}
.variantes figcaption b, .assinaturas-grade figcaption b {{ display: block; color: var(--tinta); font-weight: 600; margin-bottom: 2px; }}
.assinaturas-grade {{ grid-column: 1 / -1; display: grid; grid-template-columns: repeat(3, minmax(0,1fr)); column-gap: 24px; }}
.assinaturas-grade .palco {{ aspect-ratio: 3 / 2; }}
table {{ width: 100%; border-collapse: collapse; font-size: 15px; }}
th {{ text-align: left; font: 500 11px/1.3 var(--sis); letter-spacing: .09em; text-transform: uppercase; color: var(--reduzida); padding: 0 16px 10px 0; border-bottom: 1px solid var(--tinta); }}
td {{ padding: 12px 16px 12px 0; border-bottom: 1px solid var(--areia); vertical-align: top; }}
.chip {{ display: inline-block; width: 12px; height: 12px; border-radius: 2px; vertical-align: -1px; margin-right: 8px; box-shadow: inset 0 0 0 1px rgba(34,31,26,.28); }}

/* cor */
.campo-cor {{ grid-column: 1 / -1; margin: 0; }}
.campo-cor .faixa {{ display: grid; grid-template-columns: 62fr 20fr 14fr 4fr; height: 300px; }}
.campo-cor .legendas {{ display: grid; grid-template-columns: 62fr 20fr 14fr 4fr; margin-top: 14px; }}
.campo-cor .legendas p {{ margin: 0; font-size: 13.5px; color: var(--reduzida); padding-right: 12px; }}
.campo-cor .legendas p:last-child {{ white-space: nowrap; padding-right: 0; justify-self: end; text-align: right; }}
.campo-cor .legendas b {{ display: block; font: 400 26px/1.1 var(--inst); font-variation-settings: "opsz" 36; color: var(--tinta); }}
.campo-cor .legendas span {{ display: block; margin: 2px 0; }}
.campo-cor figcaption {{ margin-top: 20px; }}
.matriz {{ overflow-x: auto; }}
.matriz table {{ font-size: 14px; }}
.matriz th, .matriz td {{ padding: 10px 10px 10px 0; white-space: nowrap; }}
.matriz thead th {{ font-size: 10.5px; }}
.matriz tbody th {{ font: 400 14px/1.3 var(--sis); letter-spacing: 0; text-transform: none; color: var(--tinta); text-align: left; border-bottom: 1px solid var(--areia); padding: 10px 16px 10px 0; }}
.matriz thead th:not(:first-child), .matriz td {{ width: 15%; }}
.matriz td {{ text-align: left; }}
.matriz .vazio {{ color: var(--areia); }}
.matriz sup {{ color: var(--reduzida); }}
.nota sup {{ font-size: 10px; }}
.estados {{ display: grid; grid-template-columns: repeat(6, minmax(0,1fr)); border-top: 1px solid var(--tinta); }}
.estado-am {{ padding: 16px 16px 18px; display: flex; flex-direction: column; gap: 3px; font-size: 13px; color: var(--reduzida); }}
.estado-am.escuro {{ background: var(--tinta); color: var(--palha-reduzida); }}
.estado-t {{ font-size: 15px; font-weight: 500; display: flex; align-items: center; gap: 8px; }}
.estado-t::before {{ content: ""; width: 9px; height: 9px; border-radius: 2px; background: currentColor; }}
.amostras {{ display: grid; grid-template-columns: repeat(4, minmax(0,1fr)); gap: 0; }}
.amostra {{ padding: 20px; min-height: 150px; display: flex; flex-direction: column; justify-content: flex-end; gap: 2px; font-size: 13.5px; border: 1px solid rgba(34,31,26,.08); }}
.amostra b {{ font-weight: 600; font-size: 15px; }}

/* tipografia */
.especime {{ grid-column: 1 / -1; display: grid; grid-template-columns: 1fr 1fr; column-gap: 24px; }}
.especime > div {{ border-top: 1px solid var(--tinta); padding-top: 18px; }}
.especime .grande-inst {{ font: 400 176px/1 var(--inst); font-variation-settings: "opsz" 72; letter-spacing: -.03em; margin: 40px 0 28px; height: 230px; display: flex; align-items: flex-end; }}
.especime .grande-sis {{ font: 500 176px/1 var(--sis); letter-spacing: -.04em; margin: 40px 0 28px; height: 230px; display: flex; align-items: flex-end; padding-bottom: .111em; }}
.especime .alfabeto {{ font-size: 22px; line-height: 1.4; margin: 0 0 16px; max-width: none; letter-spacing: .01em; }}
.especime .alfabeto.inst {{ font-family: var(--inst); font-variation-settings: "opsz" 24; }}
.hierarquia {{ grid-column: 1 / -1; border-top: 1px solid var(--tinta); }}
.hierarquia > div {{ display: grid; grid-template-columns: 3fr 9fr; column-gap: 24px; padding: 22px 0; border-bottom: 1px solid var(--areia); align-items: baseline; }}
.hierarquia .nome-papel {{ font-size: 14px; }}
.hierarquia .nome-papel span {{ display: block; color: var(--reduzida); font-size: 13px; margin-top: 4px; }}

/* gramática */
.dispositivos {{ grid-column: 1 / -1; display: grid; grid-template-columns: repeat(2, minmax(0,1fr)); column-gap: 24px; row-gap: 56px; }}
.dispositivo .visual {{ background: #fff; border: 1px solid var(--areia); aspect-ratio: 16 / 10; position: relative; overflow: hidden; margin-bottom: 20px; }}
.demo-doc {{ background: var(--areia) !important; display: flex; align-items: center; justify-content: center; }}
.demo-doc img {{ height: 86%; width: auto; box-shadow: 0 1px 2px rgba(34,31,26,.12), 0 8px 24px rgba(34,31,26,.10); }}
.demo-foto img {{ width: 100%; height: 100%; object-fit: cover; }}
.demo-ui {{ padding: 36px 40px; display: flex; flex-direction: column; }}
.demo-ui .demo-h {{ font: 600 28px/1.1 var(--sis); letter-spacing: -.01em; margin: 8px 0 6px; }}
.demo-ui .demo-a {{ font-size: 14px; color: var(--reduzida); margin: 0; }}
.demo-ui .demo-b {{ margin-top: auto; display: flex; gap: 12px; justify-content: flex-end; flex-wrap: wrap; }}
.demo-ui .demo-b span {{ font: 500 14px/1 var(--sis); padding: 13px 16px; border-radius: 4px; display: inline-flex; align-items: center; gap: 10px; white-space: nowrap; }}
.demo-ui .b2 {{ box-shadow: inset 0 0 0 1px var(--filete-forte); }}
.demo-ui .b1 {{ background: var(--tinta); color: var(--palha); }}
.demo-ui .barra {{ width: 17px; height: 7px; }}
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
.frases .grande {{ font: 400 52px/1.02 var(--inst); font-variation-settings: "opsz" 72; letter-spacing: -.015em; margin: 16px 0 16px; text-wrap: balance; max-width: 11em; }}
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
.arquivos {{ grid-column: 1 / -1; }}
.grupo-ativos {{ display: grid; grid-template-columns: repeat(12, minmax(0,1fr)); column-gap: 24px; padding: 32px 0; border-top: 1px solid var(--areia); }}
.grupo-ativos:first-child {{ border-top: 1px solid var(--tinta); }}
.cab-ativos {{ grid-column: 1 / 4; }}
.cab-ativos h3, .listas h3 {{ font: 500 24px/1.15 var(--inst); font-variation-settings: "opsz" 36; margin: 0 0 8px; }}
.cab-ativos p {{ font-size: 14px; color: var(--reduzida); margin: 0; }}
.ativos {{ grid-column: 4 / 13; display: grid; grid-template-columns: repeat(4, minmax(0,1fr)); column-gap: 20px; row-gap: 24px; }}
.ativo {{ margin: 0; }}
.miniatura {{ aspect-ratio: 4 / 3; display: flex; align-items: center; justify-content: center; }}
.miniatura img {{ width: 72%; height: 56%; object-fit: contain; }}
.ativo figcaption {{ margin-top: 10px; font-size: 13.5px; display: flex; flex-direction: column; gap: 4px; color: var(--tinta); }}
.ativo figcaption b {{ font-weight: 500; }}
.ativo figcaption span {{ display: flex; gap: 4px 12px; flex-wrap: wrap; }}
.ativo figcaption a {{ font-size: 12px; font-weight: 500; letter-spacing: .06em; color: var(--urucum-texto); text-decoration: none; }}
.ativo figcaption a:hover {{ text-decoration: underline; }}
.listas {{ display: grid; grid-template-columns: repeat(2, minmax(0,1fr)); column-gap: 48px; padding-top: 48px; border-top: 1px solid var(--tinta); margin-top: 16px; }}
.listas .nota {{ margin: 0 0 16px; }}
.lista {{ list-style: none; margin: 0; padding: 0; border-top: 1px solid var(--tinta); }}
.lista li {{ display: grid; grid-template-columns: 1fr auto; column-gap: 16px; padding: 11px 0; border-bottom: 1px solid var(--areia); font-size: 15px; align-items: baseline; }}
.lista li > span {{ font-size: 13px; color: var(--reduzida); }}
.lista.fontes li {{ grid-template-columns: auto 1fr auto; }}
.lista .links {{ display: flex; gap: 14px; }}
.lista a {{ text-decoration: none; }}
.lista a:hover {{ text-decoration: underline; }}
.lista .links a {{ font-size: 13px; color: var(--urucum-texto); font-weight: 500; }}
.aplic .celular {{ display: grid; grid-template-columns: 1fr 1fr 2fr; column-gap: 24px; margin-bottom: 72px; align-items: start; }}
.nota-celular {{ align-self: end; border-top: 1px solid var(--tinta); padding-top: 14px; }}
.nota-celular p:last-child {{ font-size: 16px; margin-top: 8px; }}
.aplic .micro {{ display: grid; grid-template-columns: 2fr 1fr; column-gap: 24px; margin-bottom: 24px; }}
.micro-col {{ display: grid; row-gap: 24px; align-content: start; }}
.micro-col .palco {{ aspect-ratio: 5 / 3; }}
.palco-email img {{ width: 84%; box-shadow: none !important; }}
.palco .avatar {{ width: 34%; border-radius: 50%; box-shadow: none !important; }}
.palco-selo {{ aspect-ratio: 16 / 9; gap: 40px; }}
.colofao {{ grid-column: 1 / -1; display: flex; flex-wrap: wrap; gap: 12px 48px; margin: 48px 0 0; padding-top: 14px; border-top: 1px solid var(--filete-escuro); }}
.colofao dt {{ font: 500 10.5px/1.3 var(--sis); letter-spacing: .09em; text-transform: uppercase; color: var(--palha-reduzida); }}
.colofao dd {{ margin: 2px 0 0; font-size: 13.5px; }}

footer.fim {{ padding: 72px var(--m) 56px; display: grid; grid-template-columns: repeat(12, minmax(0,1fr)); column-gap: 24px; }}
footer.fim img {{ grid-column: 1 / 4; height: 64px; width: auto; margin: -16px 0 0 -20px; }}
footer.fim p {{ grid-column: 5 / 12; font-size: 15px; color: var(--palha-reduzida); }}

@media (max-width: 900px) {{
  .s-cab, .corpo-s {{ display: block; }}
  .s-cab h2 {{ margin-top: 12px; }}
  .corpo-s > * + * {{ margin-top: 48px; }}
  .fotos, .regras, .cadeia, .painel-simbolo, .assinaturas-grade, .especime, .dispositivos, .falhas, .frases, .decisao-nome, .aplic .par, .aplic .tres, .aplic .micro, .listas {{ grid-template-columns: 1fr; row-gap: 32px; }}
  .indice {{ columns: 1; }}
  .variantes, .aplic .celular {{ grid-template-columns: 1fr 1fr; row-gap: 32px; }}
  .nota-celular {{ grid-column: 1 / -1; }}
  .grupo-ativos {{ display: block; }}
  .cab-ativos {{ margin-bottom: 18px; }}
  .ativos {{ grid-template-columns: 1fr 1fr; }}
  .estados {{ grid-template-columns: 1fr 1fr; }}
  .listas {{ display: grid; }}
  .campo-cor .faixa {{ height: 180px; }}
  .campo-cor .legendas {{ grid-template-columns: 1fr 1fr; row-gap: 14px; }}
  .campo-cor .legendas p:last-child {{ justify-self: start; text-align: left; }}
  .reg-demo {{ grid-template-columns: repeat(2, auto) !important; row-gap: 8px; left: 24px !important; right: 24px !important; bottom: 24px !important; }}
  .demo-ui {{ padding: 24px; }}
  .demo-ui .demo-b span.b2 {{ display: none; }}
  .colofao {{ gap: 12px 32px; }}
  .capa h1 {{ font-size: 50px; hyphens: manual; }}
  .lista li, .lista.fontes li {{ grid-template-columns: 1fr; row-gap: 2px; }}
  .lista .links {{ margin-top: 4px; }}
  .matriz table {{ min-width: 640px; }}
  .amostras {{ grid-template-columns: 1fr 1fr; }}
  .especime .grande-inst, .especime .grande-sis {{ font-size: 110px; }}
  .hierarquia > div, .antes-depois > div {{ grid-template-columns: 1fr; row-gap: 6px; }}
  .capa .campo {{ width: 118vw; right: auto; left: 22vw; top: 40px; }}
  .capa h1 {{ margin-top: 380px; }}
  section.s, .aplic {{ padding-top: 72px; padding-bottom: 56px; }}
  table {{ font-size: 13.5px; }}
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
  .indice {{ columns: 3; }}
  .indice li {{ font-size: 9pt; }}
  section.s, .aplic {{ padding: 0; border: 0; page-break-before: always; }}
  .s-cab {{ margin-bottom: 10mm; }}
  .s-cab h2 {{ font-size: 34pt; }}
  .regra, .falha, figure, .dispositivo, tr, .grupo-ativos, .lista li {{ break-inside: avoid; }}
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
m = 95  # respiro: um terço do lado


def _cota_h(x1, x2, y, texto, acima=True):
    ty = y - 7 if acima else y + 15
    return (f'<g class="cota-l"><line x1="{x1}" y1="{y}" x2="{x2}" y2="{y}"/><line x1="{x1}" y1="{y - 4}" x2="{x1}" y2="{y + 4}"/>'
            f'<line x1="{x2}" y1="{y - 4}" x2="{x2}" y2="{y + 4}"/></g>'
            f'<text x="{(x1 + x2) / 2}" y="{ty}" text-anchor="middle" class="cota">{texto}</text>')


def _cota_v(y1, y2, x, texto, direita=True):
    tx = x + 8 if direita else x - 8
    ancora = "start" if direita else "end"
    return (f'<g class="cota-l"><line x1="{x}" y1="{y1}" x2="{x}" y2="{y2}"/><line x1="{x - 4}" y1="{y1}" x2="{x + 4}" y2="{y1}"/>'
            f'<line x1="{x - 4}" y1="{y2}" x2="{x + 4}" y2="{y2}"/></g>'
            f'<text x="{tx}" y="{(y1 + y2) / 2 + 4}" text-anchor="{ancora}" class="cota">{texto}</text>')


L_ = 285 + 2 * m
eixos = "".join(f'<line x1="{m + c}" y1="{m - 12}" x2="{m + c}" y2="{m + 297}" class="eixo"/>'
                f'<line x1="{m - 12}" y1="{m + c}" x2="{m + 297}" y2="{m + c}" class="eixo"/>' for c in (40.5, 142.5, 244.5))
barras_svg = "".join(
    f'<rect x="{m + x}" y="{m + y}" width="{w}" height="{h}" rx="17" fill="{"#B4602F" if i == 4 else "#221F1A"}"/>'
    for i, (x, y, w, h) in enumerate(BARRAS))
cotas = (_cota_h(m + 40.5, m + 142.5, m - 44, "passo 102")
         + _cota_h(m, m + 81, m - 18, "81")
         + _cota_v(m + 23.5, m + 57.5, m + 285 + 18, "34")
         + _cota_v(m + 102, m + 183, m + 285 + 18, "81")
         + _cota_h(0, m, m - 18, "respiro 95")
         + _cota_h(m, m + 285, m + 285 + 44, "lado 285", acima=False))
raio = (f'<line x1="{m + 102 + 81 - 5}" y1="{m + 125.5 + 34 + 4}" x2="{m + 222}" y2="{m + 196}" class="guia"/>'
        f'<text x="{m + 226}" y="{m + 200}" class="cota">raio 17</text>')
construcao = f'''<svg viewBox="0 0 {L_} {L_}" role="img" aria-label="Construção do símbolo em unidades do master de 285: barras de 81 por 34 com raio 17, alternando horizontais e verticais, com passo de 102 entre centros; a barra central, horizontal, em Urucum; respiro de 95, um terço do lado.">
<rect x="0.5" y="0.5" width="{L_ - 1}" height="{L_ - 1}" fill="none" class="moldura"/>
<rect x="{m}" y="{m}" width="285" height="285" fill="none" class="limite"/>
{eixos}{barras_svg}{cotas}{raio}
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
     "Soberania aqui é colaborar sob controle: política, revogação, origem e prova. O cadeado diz só “trancado” e puxa a marca para a estética de cibersegurança. Mostre o estado com rótulo."),
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
estados_html = "".join(
    f'<div class="estado-am{" escuro" if "Tinta" in n else ""}"><span class="estado-t" style="color:{h}">{e(n.replace(" sobre Tinta", ""))}</span><span class="dado">{h}</span><span>{"sobre Tinta" if "Tinta" in n else "sobre Palha e branco"}</span></div>'
    for n, h in estados)
estados_tabela = tabela(["Estado", "Hex", "Onde"], [
    (f'<span class="chip" style="background:{h}"></span>{e(n)}', f'<span class="dado">{h}</span>',
     "sobre Tinta" if "Tinta" in n else "sobre Palha e branco") for n, h in estados])
FUNDOS = ["Palha", "Areia", "Branco papel", "Tinta", "Tinta elevada"]
_linhas, _ordem = {}, []
for tn, fg, bn, bg, u, r in pares:
    if tn not in _linhas:
        _linhas[tn] = (fg, {})
        _ordem.append(tn)
    _linhas[tn][1][bn] = (r, u)
_cab = "".join(f'<th><span class="chip" style="background:{resolver(next(t["$value"] for k, t in achatar_cores() if t.get("name") == f))}"></span>{e(f)}</th>' for f in FUNDOS)
_corpo = ""
for tn in _ordem:
    fg, cel = _linhas[tn]
    tds = ""
    for f in FUNDOS:
        if f in cel:
            r, u = cel[f]
            marca = "" if u == "texto" else ' <sup>*</sup>'
            tds += f'<td class="dado">{fmt(r)}{marca}</td>'
        else:
            tds += '<td class="vazio">—</td>'
    _corpo += f'<tr><th scope="row"><span class="chip" style="background:{fg}"></span>{e(tn)}</th>{tds}</tr>'
pares_tabela = (f'<div class="matriz"><table><thead><tr><th>Texto ou forma</th>{_cab}</tr></thead><tbody>{_corpo}</tbody></table></div>'
                '<p class="nota">Razão de contraste WCAG 2.x. Texto comum pede 4,5 : 1. <sup>*</sup> Só para texto grande, bordas e formas, que pedem 3 : 1.</p>')

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
  <h1>A marca,<br>e como usá-la</h1>
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
      <div class="leitura">
        <p class="rotulo">Como ler o desenho</p>
        <ol>
          <li><b>Malha de três por três.</b> Nove barras iguais, alternando horizontais e verticais, como fibras trançadas.</li>
          <li><b>Passo de 102.</b> Os centros das barras estão a 102 unidades uns dos outros; cada barra mede 81 × 34, com pontas de raio 17.</li>
          <li><b>Uma decisão.</b> A barra do centro é horizontal e é a única em Urucum.</li>
          <li><b>Respiro de 95.</b> Um terço do lado, em volta de todo o símbolo; os arquivos já o incluem.</li>
        </ol>
        <p class="nota">Medidas em unidades do master, que tem 285 de lado.</p>
      </div>
    </div>
    <div class="variantes">
      <figure><div class="palco f-p"><img src="logo/simbolo.svg" alt="Símbolo em Tinta e Urucum"></div><figcaption><b>Cor</b>Tinta e Urucum, sobre Palha ou branco. A versão principal.</figcaption></figure>
      <figure><div class="palco f-t"><img src="logo/simbolo-negativa.svg" alt="Símbolo negativo em Palha e Urucum"></div><figcaption><b>Negativa</b>Palha e Urucum, sobre Tinta.</figcaption></figure>
      <figure><div class="palco f-b"><img src="logo/simbolo-mono.svg" alt="Símbolo em uma cor, Tinta"></div><figcaption><b>Uma cor</b>Carimbo, relevo seco, gravação, fax.</figcaption></figure>
      <figure><div class="palco f-t"><img src="logo/simbolo-mono-negativa.svg" alt="Símbolo em uma cor, Palha"></div><figcaption><b>Uma cor, negativa</b>Hot stamping e serigrafia sobre escuro.</figcaption></figure>
    </div>
    <div class="assinaturas-grade">
      <figure><div class="palco f-b"><img src="logo/assinatura-horizontal.svg" alt="Assinatura horizontal" style="width:78%"></div><figcaption><b>Assinatura horizontal</b>A padrão. Símbolo com pelo menos 44 px de altura na tela ou 8,5 mm no impresso; abaixo disso, use só o símbolo.</figcaption></figure>
      <figure><div class="palco f-b"><img src="logo/assinatura-vertical.svg" alt="Assinatura vertical" style="width:52%"></div><figcaption><b>Assinatura vertical</b>Para formatos estreitos e altos: fachada, lombada, avatar de evento. O mesmo mínimo do símbolo.</figcaption></figure>
      <figure><div class="palco f-t"><img src="logo/forja-assinatura-negativa.svg" alt="Forja, um produto do Instituto Urupema" style="width:70%"></div><figcaption><b>Assinatura de produto</b>Nome do produto sobre a linha de endosso; o símbolo aparece só na linha de endosso.</figcaption></figure>
    </div>
    <div class="regras" style="grid-column:1/-1">
      {regra("Deixe uma célula de respiro", e(L["clear_space"]), "Um terço do lado é uma medida que se confere a olho e com régua, em qualquer tamanho.", "Em capas e fachadas, aumente o respiro; nunca o reduza.")}
      {regra("Respeite os tamanhos mínimos", "Símbolo sozinho: " + e(L["minimum_size"]["simbolo"]) + ". Assinaturas: símbolo com 44 px ou 8,5 mm de altura; abaixo disso, use só o símbolo. Carimbo: " + e(L["minimum_size"]["carimbo"]) + ".", "Abaixo disso as barras se fundem e INSTITUTO deixa de ser lido; o símbolo sozinho resiste a tamanhos bem menores.", "Em 16 e 32 px, use os arquivos de favicon, já alinhados à grade de pixels.")}
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
    <figure class="campo-cor">
      <div class="faixa" role="img" aria-label="Proporção de uso: Palha domina o campo, depois Areia e Tinta; Urucum aparece numa faixa estreita.">
        <i style="background:var(--palha);box-shadow:inset 0 0 0 1px var(--areia)"></i><i style="background:var(--areia)"></i><i style="background:var(--tinta)"></i><i style="background:var(--urucum)"></i>
      </div>
      <div class="legendas">
        <p><b>Palha</b><span class="dado">#F6F1E7</span>o campo</p>
        <p><b>Areia</b><span class="dado">#E7DFD0</span>agrupa e separa</p>
        <p><b>Tinta</b><span class="dado">#221F1A</span>texto e símbolo</p>
        <p><b>Urucum</b><span class="dado">#B4602F</span>a decisão, uma vez</p>
      </div>
      <figcaption>A faixa mostra a proporção em uso numa peça típica, não uma paleta para escolher.</figcaption>
    </figure>
    <div class="col-esq"><p class="rotulo" style="margin-bottom:14px">As quatro cores da marca e as cores de apoio</p>{cores_tabela}</div>
    <div class="col-dir">
      <div class="regras" style="grid-template-columns:1fr;row-gap:28px">
        {regras_de(C["visual"]["palette"]["rules"])}
      </div>
    </div>
    <div class="col-cheia"><p class="rotulo" style="margin-bottom:14px">Estados de operação — só em produto e infraestrutura, sempre com rótulo</p><div class="estados">{estados_html}</div></div>
    <div class="col-cheia"><p class="rotulo" style="margin-bottom:14px">Contraste verificado</p>{pares_tabela}</div>
  </div>
</section>

<section class="s" id="tipografia">
  {cab(4, "tipografia", "Editorial para a casa, sistema para a operação", "Duas famílias com licença aberta (SIL OFL 1.1) e suporte completo ao português. A Newsreader fala pela instituição; a Space Grotesk opera: corpo, interface, dados, rótulos e o nome na assinatura.")}
  <div class="corpo-s">
    <div class="especime">
      <div><p class="rotulo">Newsreader · voz institucional</p><p class="grande-inst">Ág</p><p class="alfabeto inst">ABCÇDEFGHIJKLM<br>NOPQRSTUVWXYZ<br>abcçdefghijklm<br>nopqrstuvwxyz<br>áâãéêíóôõú 0123456789</p><p style="font-size:15px;color:var(--reduzida)">{e(TY["families"][0]["use"][:1].upper() + TY["families"][0]["use"][1:])}.</p></div>
      <div><p class="rotulo">Space Grotesk · voz de sistema</p><p class="grande-sis">Ág</p><p class="alfabeto">ABCÇDEFGHIJKLM<br>NOPQRSTUVWXYZ<br>abcçdefghijklm<br>nopqrstuvwxyz<br>áâãéêíóôõú 0123456789</p><p style="font-size:15px;color:var(--reduzida)">{e(TY["families"][1]["use"][:1].upper() + TY["families"][1]["use"][1:])}.</p></div>
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
        <div class="visual demo-doc"><img src="aplicacoes/proposta-1.jpg" alt="Capa de proposta: o símbolo em escala de campo alinhado às margens da página"></div>
        {regra("Malha e célula", e(C["visual"]["composition"]["grid"]) + " " + e(C["visual"]["composition"]["rules"][0]), "A malha vem antes do fluxo: a estrutura aparece antes do conteúdo que a atravessa.", "Em capas, a própria malha do símbolo pode ser a malha da página, alinhada às margens.")}
      </div>
      <div class="dispositivo">
        <div class="visual demo-ui"><p class="rotulo">Execuções / FJ-2048</p><p class="demo-h">Execução FJ-2048</p><p class="demo-a">Três secretarias · resultado agregado pronto</p><div class="demo-b"><span class="b2">Revogar autorização</span><span class="b1"><i class="barra"></i>Liberar resultado agregado</span></div></div>
        {regra("Barra de decisão", e(C["visual"]["composition"]["rules"][1]), "É a barra central do símbolo tirada da marca e posta no ponto que decide: a peça inteira aponta para lá.", "Na vertical (1 : 2,4) quando o eixo da peça é vertical, como numa trilha.")}
      </div>
      <div class="dispositivo">
        <div class="visual"><p class="rotulo" style="position:absolute;left:40px;top:40px">Relatório técnico</p><p style="position:absolute;left:40px;top:66px;font:400 30px/1.08 var(--inst);font-variation-settings:'opsz' 48;margin:0;max-width:13em">Doze semanas de consultas conjuntas sem mover um registro</p><div class="reg-demo"><div><span>Documento</span><b>Relatório técnico</b></div><div><span>Versão</span><b>2.1</b></div><div><span>Data</span><b>30 set 2026</b></div><div><span>Identificador</span><b>IU-RT-2026-007</b></div></div></div>
        {regra("Registro", e(C["visual"]["composition"]["rules"][3]) + " " + e(D["principles"][3]["rule"]), "É a proofline na forma de desenho: a peça mostra de onde vem antes de pedir confiança.", "Em telas, o registro vira a linha de evidência; em certificados, carrega o código de verificação.")}
      </div>
      <div class="dispositivo">
        <div class="visual demo-foto"><img src="aplicacoes/apresentacao-1.jpg" alt="Capa de apresentação: o símbolo recortado pela borda, com o centro em Urucum inteiro"></div>
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
  <div class="inteira">{fig("aplicacoes/site-home.jpg", "Abertura do site institucional no computador", "<b>Site institucional.</b> A tese em escala monumental; o símbolo recortado à direita, com o centro inteiro.")}</div>
  <div class="celular">
    {fig("aplicacoes/site-celular.jpg", "Abertura do site no celular", "<b>Site no celular.</b> A malha vira uma coluna; o campo desce para baixo do texto.")}
    {fig("aplicacoes/formacao-celular.jpg", "Página de formação no celular", "<b>Formação.</b> Resultado de trabalho, não promessa motivacional.")}
    <div class="nota-celular"><p class="rotulo">Na tela pequena</p><p>A estrutura é a mesma, em uma coluna. O título continua sendo a única escala grande, a barra de decisão continua marcando uma só ação, e o registro desce para o fim da página.</p></div>
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
  <div class="micro">
    {fig("aplicacoes/cena-cracha.jpg", "Crachá impresso em fundo Tinta, com cordão, sobre a mesa", "<b>Crachá.</b> Nome na voz institucional, registro de acesso, símbolo em campo com o centro inteiro.")}
    <div class="micro-col">
      <figure><div class="palco f-b palco-email"><img src="aplicacoes/assinatura-email.jpg" alt="Assinatura de e-mail em fontes de sistema"></div><figcaption><b>Assinatura de e-mail.</b> Fontes de sistema, porque clientes de e-mail não carregam as da marca.</figcaption></figure>
      <figure><div class="palco f-p"><img src="logo/avatar-800.png" alt="Avatar: símbolo negativo sobre Tinta" class="avatar"></div><figcaption><b>Avatar.</b> Para redes e aplicativos; seguro para recorte circular.</figcaption></figure>
    </div>
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
    <div class="col-texto"><p style="font-size:15px;color:var(--reduzida)">Só escreva “ICT privada sem fins lucrativos” em peças públicas quando o estatuto do Instituto sustentar a qualificação; na dúvida, consulte o responsável pela marca.</p></div>
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
    <div class="col-esq"><div class="palco f-b palco-selo"><img src="logo/carimbo.svg" alt="Carimbo institucional em uma cor" style="width:40%"><img src="logo/carimbo-urucum.svg" alt="Carimbo institucional em Urucum" style="width:24%"></div></div>
    <div class="col-dir">
      {regra("Carimbo institucional", "Use em convênios, certificados, ofícios e documentos assinados pelo Instituto, em uma cor: Tinta, ou Urucum quando for a única decisão da peça. Serve também como matriz de relevo seco.", "Ele diz quem emite o documento; não afirma que algo foi verificado.", "Diâmetro mínimo de 25 mm; em tela, 160 px.")}
    </div>
    <div class="col-esq"><div class="palco f-p palco-selo">
      <div style="transform:scale(1.25);display:inline-grid;grid-template-columns:auto 1fr;column-gap:12px;border:1.5px solid var(--tinta);border-radius:4px;padding:12px 16px 12px 12px;background:var(--palha)">
        <img src="logo/simbolo-mono.svg" alt="" style="width:28px;height:28px">
        <div><div style="font-size:12px;font-weight:600;letter-spacing:.1em;text-transform:uppercase">Verificado <span style="font-weight:500;color:var(--reduzida)">· Instituto Urupema</span></div>
        <dl style="margin:6px 0 0;display:grid;grid-template-columns:max-content max-content;column-gap:12px;row-gap:1px;font-size:12.5px"><dt class="rotulo" style="font-size:10px;padding-top:2px">Objeto</dt><dd style="margin:0">Execução FJ-2048</dd><dt class="rotulo" style="font-size:10px;padding-top:2px">Regra</dt><dd style="margin:0">G-881 v4</dd><dt class="rotulo" style="font-size:10px;padding-top:2px">Evidência</dt><dd style="margin:0" class="dado">ev.forja/FJ-2048</dd></dl></div>
      </div>
    </div></div>
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
  <div class="corpo-s"><div class="arquivos">{biblioteca()}</div></div>
</section>

<footer class="fim escuro">
  <img src="logo/assinatura-horizontal-negativa.svg" alt="Instituto Urupema">
  <p>{e(V["boilerplates"]["curto"])}</p>
  <dl class="colofao"><div><dt>Documento</dt><dd>Guia da marca</dd></div><div><dt>Edição</dt><dd>Setembro de 2026</dd></div><div><dt>Tipografia</dt><dd>Newsreader e Space Grotesk</dd></div><div><dt>Responsável</dt><dd>Direção do Instituto</dd></div></dl>
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
