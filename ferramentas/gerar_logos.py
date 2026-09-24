"""Gera os masters vetoriais da marca em docs/logo.

O símbolo é patrimônio fixo: a geometria abaixo reproduz o master
recebido (285 x 285) sem alteração. As assinaturas convertem o
lettering em contornos, então nenhum arquivo depende de fonte instalada.

Uso: python3 ferramentas/gerar_logos.py
"""
from pathlib import Path

from tipografia import contorno

SAIDA = Path(__file__).resolve().parent.parent / "docs" / "logo"

PALHA = "#F6F1E7"
TINTA = "#221F1A"
URUCUM = "#B4602F"
TINTA_REDUZIDA = "#6D665C"

# Nove barras da malha 3 x 3: (x, y, largura, altura). A quinta é o centro.
BARRAS = [
    (0, 23.5, 81, 34), (125.5, 0, 34, 81), (204, 23.5, 81, 34),
    (23.5, 102, 34, 81), (102, 125.5, 81, 34), (227.5, 102, 34, 81),
    (0, 227.5, 81, 34), (125.5, 204, 34, 81), (204, 227.5, 81, 34),
]
CENTRO = 4
LADO = 285
CELULA = LADO / 3  # unidade de respiro: um terço do símbolo

# Assinatura: proporções relativas ao lado do símbolo, calibradas no render.
URUPEMA_CORPO = 0.785 * LADO      # altura de x ~ 0,40 do símbolo
INSTITUTO_CORPO = 0.205 * LADO    # altura de maiúscula ~ 0,145 do símbolo
INSTITUTO_RASTREIO = 0.21
TOPO_OPTICO = 23.5                 # topo das barras horizontais
BASE_OPTICA = 261.5                # base das barras horizontais
AFASTAMENTO = 0.19 * LADO          # símbolo → texto


def barras(cor, centro, dx=0.0, dy=0.0, escala=1.0):
    partes = []
    for i, (x, y, w, h) in enumerate(BARRAS):
        c = centro if i == CENTRO else cor
        partes.append(
            f'<rect x="{dx + x * escala:.3f}" y="{dy + y * escala:.3f}" '
            f'width="{w * escala:.3f}" height="{h * escala:.3f}" '
            f'rx="{17 * escala:.3f}" fill="{c}"/>'
        )
    return "".join(partes)


def svg(largura, altura, titulo, desc, corpo, fundo=None):
    fundo_rect = f'<rect width="{largura:.2f}" height="{altura:.2f}" fill="{fundo}"/>' if fundo else ""
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{largura:.2f}" height="{altura:.2f}" '
        f'viewBox="0 0 {largura:.2f} {altura:.2f}" role="img" aria-labelledby="t d">'
        f'<title id="t">{titulo}</title><desc id="d">{desc}</desc>'
        f"{fundo_rect}{corpo}</svg>\n"
    )


def palavra(x, cor_instituto, cor_urupema, y_topo=TOPO_OPTICO, y_base=BASE_OPTICA, alinhar="esquerda"):
    """Bloco INSTITUTO / urupema com topo e base ópticos dados."""
    inst_d, inst_w, inst_b = contorno("INSTITUTO", "space-grotesk", INSTITUTO_CORPO,
                                      (("wght", 500),), INSTITUTO_RASTREIO)
    uru_d, uru_w, uru_b = contorno("urupema", "space-grotesk", URUPEMA_CORPO, (("wght", 600),))
    # topo da maiúscula de INSTITUTO em y_topo; base de urupema em y_base
    inst_y = y_topo - inst_b[1]
    if alinhar == "centro":
        largura = max(inst_b[2] - inst_b[0], uru_b[2] - uru_b[0])
        inst_x = x + (largura - (inst_b[2] - inst_b[0])) / 2 - inst_b[0]
        uru_x = x + (largura - (uru_b[2] - uru_b[0])) / 2 - uru_b[0]
    else:
        inst_x = x - inst_b[0]
        uru_x = x - uru_b[0]
    inst_d, _, ib = contorno("INSTITUTO", "space-grotesk", INSTITUTO_CORPO,
                             (("wght", 500),), INSTITUTO_RASTREIO, inst_x, inst_y)
    uru_d, _, ub = contorno("urupema", "space-grotesk", URUPEMA_CORPO, (("wght", 600),), 0, uru_x, y_base)
    corpo = f'<path d="{inst_d}" fill="{cor_instituto}"/><path d="{uru_d}" fill="{cor_urupema}"/>'
    direita = max(ib[2], ub[2])
    baixo = ub[3]
    return corpo, direita, baixo


