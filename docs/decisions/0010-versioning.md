# 0010. SemVer, Conventional Commits e git-cliff

**Status:** decidido · **Data:** 2026-10-09

## Contexto

O projeto não tinha versão, changelog nem padrão de commit.

## Decisão

- Versão SemVer em `pyproject.toml`, exposta em `adote.__version__`, no rodapé do menu e em `/saude/`.
  Antes da 1.0, funcionalidade e quebra sobem `MINOR`; correção sobe `PATCH`.
- Commits em Conventional Commits, conferidos pelo hook `commit-msg`.
- `CHANGELOG.md` no formato Keep a Changelog, gerado pelo git-cliff a partir dos commits.
- `scripts/release.sh` (via `uv run poe release`) calcula a próxima versão, atualiza `pyproject.toml`,
  `uv.lock` e o changelog, faz o commit `chore(release)` e a tag anotada com as notas. Nunca dá push.
- Empurrar a tag dispara o workflow `release`, que confere a versão do `pyproject.toml` contra a tag
  e publica a GitHub Release com as notas da tag.

## Consequências

- O changelog nunca é editado à mão; uma mensagem de commit ruim vira uma linha ruim no changelog.
- Commits anteriores ao padrão não aparecem no changelog.
