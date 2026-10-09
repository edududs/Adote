# Estado

**Atualizado em:** 2026-10-09

## Onde está

A reescrita da versão de aprendizado está completa e ainda não lançada (`0.1.0` no `pyproject.toml`,
seção "Não lançado" no changelog):

- três contextos em hexágono (`accounts`, `pets`, `adoption`) e o núcleo `shared`;
- fluxo completo de divulgar, pedir, aprovar, recusar e cancelar, com e-mails;
- falhas de segurança da versão antiga fechadas (ver o commit `refactor!` e [security.md](security.md));
- 210+ testes, cobertura de 98%, máquina de estados do Hypothesis contra o banco real, suíte
  repetida em Postgres no CI;
- documentação, processo de versão e CI;
- prints de todas as telas em [screens/](screens/README.md), gerados por `uv run poe screens`;
- Django 6.1 com `MAILERS`, Tasks framework e `LoginRequiredMiddleware`;
- visual refeito com Tailwind 4, sem Bootstrap nem jQuery (ADR 0011).

## Próximo passo

1. Revisar e fazer o merge do PR da reescrita em `main` e tornar `main` a branch padrão do GitHub.
2. Cortar a `v0.1.0`: `uv run poe release --dry-run`, depois `uv run poe release` e
   `git push --follow-tags` ([runbooks/release.md](runbooks/release.md)).
3. Escolher onde hospedar e seguir [runbooks/deploy.md](runbooks/deploy.md).

## Riscos conhecidos

- A imagem Docker foi escrita e o passo crítico dela (`collectstatic` com manifesto, healthcheck,
  cabeçalhos em modo produção) foi verificado fora do Docker, mas o `docker build` ainda não rodou
  numa máquina com daemon. Rode uma vez antes do primeiro deploy.
- O banco SQLite e as fotos da versão antiga não migram: o esquema é novo (ADR 0007).