VARIANTES = {
    # nome: (cor das barras, cor do centro, cor INSTITUTO, cor urupema, fundo, descrição)
    "": (TINTA, URUCUM, TINTA_REDUZIDA, TINTA, None, "Tinta e Urucum, para fundos claros"),
    "-negativa": (PALHA, URUCUM, PALHA, PALHA, None, "Palha e Urucum, para fundo Tinta"),
    "-mono": (TINTA, TINTA, TINTA, TINTA, None, "Uma cor, Tinta: carimbo, relevo seco, fax, gravação"),
    "-mono-negativa": (PALHA, PALHA, PALHA, PALHA, None, "Uma cor, Palha, sobre fundo escuro"),
}


def simbolos():
    for sufixo, (cor, centro, _, _, _, desc) in VARIANTES.items():
        corpo = barras(cor, centro)
        (SAIDA / f"simbolo{sufixo}.svg").write_text(
            svg(LADO, LADO, f"Símbolo do Instituto Urupema{(' — ' + desc) if sufixo else ''}",
                "Nove barras arredondadas em malha três por três; a barra central é a decisão.", corpo))


def simbolos_campo():
    """Símbolo em escala de campo: barras em tom de fundo, centro em Urucum.

    Uso exclusivo em escala de campo (capas, aberturas), recortado pelo quadro.
    """
    for sufixo, cor, desc in (("", "#E7DFD0", "Areia sobre Palha"), ("-escuro", "#2D2A24", "Tinta elevada sobre Tinta")):
        (SAIDA / f"simbolo-campo{sufixo}.svg").write_text(
            svg(LADO, LADO, f"Símbolo em escala de campo — {desc}",
                "Oito barras no tom do fundo e a barra central em Urucum; só para escala de campo.", barras(cor, URUCUM)))


def assinatura_horizontal():
    for sufixo, (cor, centro, ci, cu, _, desc) in VARIANTES.items():
        m = CELULA  # respiro embutido de uma célula
        corpo_texto, direita, baixo = palavra(m + LADO + AFASTAMENTO, ci, cu, m + TOPO_OPTICO, m + BASE_OPTICA)
        corpo = barras(cor, centro, m, m) + corpo_texto
        largura = direita + m
        altura = LADO + 2 * m
        (SAIDA / f"assinatura-horizontal{sufixo}.svg").write_text(
            svg(largura, altura, f"Assinatura horizontal do Instituto Urupema — {desc}",
                "Símbolo à esquerda, INSTITUTO sobre urupema. Inclui a área de respiro de uma célula.", corpo))


def assinatura_vertical():
    for sufixo, (cor, centro, ci, cu, _, desc) in VARIANTES.items():
        m = CELULA
        # mede o bloco de texto para centralizar
        _, dir0, _ = palavra(0, ci, cu, 0, 0, "centro")
        largura_texto = dir0
        largura = max(LADO, largura_texto) + 2 * m
        sx = (largura - LADO) / 2
        topo_texto = m + LADO + 0.30 * LADO
        base_texto = topo_texto + (BASE_OPTICA - TOPO_OPTICO)
        corpo_texto, _, baixo = palavra((largura - largura_texto) / 2, ci, cu, topo_texto, base_texto, "centro")
        corpo = barras(cor, centro, sx, m) + corpo_texto
        altura = baixo + m
        (SAIDA / f"assinatura-vertical{sufixo}.svg").write_text(
            svg(largura, altura, f"Assinatura vertical do Instituto Urupema — {desc}",
                "Símbolo centralizado sobre INSTITUTO e urupema. Inclui a área de respiro de uma célula.", corpo))


