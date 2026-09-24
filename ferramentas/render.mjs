// Renderiza elementos de uma página HTML em PNG, para olhar as aplicações.
// Uso: node ferramentas/render.mjs <arquivo.html> <seletor> <saida-prefixo> [largura] [altura] [escala] [--pagina-inteira]
import { chromium } from 'playwright';
import { pathToFileURL } from 'node:url';
import path from 'node:path';
const [,, arquivo, seletor, saida, w = '1440', h = '900', escala = '2', ...resto] = process.argv;
const exe = process.env.CHROMIUM || '/opt/pw-browsers/chromium-1194/chrome-linux/chrome';
const b = await chromium.launch({ executablePath: exe, args: ['--no-sandbox'] });
const p = await b.newPage({ viewport: { width: +w, height: +h }, deviceScaleFactor: +escala });
await p.goto(pathToFileURL(path.resolve(arquivo)).href, { waitUntil: 'load' });
await p.evaluate(() => document.fonts.ready);
await p.waitForTimeout(200);
if (seletor === 'viewport') {
  await p.screenshot({ path: `${saida}.png`, fullPage: resto.includes('--pagina-inteira') });
} else {
  const els = await p.$$(seletor);
  for (let i = 0; i < els.length; i++) await els[i].screenshot({ path: els.length > 1 ? `${saida}-${i + 1}.png` : `${saida}.png` });
}
await b.close();
