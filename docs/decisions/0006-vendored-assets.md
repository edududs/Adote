# 0006. Bibliotecas de front servidas pela aplicação

**Status:** decidido · **Data:** 2026-10-09

## Contexto

A versão antiga carregava jQuery, Bootstrap (um alfa), Select2, jQuery Mask e Chart.js de quatro CDNs,
um deles sem versão fixa (`chart.js` sem número). Cada CDN é um terceiro que pode mudar o arquivo,
sair do ar ou registrar quem visita, e obriga a CSP a aceitar essas origens.

## Decisão

Copiar os arquivos de distribuição de cada biblioteca, de uma versão fixa, para
`shared/adapters/static/vendor/<nome>-<versão>/`, com a licença ao lado. O WhiteNoise os serve com hash
no nome e compressão. A CSP aceita script, estilo e fonte só de `'self'`. Um teste falha se um template
apontar para outra origem.

## Consequências

- ~740 KB no repositório, marcados como `linguist-vendored`.
- Atualizar uma biblioteca é trocar uma pasta (procedimento no README da pasta).
- A aplicação funciona sem acesso à internet, exceto o preenchimento por CEP.
