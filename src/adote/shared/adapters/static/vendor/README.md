# Bibliotecas de terceiros

Copiadas do pacote npm de cada versão, só os arquivos de distribuição usados e a licença.
Servidas pelo próprio app (WhiteNoise): nenhum CDN em tempo de execução, e a CSP aceita só `'self'`.
Comentários `sourceMappingURL` foram removidos, porque os mapas não são copiados.

| Pasta | Pacote npm | Licença |
|---|---|---|
| `tom-select-2.6.2/` | `tom-select@2.6.2` (build `complete`, com plugins) | Apache-2.0 |
| `chartjs-4.5.1/` | `chart.js@4.5.1` | MIT |
| `fontawesome-7.3.1/` | `@fortawesome/fontawesome-free@7.3.1` (CSS e webfonts) | Ícones CC BY 4.0, fontes OFL 1.1, código MIT |
| `fontsource-nunito-5.3.0/` | `@fontsource-variable/nunito@5.3.0` (latin, eixo de peso) | OFL 1.1 |
| `fontsource-inter-5.3.0/` | `@fontsource-variable/inter@5.3.0` (latin, eixo de peso) | OFL 1.1 |

O CSS do app é Tailwind, compilado de `assets/css/app.css` (ver `package.json`); não há Bootstrap
nem jQuery. O select de múltipla escolha é o Tom Select; máscaras, menu, diálogos e avisos são JS puro
em `static/adote/js/`.

Para atualizar: `npm pack <pacote>@<versão>`, copie os mesmos arquivos para uma pasta com a nova
versão no nome, troque os caminhos nos templates (ou em `css/fonts.css`) e apague a pasta antiga.
