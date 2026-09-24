// Exporta PNGs a partir dos masters SVG (Chromium do Playwright).
// Uso: node ferramentas/exportar_png.mjs  (a partir da raiz do repositório)
import { chromium } from 'playwright';
import path from 'node:path';
import fs from 'node:fs';
const raiz = path.resolve('livro/logo');
const saidas = [
  ['favicon-16.svg', 'favicon-16.png', 16, 16, null, 0],
  ['favicon-32.svg', 'favicon-32.png', 32, 32, null, 0],
  ['favicon.svg', 'favicon-48.png', 48, 48, null, 0],
  ['simbolo.svg', 'icone-app-180.png', 180, 180, '#F6F1E7', 0.2],
  ['simbolo.svg', 'icone-app-512.png', 512, 512, '#F6F1E7', 0.2],
  ['avatar.svg', 'avatar-800.png', 800, 800, null, 0],
  ['assinatura-horizontal.svg', 'assinatura-horizontal-1200.png', 1200, null, null, 0],
  ['assinatura-horizontal-negativa.svg', 'assinatura-horizontal-negativa-1200.png', 1200, null, '#221F1A', 0],
];
const exe = process.env.CHROMIUM || '/opt/pw-browsers/chromium-1194/chrome-linux/chrome';
const b = await chromium.launch({ executablePath: exe, args: ['--no-sandbox'] });
for (const [src, out, w, h, fundo, pad] of saidas) {
  const p = await b.newPage({ viewport: { width: w, height: h || w }, deviceScaleFactor: 1 });
  const url = 'data:image/svg+xml;base64,' + fs.readFileSync(path.join(raiz, src)).toString('base64');
  await p.setContent(`<html><body style="margin:0;background:${fundo || 'transparent'}">
    <img id="i" src="${url}" style="display:block;width:${w * (1 - 2 * pad)}px;margin:${w * pad}px"></body></html>`);
  await p.waitForLoadState('load');
  const box = await (await p.$('#i')).boundingBox();
  await p.setViewportSize({ width: w, height: Math.round(box.height + 2 * w * pad) });
  await p.screenshot({ path: path.join(raiz, out), omitBackground: !fundo });
  await p.close();
}
await b.close();
