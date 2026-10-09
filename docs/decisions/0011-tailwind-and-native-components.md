# 0011. Tailwind no lugar do Bootstrap, componentes nativos

**Status:** decidido · **Data:** 2026-10-09 · **Substitui:** D-006

## Contexto

O visual da primeira versão era o Bootstrap quase sem personalização, com jQuery, Select2 e jQuery
Mask para máscaras e selects. A aparência era de protótipo, e personalizar o Bootstrap compilado
significava brigar com cores e espaçamentos fixos no CSS dele.

## Decisão

- **Tailwind 4.3**, configurado no próprio CSS (`assets/css/app.css`): os tokens de cor, fonte,
  sombra e animação ficam em `@theme`; os componentes repetidos (`.btn`, `.card`, `.badge`, `.input`,
  `.pet-card`, `.toast`...) em `@layer components` com `@apply`; o resto é utilitário no template.
- A CLI oficial (`@tailwindcss/cli`) é a única dependência Node, de desenvolvimento. O CSS compilado
  e minificado é versionado em `static/adote/css/app.css`, então rodar ou publicar o app não exige
  Node. O CI recompila e falha se o arquivo versionado estiver desatualizado.
- **Sem Bootstrap e sem jQuery.** Menu do celular e confirmação são `<dialog>` nativos; filtros que
  recolhem são `<details>`; toasts, máscaras, prévia da foto e animações são JS puro. O select
  múltiplo é o Tom Select, que não depende de jQuery.
- **Identidade:** fundo creme, ameixa como âncora, verde-azulado para ação, vinho para o momento da
  adoção, mel como acento; Nunito nos títulos e Inter no texto, servidas pelo app.
- **Movimento:** só `transform` e `opacity`, todo sob `motion-safe:` ou checando
  `prefers-reduced-motion` no JS.

## Consequências

- Menos JS e CSS de terceiros (sem jQuery, Select2, jQuery Mask e Bootstrap) e controle total do visual.
- Mudar uma classe num template exige recompilar o CSS (`uv run poe css`, ou `poe css-watch` durante
  o trabalho).
- Os prints em `docs/screens/` são a referência visual de cada tela.

## Alternativas descartadas

- **Bootstrap com tema próprio (Sass).** Exige o pipeline de Sass e continua com a estrutura e o
  JavaScript do Bootstrap.
- **Bootstrap e Tailwind juntos.** Resets e nomes de classe em conflito, e CSS duplicado.
- **Tailwind por CDN (Play CDN).** Compila no navegador, não é para produção e viola a CSP `'self'`.
