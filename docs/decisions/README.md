# Decisões

Tabela única de todas as decisões. Uma linha basta quando o motivo é evidente; quando não é, a coluna
**Registro** aponta para um ADR com contexto, decisão, consequências e alternativas descartadas.

**Status:** `decidido`, `proposto` (falta validar) ou `adiado` (fora do escopo atual, com intenção registrada).
Decisão não se edita: cria-se outra e marca-se a antiga como `substituída por D-NNN`.

## Direção

| ID | Decisão | Status | Registro |
|---|---|---|---|
| D-001 | Reescrever a versão de aprendizado em vez de remendar: esquema, rotas e estrutura novos | decidido | [0007](0007-fresh-schema.md) |
| D-002 | Hexagonal com DDD: domínio e aplicação em Python puro com Pydantic, Django só nos adaptadores | decidido | [0001](0001-hexagonal-ddd-django-in-adapters.md) |
| D-003 | Contextos `accounts`, `pets` e `adoption`, mais `shared`; cada um com seu app Django dentro de `adapters/` | decidido | [0002](0002-bounded-contexts.md) |
| D-004 | Código, identificadores e arquivos em inglês; documentação, interface, URLs e e-mails em pt-BR | decidido | |
| D-005 | Python 3.14, Django 6, uv, ruff com todas as regras, pyright estrito, tarefas no poe | decidido | |
| D-006 | Renderização no servidor com Bootstrap; sem SPA. O único JSON é o do gráfico do painel | decidido | |
| D-007 | Licença MIT, como os outros projetos do autor | decidido | |
| D-008 | A branch padrão é `main`; `master` deixa de existir depois do merge da reescrita | decidido | |

## Adoção

| ID | Decisão | Status | Registro |
|---|---|---|---|
| D-010 | Todos os pedidos de um pet formam um agregado, salvo numa transação com lock na linha do pet | decidido | [0003](0003-adoption-process-aggregate.md) |
| D-011 | "Adotado" é calculado a partir dos pedidos, nunca gravado no pet | decidido | [0003](0003-adoption-process-aggregate.md) |
| D-012 | Aprovar um pedido recusa os outros pendentes automaticamente, e cada um recebe aviso | decidido | |
| D-013 | Recusa é definitiva para aquele pet; só quem cancelou o próprio pedido pode pedir de novo | decidido | |
| D-014 | O adotante pode cancelar o pedido enquanto ele está pendente | decidido | |
| D-015 | A página recebe as ações permitidas do agregado (`actions_for`); o template não recalcula regra | decidido | |
| D-016 | Invariantes do agregado repetidas como constraints do banco | decidido | [0003](0003-adoption-process-aggregate.md) |
| D-017 | Pet adotado não pode ser removido: é histórico e conta no painel | decidido | |

## Pets

| ID | Decisão | Status | Registro |
|---|---|---|---|
| D-020 | Cães e gatos; raça pertence a uma espécie | decidido | |
| D-021 | Raças e características entram por migração de dados reversível, não por sinal `post_migrate` | decidido | |
| D-022 | UF é um `StrEnum` de 27 valores, não tabela | decidido | |
| D-023 | Pets e pedidos com UUID: não expõem contagem e não se adivinham | decidido | |
| D-024 | Foto conferida pelo Pillow (JPEG, PNG, WEBP, até 5 MB) e guardada com nome aleatório | decidido | |
| D-025 | Várias fotos por pet | adiado | |

## Contas e privacidade

| ID | Decisão | Status | Registro |
|---|---|---|---|
| D-030 | O telefone do tutor só aparece para o próprio tutor e para o adotante aprovado | decidido | [0009](0009-contact-after-approval.md) |
| D-031 | O perfil de um interessado só aparece para o tutor do pet que ele pediu | decidido | [0009](0009-contact-after-approval.md) |
| D-032 | Ver pets exige conta | decidido | [0009](0009-contact-after-approval.md) |
| D-033 | E-mail único sem diferenciar maiúsculas, garantido também no banco | decidido | |
| D-034 | Confirmação de e-mail e recuperação de senha | adiado | |

## Aplicação

| ID | Decisão | Status | Registro |
|---|---|---|---|
| D-040 | Escrita passa pelo domínio; leitura das páginas vai direto ao ORM em `queries.py` | decidido | [0004](0004-read-side-queries.md) |
| D-041 | Casos de uso síncronos (WSGI, gunicorn), ao contrário do BrazCar | decidido | [0005](0005-sync-use-cases.md) |
| D-042 | Autorização falha como 404; mudança de estado só por POST com CSRF | decidido | |
| D-043 | Bibliotecas de front servidas pela aplicação; CSP só `'self'` | decidido | [0006](0006-vendored-assets.md) |
| D-044 | Configuração por ambiente, segura por padrão: debug é a exceção que se liga | decidido | |
| D-045 | Falha de e-mail é registrada e nunca desfaz a ação | decidido | |

## Qualidade e processo

| ID | Decisão | Status | Registro |
|---|---|---|---|
| D-050 | Testes por propriedade com Hypothesis; máquina de estados da adoção contra modelo de referência | decidido | [0008](0008-property-based-testing.md) |
| D-051 | Contratos de porta rodam fake e adaptador Django lado a lado | decidido | [0008](0008-property-based-testing.md) |
| D-052 | Suíte inteira também em Postgres no CI | decidido | |
| D-053 | Piso de cobertura de 95% | decidido | |
| D-054 | SemVer; changelog e notas geradas pelo git-cliff a partir de Conventional Commits; release local, publicação por tag | decidido | [0010](0010-versioning.md) |
| D-055 | Commits em Conventional Commits, sem trailers | decidido | |
| D-056 | Prints de todas as telas em `docs/screens/`, gerados por script (Playwright sobre a aplicação em modo produção com a semente de demonstração), em WebP; nunca tirados à mão | decidido | |