def assinatura_produto(nome, arquivo):
    """Nome do produto + linha de endosso com o símbolo reduzido.

    O único Urucum da assinatura é o centro do símbolo de endosso.
    """
    from tipografia import metricas
    for sufixo, (cor, centro, ci, cu, _, desc) in list(VARIANTES.items())[:2]:
        m = CELULA
        corpo_nome = 1.05 * LADO
        d_nome, w_nome, b_nome = contorno(nome, "space-grotesk", corpo_nome, (("wght", 600),))
        cap = metricas("space-grotesk")["maiuscula"] * corpo_nome
        x0 = m - b_nome[0]
        base_nome = m + cap
        d_nome, _, bn = contorno(nome, "space-grotesk", corpo_nome, (("wght", 600),), 0, x0, base_nome)
        # linha de endosso: símbolo com lado = 0,36 do lado original
        esc = 0.36
        topo_endosso = base_nome + 0.40 * LADO
        simb = barras(cor, centro, m, topo_endosso, esc)
        corpo_endosso = 0.25 * LADO
        cap_e = metricas("space-grotesk")["maiuscula"] * corpo_endosso
        base_e = topo_endosso + (LADO * esc) / 2 + cap_e / 2
        xe = m + LADO * esc + 0.13 * LADO
        d1, w1, b1 = contorno("um produto do ", "space-grotesk", corpo_endosso, (("wght", 400),), 0, xe, base_e)
        d2, w2, b2 = contorno("Instituto Urupema", "space-grotesk", corpo_endosso, (("wght", 600),), 0, xe + w1, base_e)
        cor_apoio = TINTA_REDUZIDA if sufixo == "" else PALHA
        corpo = (f'<path d="{d_nome}" fill="{cu}"/>' + simb +
                 f'<path d="{d1}" fill="{cor_apoio}"/><path d="{d2}" fill="{cu}"/>')
        largura = max(bn[2], b2[2]) + m
        altura = topo_endosso + LADO * esc + m
        (SAIDA / f"{arquivo}{sufixo}.svg").write_text(
            svg(largura, altura, f"{nome} — um produto do Instituto Urupema ({desc})",
                "Assinatura endossada: nome do produto sobre a linha de endosso do Instituto.", corpo))


def carimbo():
    """Carimbo institucional circular, uma cor. Não é selo de verificação."""
    import math
    from tipografia import glifos, desenhar, metricas
    D = 1000.0
    cx = cy = D / 2
    r_ext = 480.0
    traco = 10.0
    corpo_txt = 58.0
    cap = metricas("newsreader", (("wght", 500), ("opsz", 24)))["maiuscula"] * corpo_txt
    r_in = 355.0             # linha de base do texto superior
    r_out = r_in + cap       # topo das maiúsculas
    r_anel = r_out + 38.0    # anel externo do texto
    r_anel_in = r_in - 38.0  # anel interno
    eixos = (("wght", 500), ("opsz", 24))

    def arco(texto, superior, corpo, rastreio, graus_max):
        gs, largura, glyphset, esc = glifos(texto, "newsreader", corpo, eixos, rastreio)
        cap_atual = metricas("newsreader", eixos)["maiuscula"] * corpo
        meio_anel = (r_in + r_out) / 2
        raio = meio_anel - cap_atual / 2 if superior else meio_anel + cap_atual / 2
        # espaçamento medido no meio da altura das maiúsculas, não na linha de base
        raio_medida = meio_anel
        if math.degrees(largura / raio_medida) > graus_max:
            return arco(texto, superior, corpo * 0.97, rastreio, graus_max)
        out = []
        for nome, x, av in gs:
            meio = x + av / 2 - largura / 2
            a = meio / raio_medida
            if superior:
                px, py, rot = cx + raio * math.sin(a), cy - raio * math.cos(a), a
            else:
                px, py, rot = cx + raio * math.sin(a), cy + raio * math.cos(a), -a
            c, s_ = math.cos(rot), math.sin(rot)
            # (gx, gy) em unidades da fonte → u = esc*gx - av/2, v = -esc*gy
            # x' = px + c*u - s*v ; y' = py + s*u + c*v
            # fontTools: (xx, xy, yx, yy, dx, dy) → x' = xx*x + yx*y + dx ; y' = xy*x + yy*y + dy
            m = (c * esc, s_ * esc, s_ * esc, -c * esc, px - c * av / 2, py - s_ * av / 2)
            out.append(desenhar(glyphset, nome, m))
        return out

    for sufixo, cor, desc in (("", TINTA, "Tinta"), ("-urucum", URUCUM, "Urucum, como única decisão da peça"),
                              ("-negativo", PALHA, "Palha sobre fundo escuro")):
        partes = (arco("INSTITUTO URUPEMA", True, corpo_txt, 0.2, 132)
                  + arco("REFINAR TECNOLOGIA EM BEM COMUM", False, corpo_txt * 0.8, 0.14, 138))
        texto = "".join(f'<path d="{d}"/>' for d in partes)
        # separadores: duas barras curtas nas posições de 3 e 9 horas
        rm = (r_in + r_out) / 2
        bl, be = 40.0, 16.8
        sep = (f'<rect x="{cx - rm - bl / 2:.2f}" y="{cy - be / 2:.2f}" width="{bl}" height="{be}" rx="{be / 2}"/>'
               f'<rect x="{cx + rm - bl / 2:.2f}" y="{cy - be / 2:.2f}" width="{bl}" height="{be}" rx="{be / 2}"/>')
        esc = 300.0 / LADO
        simb = barras(cor, cor, cx - 150, cy - 150, esc)
        aneis = (f'<circle cx="{cx}" cy="{cy}" r="{r_anel}" fill="none" stroke="{cor}" stroke-width="{traco}"/>'
                 f'<circle cx="{cx}" cy="{cy}" r="{r_anel_in}" fill="none" stroke="{cor}" stroke-width="{traco * 0.5}"/>')
        corpo = f'<g fill="{cor}">{texto}{sep}</g>{aneis}{simb}'
        (SAIDA / f"carimbo{sufixo}.svg").write_text(
            svg(D, D, f"Carimbo institucional do Instituto Urupema — {desc}",
                "Anel com INSTITUTO URUPEMA e a tese; símbolo ao centro, em uma cor. Autentica documentos do Instituto; não atesta verificação.", corpo))


