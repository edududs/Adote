# 0002. Contextos `accounts`, `pets`, `adoption` e `shared`

**Status:** decidido · **Data:** 2026-10-09

## Contexto

Os apps antigos (`usuarios`, `divulgar`, `adotar`) eram nomes de telas, não de conceitos: `divulgar`
tinha a view de "ver pedidos de adoção" e o JSON do painel; `adotar` tinha o modelo de pedido.

## Decisão

- `accounts`: quem é a pessoa (perfil, credenciais).
- `pets`: o que foi divulgado (pet, catálogo de raças e características, fotos).
- `adoption`: o encontro entre um pet e um adotante (pedidos, decisão), e as páginas que dependem
  dele: mural, página do pet, meus pets, pedidos, painel.
- `shared`: value objects que mais de um contexto usa (telefone, CEP, UF), portas de relógio e
  e-mail, layout e estáticos.
- `demo`: só composição; sem domínio.

Cada contexto tem seu app Django em `adapters/`, com `label` curto (`accounts`, `pets`, `adoption`).
Um contexto referencia outro só por identificador. Quando `pets` precisa saber se um pet foi adotado,
declara a porta `AdoptionLedger`, e `adoption/adapters/bridges.py` a implementa.

## Consequências

- O mural e a página do pet ficam em `adoption`, embora mostrem pets: o que eles respondem é "posso
  adotar este pet?", que é pergunta de adoção.
- `adoption/adapters` importa os models de `pets` (chave estrangeira e consultas). Acoplamento entre
  adaptadores é aceito; entre núcleos, não.
