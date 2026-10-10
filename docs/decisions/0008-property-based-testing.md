# 0008. Testes por propriedade e contratos de porta

**Status:** decidido · **Data:** 2026-10-09

## Contexto

As regras de adoção dependem da ordem dos acontecimentos (quem pediu, quem cancelou, o que foi
aprovado antes). Testes de exemplo cobrem os casos que alguém lembrou de escrever.

## Decisão

- Uma máquina de estados do Hypothesis sorteia sequências de comandos e as aplica, lado a lado, ao
  sistema e a um modelo de referência propositalmente ingênuo, conferindo as invariantes a cada passo.
  A mesma máquina roda no agregado puro, nos casos de uso com repositório em memória e nos casos de
  uso com o repositório Django no banco real.
- Cada porta tem um fake em `tests/fakes.py` e um teste de contrato que roda fake e adaptador Django
  com as mesmas entradas geradas.
- Value objects e formulários têm propriedades de ida e volta (formatar e interpretar devolve o mesmo valor).

## Consequências

- A máquina foi validada por mutação: desligar uma regra a faz falhar em poucos passos.
- Os testes de caso de uso podem usar fakes sem mentir, porque o contrato prova que o fake se comporta
  como o adaptador.
- Exemplos que escrevem no banco precisam de `rolled_back()` por exemplo.
