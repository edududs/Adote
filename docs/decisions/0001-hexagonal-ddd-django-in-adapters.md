# 0001. Hexagonal com DDD, Django nos adaptadores

**Status:** decidido · **Data:** 2026-10-09

## Contexto

A versão anterior tinha regra de negócio espalhada nas views: aprovar um pedido era um `if` na
view, sem conferir quem aprovava; o "pet adotado" era um campo que a view mudava à mão. Testar uma
regra exigia subir HTTP e banco, e não havia teste nenhum.

## Decisão

Domínio e aplicação em Python puro: entidades e value objects em Pydantic congelado, casos de uso
como dataclasses que recebem portas (`Protocol`). O Django entra como adaptador: models, migrations,
views, formulários e templates moram em `adapters/`, e `composition.py` liga casos de uso a
adaptadores reais. Um teste lê a AST de `domain/` e `application/` e falha com qualquer import
proibido.

## Consequências

- Regras testáveis sem banco, com milhares de exemplos por segundo (a máquina de estados roda 300
  sequências no agregado em poucos segundos).
- Cada porta tem dois adaptadores (fake e Django) e um teste de contrato que os mantém iguais.
- Há mapeamento entre linha do ORM e entidade. É código a mais, aceito em troca da fronteira.
- O admin do Django continua disponível, mas pedidos de adoção ficam só leitura nele: decidir
  passa pelo caso de uso, que mantém as invariantes e avisa as pessoas.

## Alternativas descartadas

- **Django "gordo" com regras nos models.** Menos código, mas as invariantes que cruzam pedidos não
  cabem num `save()` de um model, e o teste continuaria preso ao banco.
- **Service layer sem portas.** Tira a regra da view, mas o serviço ainda importaria o ORM.
