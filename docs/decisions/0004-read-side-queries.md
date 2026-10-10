# 0004. Escrita pelo domínio, leitura direta do ORM

**Status:** decidido · **Data:** 2026-10-09

## Contexto

As páginas precisam de listas com junções, filtros, contagens e paginação (mural, pedidos recebidos,
painel). Reconstruir agregados para cada linha seria lento e não acrescentaria regra nenhuma.

## Decisão

Comandos passam por caso de uso e agregado. Leituras de página são funções em
`adapters/queries.py`, que devolvem querysets prontos para o template. Toda consulta que poderia
mostrar dado de outra pessoa recebe quem está vendo e filtra por isso na própria consulta. O único
ponto em que a página precisa de regra, "o que esta pessoa pode fazer aqui", vem do agregado (`actions_for`).

## Consequências

- O painel faz uma consulta para adoções por raça, em vez de uma por raça como antes.
- A autorização de leitura vive na consulta, e os testes de view provam a matriz inteira.
- Se uma leitura começar a precisar de regra de negócio, ela vira consulta do domínio, não `if` no template.
