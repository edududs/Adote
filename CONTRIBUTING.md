# Contribuindo

## Preparar o ambiente

```sh
uv sync              # Python 3.14 e todas as dependências, inclusive as de desenvolvimento
uv run poe hooks     # liga os hooks versionados em .githooks/
uv run poe setup     # banco local e semente de demonstração
uv run poe serve     # http://127.0.0.1:8000
```

`uv run poe` sem argumentos lista todas as tarefas. Para mexer no visual, rode `npm ci` uma vez e
`uv run poe css-watch` enquanto trabalha: o CSS é Tailwind, compilado para `static/adote/css/app.css`.

## O portão

- `uv run poe fix` formata, aplica as correções do ruff e checa tipos. Rode antes de cada commit.
- `uv run poe check` é o que o CI roda, sem reescrever nada: formatação, lint, pyright estrito,
  testes com cobertura mínima de 95%, migrations em dia e o `check --deploy` do Django.
- `uv run poe test-postgres` roda a suíte de novo em Postgres (`docker compose up db` sobe um).

O hook de `pre-commit` roda só formatação e lint, para ser rápido; o portão completo fica com o CI.

## Onde mexer

Leia [docs/conventions.md](docs/conventions.md): são poucas regras, e todas valem. Em resumo:

- Regra de negócio vai no `domain/` do contexto, com teste de propriedade. Regra de adoção nova
  entra também no modelo de referência de `tests/adoption/machine.py`.
- Caso de uso novo vai em `application/use_cases.py`; porta nova em `application/ports.py`, com
  fake em `tests/fakes.py` e teste de contrato rodando fake e adaptador Django.
- View, formulário, model e template ficam em `adapters/`.
- Decisão de arquitetura ou de produto vira linha em [docs/decisions/README.md](docs/decisions/README.md),
  e um ADR quando o motivo não é óbvio.

## Commits

[Conventional Commits](https://www.conventionalcommits.org/pt-br/): `feat`, `fix`, `perf`, `refactor`,
`docs`, `test`, `build`, `ci`, `chore`, com escopo opcional (`accounts`, `pets`, `adoption`,
`shared`, `config`, `demo`). Quebra de compatibilidade leva `!` no tipo e um rodapé
`BREAKING CHANGE:`. O changelog e as notas de versão são gerados dessas mensagens, então o assunto
deve descrever a mudança para quem lê o changelog. Sem trailers: o hook `commit-msg` recusa.

## Pull requests

Um assunto por PR, com o portão verde. O template de PR pede o que mudou, por quê e como foi
verificado. Mudança visível na tela regenera os prints no mesmo PR: `uv run poe screens`
(precisa de um Chromium; `ADOTE_CHROMIUM` aponta um já instalado).

## Versões

Ver [docs/runbooks/release.md](docs/runbooks/release.md).
