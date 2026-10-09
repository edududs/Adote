# Testes

`uv run poe check` roda tudo. Piso de cobertura: 95% (está em ~99%).

## O que cada grupo prova

| Grupo | Onde | Prova |
|---|---|---|
| Máquina de estados | `tests/adoption/machine.py`, `test_machine.py` | Qualquer sequência de pedir, aprovar, recusar e cancelar concorda com um modelo de referência ingênuo, e todas as invariantes valem a cada passo |
| Propriedades de domínio | `tests/shared/`, `tests/adoption/test_process.py` | Value objects aceitam o que se digita e recusam o resto; regras pontuais do agregado |
| Casos de uso | `tests/*/test_use_cases.py` | Orquestração com fakes em memória: ordem dos erros, eventos notificados, foto apagada se o pet não salvou |
| Contratos de porta | `tests/*/test_*contract.py`, marcados `contract` | O fake e o adaptador Django se comportam igual, então o que os testes de caso de uso assumem é o que produção faz |
| Banco | `tests/adoption/test_repository.py` | Atomicidade do `change`; constraints que seguram escritas que contornam o domínio |
| Views | `tests/*/test_views.py` | Matriz de autorização, privacidade do telefone, filtros do mural como propriedade, números do painel que fecham |
| Projeto | `tests/test_project.py`, `test_architecture.py` | Fronteira do hexágono, versão SemVer igual ao pacote, migrations em dia, admin abre, estáticos existem, nada de outra origem, cabeçalhos de segurança, produção segura por padrão |

## A máquina de estados

O modelo de referência é um dicionário de pedido para (adotante, situação), com as regras escritas
como `if`s simples. A máquina sorteia comandos e quem os executa (o tutor ou um de quatro
interessados), aplica no sistema e no modelo e confere, depois de cada passo:

- o estado gravado é igual ao do modelo;
- o processo gravado passa pela validação do agregado;
- no máximo uma aprovação; nenhum pendente depois dela;
- todo pedido decidido tem `decided_at` posterior ao pedido;
- cada mudança emitiu exatamente os eventos esperados, na ordem;
- uma situação final nunca muda;
- a página ofereceria exatamente as ações que as regras aceitam (`actions_for`).

Ela roda três vezes: no agregado puro (300 exemplos), nos casos de uso com o repositório em memória e
nos casos de uso com o repositório Django no banco real, cada execução dentro de uma transação
desfeita no fim. Foi verificada por mutação: desligar a regra de pedido duplicado ou a recusa
automática faz a máquina falhar em poucos passos.

## Banco

Os testes rodam em SQLite. Com `TEST_DATABASE_URL` apontando para um Postgres, a suíte inteira roda
nele (`uv run poe test-postgres`); o CI faz isso a cada push.

Exemplos do Hypothesis que escrevem no banco rodam dentro de `rolled_back()` (em `tests/conftest.py`):
o pytest-django isola um teste, não cada exemplo dentro dele. Evite testes transacionais
(`transaction=True`): o `flush` no fim apaga o catálogo semeado por migração para os testes seguintes.

## Perfis do Hypothesis

`HYPOTHESIS_PROFILE=ci` (usado no CI) roda mais exemplos que o padrão local.
