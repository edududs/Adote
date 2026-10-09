# Convenções

As regras que valem em todo o código. São poucas, e todas são conferidas por teste ou pelo portão
(`uv run poe check`) sempre que possível.

## Regras do projeto

1. **Idioma.** Código, identificadores, pastas e nomes de arquivo em inglês. Documentação, textos de
   interface, URLs e e-mails em pt-BR.
2. **Hexágono.** `domain/` e `application/` só importam stdlib, Pydantic e as camadas de baixo, do
   próprio contexto ou de `shared`. Django mora em `adapters/`. `tests/test_architecture.py` garante.
3. **Um contexto não importa o núcleo de outro.** Referência entre contextos é por identificador.
   Quando um contexto precisa de uma resposta de outro, ele declara a porta e o outro a implementa
   em `adapters/bridges.py` (ver `AdoptionLedger`).
4. **Um pet, um agregado, uma transação.** Toda mudança em pedidos de adoção passa por
   `AdoptionProcesses.change`, que trava a linha do pet. Ver [ADR 0003](decisions/0003-adoption-process-aggregate.md).
5. **Fonte única.** "Adotado" é calculado dos pedidos, nunca gravado. A página recebe as ações
   permitidas prontas (`actions_for`); o template não recalcula regra.
6. **Escrita pelo domínio, leitura direta.** Comando passa por caso de uso; página lê por
   `queries.py` do adaptador, que filtra por quem está vendo. Ver [ADR 0004](decisions/0004-read-side-queries.md).
7. **Privacidade.** O telefone de quem divulgou só aparece para quem divulgou e para o adotante
   aprovado. O perfil de um interessado só aparece para o tutor do pet que ele pediu.
8. **Autorização falha como 404.** Recurso de outra pessoa responde como inexistente. Toda mudança
   de estado é POST com CSRF.
9. **Sem tipos frouxos.** Pyright estrito, sem `Any` solto. Antes de abrir um PR: `uv run poe fix`
   e `uv run poe check`.
10. **Commits.** Conventional Commits, sem trailers; o hook `commit-msg` confere.
11. **Documentação no mesmo commit.** Decisão nova vira linha em
    [decisions/README.md](decisions/README.md); decisão antiga não se edita, se substitui.
12. **O que foi verificado à mão vira teste no mesmo passo**; correção de bug entra com o teste que
    a reproduz.
13. **Segredos.** Nunca versionar `.env`, banco ou fotos enviadas.

## Domínio e aplicação

- Antes de nomear algo, consulte o glossário em `domain/<contexto>.md`. Um conceito, um nome.
- Estado inválido não deve ser representável: value object e `StrEnum` em vez de string solta;
  validação no construtor (`FrozenModel` + validadores), falha cedo.
- Entidades e value objects são congelados; mudar devolve cópia nova com `evolve`, que valida de novo.
- O agregado emite eventos em `events`; o caso de uso os entrega ao `Notifier`. Eventos não são estado.
- Erro de regra é uma classe em `errors.py` herdando do erro base do contexto, com docstring dizendo
  a regra. O adaptador traduz em mensagem pt-BR.
- Caso de uso é `@dataclass(frozen=True, slots=True)` com as portas como campos e `__call__`.
  A docstring lista os erros que ele levanta, na ordem em que os confere.
- Regra nova no agregado entra na máquina de estados (`tests/adoption/machine.py`) e no modelo de referência.

## Adaptadores

- Toolchain: uv, ruff (`select = ["ALL"]`, cada exceção justificada em `ruff.toml`), pyright estrito,
  tarefas em `poe_tasks.toml`.
- O app Django de cada contexto (models, migrations, views, templates, admin) mora em `adapters/`,
  com `label` curto. `adapters/composition.py` é o único lugar que instancia casos de uso.
- View: decorador de método HTTP (`require_GET`/`require_POST`), `login_required`, traduz erro de
  domínio em mensagem ou 404. Sem regra de negócio em view nem em template.
- Formulário herda de `BootstrapForm` e converte a entrada em value objects nos `clean_*`.
- Dado de referência (raças, características) entra por migração de dados, nunca por sinal.

## Templates e estáticos

- Página logada estende `app.html`; login e cadastro estendem `auth.html`. Campo de formulário pelo
  `partials/_field.html`, mensagens pelo `partials/_messages.html`.
- Nenhum recurso de outra origem: bibliotecas ficam em `shared/adapters/static/vendor/` com a versão
  no nome da pasta. A CSP só aceita `'self'`.
- Sem `<script>` inline nem `onclick`: comportamento vai para um arquivo em `static/adote/js/`.
  Confirmação de ação destrutiva é `data-confirm` no `<form>`.
- Ação que muda estado é `<form method="post">` com `{% csrf_token %}`, nunca link.
- O template não decide regra: usa as flags que a view calculou (`can_request`, `can_decide`...).
- Acessibilidade: `alt` em imagem, `label` ligado ao campo, `aria-label` em navegação e ícone sem texto.
- Mudou uma tela: `uv run poe screens` no mesmo PR.

## Testes

- Domínio sem banco; Hypothesis para regras.
- Porta nova ganha fake em `tests/fakes.py` e teste de contrato rodando fake e adaptador Django lado a lado.
- Exemplo do Hypothesis que escreve no banco roda dentro de `rolled_back()`.
- Detalhes em [testing.md](testing.md).
