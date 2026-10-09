# Índice da documentação

Mapa da documentação do projeto: um documento por assunto, e quando cada um é atualizado.

| Documento | Para quê | Atualiza quando |
|---|---|---|
| [conventions.md](conventions.md) | As regras do código: hexágono, nomes, views, templates, testes. | Uma regra muda |
| [ROADMAP.md](ROADMAP.md) | Estado atual, próximos marcos e o que vem depois. | A cada versão, ou quando o escopo muda |
| [product.md](product.md) | Problema, pessoas, o que o produto faz e não faz. | Escopo de produto muda |
| [architecture.md](architecture.md) | Contextos, camadas, fluxos, conceitos transversais. | Fronteira de contexto ou dependência externa muda |
| [testing.md](testing.md) | Estratégia de testes: o que cada camada de teste prova. | Tipo novo de teste ou portão muda |
| [security.md](security.md) | Modelo de ameaça em uma página. | Proteção, limite ou risco assumido muda |
| [privacy.md](privacy.md) | Dados pessoais: o que, de quem, para quê, quem vê. | Dado pessoal novo ou regra de visibilidade muda |
| [decisions/README.md](decisions/README.md) | Tabela de todas as decisões, com status. | Toda decisão nova |
| `decisions/NNNN-*.md` | Registro completo das decisões cujo motivo não é óbvio. | Imutável; decisão nova substitui |
| [domain/shared.md](domain/shared.md) | Value objects comuns: telefone, CEP, UF. | Conceito muda ou é renomeado |
| [domain/accounts.md](domain/accounts.md) | Glossário e invariantes de contas. | Idem |
| [domain/pets.md](domain/pets.md) | Glossário e invariantes de pets. | Idem |
| [domain/adoption.md](domain/adoption.md) | Glossário, ciclo de vida e invariantes da adoção. | Idem |
| [screens/README.md](screens/README.md) | Uma imagem por tela e por situação, com quem está vendo, a rota e a explicação. **Gerado** por `uv run poe screens`, não se edita. | A cada mudança de tela |
| [runbooks/release.md](runbooks/release.md) | Como cortar e publicar uma versão. | O procedimento muda |
| [runbooks/deploy.md](runbooks/deploy.md) | Como colocar no ar e operar. | O procedimento muda |

A documentação não repete o que o próprio código mostra (estrutura de pastas, assinaturas, lista
de rotas, campos de model); a lista de tarefas de desenvolvimento sai de `uv run poe`.
