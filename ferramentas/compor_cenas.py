"""Compõe os artes reais da marca sobre cenas fotográficas (FLUX), para ver as peças físicas onde vivem.

A arte entra por reprodução fiel: é o render do modelo, multiplicado pela luz do papel ou do cartão
da cena; o carimbo entra como relevo seco, gerado da máscara do próprio master.
Uso: python3 ferramentas/compor_cenas.py <arte.png> <mascara-carimbo.png> <cracha.png>
(os três renders vêm de ferramentas/render.mjs; ver o livro, seção Aplicações)
"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter

RAIZ = Path(__file__).resolve().parent
SAIDA = RAIZ.parent / "livro" / "aplicacoes"


def luz(cena, caixa):
    """Mapa de luz da superfície branca: a cena dividida pelo seu branco típico."""
    x0, y0, x1, y1 = caixa
    reg = cena[y0:y1, x0:x1]
    branco = np.percentile(reg.reshape(-1, 3), 90, axis=0)
    # luz suave: tira poeira e grão da superfície branca, preserva o gradiente da janela
    suave = np.asarray(Image.fromarray(np.clip(reg, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(6))).astype(float)
    return np.clip(suave / branco, 0, 1.08)


def folha(arte_png, masc_png):
    cena = np.asarray(Image.open(RAIZ / "cenas" / "mesa-folha-a4.jpg").convert("RGB")).astype(float)
    x0, y0, x1, y1 = 485, 211, 1053, 971          # folha na cena
    h = y1 - y0
    w = round(h * 210 / 297)
    ox = x0 + (x1 - x0 - w) // 2
    arte = Image.open(arte_png).convert("RGB").resize((w, h), Image.LANCZOS)
    arte = np.asarray(arte.filter(ImageFilter.GaussianBlur(0.35))).astype(float) / 255
    L = luz(cena, (ox, y0, ox + w, y1))
    reg = cena[y0:y1, ox:ox + w]
    # tinta sobre papel: multiplica, com leve ganho de ponto
    tinta = np.power(arte, 1.06)
    saida = cena.copy()
    saida[y0:y1, ox:ox + w] = np.clip(reg * tinta, 0, 255)
    # relevo seco a partir da máscara do carimbo
    m = Image.open(masc_png).convert("L").resize((w, h), Image.LANCZOS)
    m = 1 - np.asarray(m).astype(float) / 255             # 1 onde há carimbo
    alt = np.asarray(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.05))).astype(float) / 255
    gy, gx = np.gradient(alt)
    # luz da janela à esquerda, um pouco de cima
    sombra = -(gx * 0.85 + gy * 0.35) * 4.2
    realce = np.clip(sombra, -0.18, 0.12)[..., None]
    # o relevo não tem tinta: tira a tinta do carimbo e aplica só luz e sombra
    area = saida[y0:y1, ox:ox + w]
    area[:] = np.clip(area * (1 + realce), 0, 255)
    Image.fromarray(saida.astype(np.uint8)).save(SAIDA / "cena-convenio.jpg", quality=90, optimize=True, progressive=True)


def cracha(cr_png):
    cena = np.asarray(Image.open(RAIZ / "cenas" / "mesa-cracha.jpg").convert("RGB")).astype(float)
    x0, y0, x1, y1 = 581, 405, 1008, 1029
    arte = Image.open(cr_png).convert("RGB").resize((x1 - x0, y1 - y0), Image.LANCZOS)
    arte = np.asarray(arte.filter(ImageFilter.GaussianBlur(0.3))).astype(float) / 255
    reg = cena[y0:y1, x0:x1]
    L = luz(cena, (x0, y0, x1, y1))
    # máscara do cartão: onde a cena é o plástico branco (exclui furo, mosquetão e mesa nos cantos)
    lum = reg.mean(axis=2)
    masc = np.clip((lum - 150) / 50, 0, 1)
    masc = np.asarray(Image.fromarray((masc * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.8))).astype(float)[..., None] / 255
    # impressão fosca sobre plástico: arte × luz, com um leve brilho do plástico por cima
    impresso = arte * 255 * L
    brilho = np.clip(L - 0.96, 0, 0.12) * 255 * 0.6
    novo = np.clip(impresso + brilho, 0, 255)
    saida = cena.copy()
    saida[y0:y1, x0:x1] = reg * (1 - masc) + novo * masc
    Image.fromarray(saida.astype(np.uint8)).save(SAIDA / "cena-cracha.jpg", quality=90, optimize=True, progressive=True)


if __name__ == "__main__":
    folha(sys.argv[1], sys.argv[2])
    cracha(sys.argv[3])
    print("cenas compostas em livro/aplicacoes")
