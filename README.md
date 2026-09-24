# Marca do Instituto Urupema

O livro da marca é [`docs/index.html`](docs/index.html), publicado pelo GitHub Pages em https://urupema.github.io/marca/ — regras, masters, cores, fontes e modelos, na pasta `docs/`.

- `contrato/brand-spec.json` — decisões em vigor, em inglês, para quem opera a marca; nomes próprios (Palha, Tinta, Urucum, Forja…) e as frases da marca ficam como são.
- `ferramentas/livro-textos.pt-BR.json` — a redação em português dessas decisões no livro; muda junto com o contrato.
- `ferramentas/` — reproduz os masters, as variáveis de cor, os renders e o livro a partir do contrato:
  `python3 ferramentas/gerar_logos.py`, `python3 ferramentas/gerar_tokens.py`, `bash ferramentas/renderizar_aplicacoes.sh`, `python3 ferramentas/gerar_livro.py` (Python com fonttools e uharfbuzz; `npm i` em `ferramentas/` para o Playwright).
- `referencias/briefing-mestre.docx` — o mandato desta etapa.
- `docs/fotografia/provisoria-*.jpg` — fotos provisórias, até existir acervo real; para trocar, substitua o arquivo mantendo o nome e rode `bash ferramentas/renderizar_aplicacoes.sh` e `python3 ferramentas/gerar_livro.py`.