def favicon_ajustado(px, comprimento, espessura, centros):
    """Símbolo alinhado à grade de pixels para 16 e 32 px (mesma malha, barras inteiras)."""
    partes = []
    for i, (x, y, w, h) in enumerate(BARRAS):
        linha, coluna = i // 3, i % 3
        horizontal = w > h
        cw, ch = (comprimento, espessura) if horizontal else (espessura, comprimento)
        cx, cy = centros[coluna], centros[linha]
        cor = URUCUM if i == CENTRO else TINTA
        partes.append(f'<rect x="{cx - cw / 2:g}" y="{cy - ch / 2:g}" width="{cw}" height="{ch}" rx="{espessura / 2:g}" fill="{cor}"/>')
    (SAIDA / f"favicon-{px}.svg").write_text(
        svg(px, px, "Instituto Urupema", f"Símbolo ajustado à grade de {px} pixels.", "".join(partes)))


def favicon_e_avatar():
    favicon_ajustado(32, 10, 4, (5, 16, 27))
    favicon_ajustado(16, 6, 2, (3, 8, 13))
    # favicon: símbolo ocupando o quadro, sem fundo
    (SAIDA / "favicon.svg").write_text(svg(LADO, LADO, "Instituto Urupema", "Símbolo para favicon.", barras(TINTA, URUCUM)))
    # avatar: campo Tinta, símbolo negativo com respiro para recorte circular
    L = 1000.0
    lado_s = 0.46 * L
    esc = lado_s / LADO
    corpo = barras(PALHA, URUCUM, (L - lado_s) / 2, (L - lado_s) / 2, esc)
    (SAIDA / "avatar.svg").write_text(svg(L, L, "Avatar do Instituto Urupema",
                                          "Símbolo negativo sobre Tinta, seguro para recorte circular.", corpo, TINTA))


if __name__ == "__main__":
    SAIDA.mkdir(parents=True, exist_ok=True)
    simbolos()
    simbolos_campo()
    assinatura_horizontal()
    assinatura_vertical()
    assinatura_produto("Forja", "forja-assinatura")
    carimbo()
    favicon_e_avatar()
    for f in sorted(SAIDA.glob("*.svg")):
        print(f.name)
