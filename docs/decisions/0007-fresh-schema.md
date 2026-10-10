# 0007. Esquema novo, sem migrar o banco antigo

**Status:** decidido · **Data:** 2026-10-09

## Contexto

O banco antigo tinha `Estado` como tabela com chave estrangeira pelo nome, status do pet gravado,
chaves inteiras sequenciais, raças duplicadas e nenhuma constraint de adoção. O próprio `db.sqlite3`
e as fotos enviadas estavam versionados no git. Não há instância em produção com dados reais.

## Decisão

Migrations novas a partir do zero, com UUID em pets e pedidos. O banco e as fotos antigos saem do
repositório e passam a ser ignorados. A semente de demonstração (`manage.py seed_demo`) recria um
cenário completo passando pelos casos de uso, usando as fotos de exemplo que existiam.

## Consequências

- É uma quebra de compatibilidade: o commit é `refactor!` e o changelog marca **QUEBRA**.
- Quem tinha um banco local antigo apaga e roda `uv run poe setup`.
