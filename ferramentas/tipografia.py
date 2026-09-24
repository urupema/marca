"""Converte texto nas famílias da marca em contornos SVG.

Usado para produzir as assinaturas-mestre sem dependência de fonte.
Forma (harfbuzz, com kerning) e desenha (fontTools) a partir das
mesmas fontes variáveis publicadas em livro/fontes.
"""
from functools import lru_cache
from pathlib import Path

import uharfbuzz as hb
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.boundsPen import BoundsPen
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

FONTES = Path(__file__).resolve().parent.parent / "livro" / "fontes"
ARQUIVOS = {
    "newsreader": FONTES / "Newsreader-Variavel.woff2",
    "space-grotesk": FONTES / "SpaceGrotesk-Variavel.woff2",
}


@lru_cache(maxsize=None)
def _instancia(familia, eixos):
    fonte = TTFont(ARQUIVOS[familia])
    return instantiateVariableFont(fonte, dict(eixos), inplace=False)


@lru_cache(maxsize=None)
def _hb(familia, eixos):
    # harfbuzz não lê woff2; converte para sfnt em memória
    import io
    buf = io.BytesIO()
    fonte = TTFont(ARQUIVOS[familia])
    fonte.flavor = None
    fonte.save(buf)
    face = hb.Face(buf.getvalue())
    font = hb.Font(face)
    font.set_variations(dict(eixos))
    return font, face.upem


def contorno(texto, familia, tamanho, eixos=(("wght", 400),), rastreio=0.0, x=0.0, y=0.0):
    """Devolve (d, largura, caixa) do texto em contornos.

    tamanho em unidades do SVG; rastreio em em (0.1 = 10% do corpo);
    (x, y) é a origem na linha de base.
    """
    eixos = tuple(sorted(eixos))
    font, upem = _hb(familia, eixos)
    buf = hb.Buffer()
    buf.add_str(texto)
    buf.guess_segment_properties()
    hb.shape(font, buf, {"kern": True, "liga": True})
    glifos = _instancia(familia, eixos).getGlyphSet()
    ordem = _instancia(familia, eixos).getGlyphOrder()
    escala = tamanho / upem
    pen = SVGPathPen(glifos)
    limites = BoundsPen(glifos)
    cursor = 0.0
    n = len(buf.glyph_infos)
    for i, (info, pos) in enumerate(zip(buf.glyph_infos, buf.glyph_positions)):
        nome = ordem[info.codepoint]
        gx = x + (cursor + pos.x_offset) * escala
        gy = y - pos.y_offset * escala
        t = (escala, 0, 0, -escala, gx, gy)
        glifos[nome].draw(TransformPen(pen, t))
        glifos[nome].draw(TransformPen(limites, t))
        cursor += pos.x_advance
        if i < n - 1:
            cursor += rastreio * upem
    return pen.getCommands(), cursor * escala, limites.bounds


def glifos(texto, familia, tamanho, eixos=(("wght", 400),), rastreio=0.0):
    """Lista (glifo, x_inicial, avanço) em unidades do SVG, para compor em curva."""
    eixos = tuple(sorted(eixos))
    font, upem = _hb(familia, eixos)
    buf = hb.Buffer()
    buf.add_str(texto)
    buf.guess_segment_properties()
    hb.shape(font, buf, {"kern": True})
    inst = _instancia(familia, eixos)
    ordem = inst.getGlyphOrder()
    escala = tamanho / upem
    saida, cursor = [], 0.0
    for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
        avanco = (pos.x_advance + rastreio * upem) * escala
        saida.append((ordem[info.codepoint], cursor, pos.x_advance * escala))
        cursor += avanco
    largura = cursor - rastreio * upem * escala
    return saida, largura, inst.getGlyphSet(), escala


def desenhar(glyphset, nome, matriz):
    pen = SVGPathPen(glyphset)
    glyphset[nome].draw(TransformPen(pen, matriz))
    return pen.getCommands()


def metricas(familia, eixos=(("wght", 400),)):
    """Altura de maiúscula e de x em unidades por em (0-1)."""
    f = _instancia(familia, tuple(sorted(eixos)))
    os2 = f["OS/2"]
    upem = f["head"].unitsPerEm
    return {
        "maiuscula": os2.sCapHeight / upem,
        "x": os2.sxHeight / upem,
        "ascendente": os2.sTypoAscender / upem,
        "descendente": -os2.sTypoDescender / upem,
    }
