# Cortar uma versão

A versão é calculada dos commits desde a última tag (ADR 0010). O script trabalha só localmente;
publicar é empurrar a tag.

## Passos

1. Esteja em `main`, atualizado, com a árvore limpa e o CI verde no último commit.
2. Veja o que sai:

   ```sh
   uv run poe release --dry-run
   ```

   Mostra a última versão, a próxima e as notas. Se a próxima não for a esperada, o motivo está num
   tipo de commit (um `feat` sobe `MINOR`; um `fix`, `PATCH`).
3. Corte:

   ```sh
   uv run poe release
   ```

   Atualiza `pyproject.toml`, `uv.lock` e `CHANGELOG.md`, faz o commit `chore(release): vX.Y.Z` e cria
   a tag anotada com as notas.
4. Publique:

   ```sh
   git push --follow-tags
   ```

   O workflow `release` confere que a versão do `pyproject.toml` é a da tag e cria a GitHub Release
   com as notas da tag.
5. Atualize o estado atual no [ROADMAP.md](../ROADMAP.md) e faça o deploy ([deploy.md](deploy.md)).

## Se algo der errado

- **A tag ainda não foi empurrada:** `git tag -d vX.Y.Z && git reset --hard HEAD~1` e corte de novo.
- **Já foi empurrada:** não reescreva. Corrija com um commit `fix` e corte uma versão `PATCH`.
