# Bibliotecas de terceiros

Copiadas do pacote npm de cada versão, só os arquivos de distribuição usados e a licença.
Servidas pelo próprio app (WhiteNoise): nenhum CDN em tempo de execução, e a CSP aceita só `'self'`.
Comentários `sourceMappingURL` foram removidos, porque os mapas não são copiados.

| Pasta | Pacote npm | Licença |
|---|---|---|
| `bootstrap-5.3.3/` | `bootstrap@5.3.3` | MIT |
| `jquery-3.7.1/` | `jquery@3.7.1` | MIT |
| `select2-4.1.0-rc.0/` | `select2@4.1.0-rc.0` | MIT |
| `jquery-mask-1.14.16/` | `jquery-mask-plugin@1.14.16` | MIT |
| `chartjs-4.4.4/` | `chart.js@4.4.4` | MIT |

Para atualizar: `npm pack <pacote>@<versão>`, copie os mesmos arquivos para uma pasta com a nova
versão no nome, troque os caminhos em `templates/base.html` (ou no template que usa) e apague a pasta antiga.
