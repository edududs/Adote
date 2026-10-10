# 0003. Um agregado por pet: `AdoptionProcess`

**Status:** decidido · **Data:** 2026-10-09

## Contexto

As regras importantes da adoção cruzam pedidos: só uma aprovação por pet; aprovar recusa os outros;
um adotante não pede duas vezes. Na versão antiga, cada pedido era salvo sozinho, aprovar não recusava
os outros, dois pedidos podiam ser aprovados, e o status do pet era um campo mudado à parte (e às
vezes esquecido).

## Decisão

- O agregado é o processo de adoção de um pet: `pet_id`, `owner_id` e todos os pedidos. As
  invariantes são validadas no construtor; os comandos (`request`, `approve`, `reject`, `withdraw`)
  devolvem um processo novo com os eventos que causaram.
- A porta `AdoptionProcesses.change(pet_id, fn)` carrega o processo inteiro sob
  `SELECT ... FOR UPDATE` na linha do pet, aplica `fn` e grava o que mudou na mesma transação.
- "Adotado" é calculado: existe um pedido aprovado. O pet não tem campo de status.
- O banco repete as invariantes: índice único parcial "um aprovado por pet", índice único parcial
  "um pedido vivo por adotante e pet", e uma checagem de coerência entre situação e `decided_at`.

## Consequências

- Duas aprovações simultâneas do mesmo pet se serializam no lock; a segunda vê o pedido já decidido.
- Carregar todos os pedidos a cada mudança é barato: um pet tem poucos pedidos.
- Uma escrita que contorne o domínio (admin, shell) esbarra nas constraints.
- Não há como o pet ficar "adotado" sem adotante, ou o contrário.

## Alternativas descartadas

- **Pedido como agregado.** As regras entre pedidos ficariam fora de qualquer fronteira de consistência.
- **Pet como agregado, com os pedidos dentro.** Misturaria a descrição do pet (de `pets`) com a decisão
  (de `adoption`), e editar a descrição travaria os pedidos.
- **Status gravado no pet.** Duas fontes para o mesmo fato.
