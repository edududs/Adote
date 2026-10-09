# Changelog

Formato conforme [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/) e versões conforme
[SemVer](https://semver.org/lang/pt-BR/). Gerado pelo git-cliff a partir dos commits: não editar à mão.

Antes da 1.0 o contrato ainda se move: `MINOR` traz funcionalidade e pode quebrar compatibilidade,
`PATCH` é correção. Commits anteriores à adoção do Conventional Commits não aparecem aqui.

## [Não lançado]

### Corrigido

- **shared:** Mark a field invalid when the view adds its error

### Refatorado

- **QUEBRA** Rebuild Adote as hexagonal bounded contexts
- **adoption:** List requests by id and drop an unused query

### Testes

- Cover the system with property-based and contract tests
