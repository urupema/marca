# Marca do Instituto Urupema

O livro da marca é [`livro/index.html`](livro/index.html): regras, masters, cores, fontes e modelos, na pasta `livro/`.

- `contrato/brand-spec.json` — decisões em vigor, para quem opera a marca; não publicar junto do livro.
- `ferramentas/` — reproduz os masters, as variáveis de cor, os renders e o livro a partir do contrato:
  `python3 ferramentas/gerar_logos.py`, `python3 ferramentas/gerar_tokens.py`, `bash ferramentas/renderizar_aplicacoes.sh`, `python3 ferramentas/gerar_livro.py` (Python com fonttools e uharfbuzz; `npm i` em `ferramentas/` para o Playwright).
- `referencias/briefing-mestre.docx` — o mandato desta etapa.
