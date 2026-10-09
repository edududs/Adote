# Modelo de ameaça

## O que se protege

1. O telefone e o e-mail de quem divulga e de quem pede.
2. A decisão do tutor: só ele aprova ou recusa pedidos dos seus pets.
3. A integridade da adoção: um pet, um adotante.
4. As contas: senhas e sessões.

## Contra quem

- Uma pessoa com conta tentando agir sobre o que não é dela (o caso mais provável).
- Um robô sem conta colhendo contatos.
- Alguém na rede entre o navegador e o servidor.

## Proteções

| Ameaça | Proteção | Onde é provada |
|---|---|---|
| Aprovar ou recusar pedido de outro tutor | Caso de uso confere o tutor; view responde 404; ação só por POST | `tests/adoption/test_views.py` |
| Ver o perfil de um interessado sem ser o tutor | Consulta filtra pelo tutor | idem |
| Colher telefones | Pets só com login; telefone só para o tutor e o adotante aprovado | idem |
| Descobrir se um identificador existe | Identificadores UUID; recurso alheio responde igual a inexistente | idem |
| Dois adotantes aprovados | Lock na linha do pet e constraint única parcial no banco | `tests/adoption/test_repository.py`, máquina de estados |
| Promover-se a administrador no cadastro | O cadastro nunca concede privilégio (a versão antiga dava superusuário a quem se chamasse "admin") | `tests/accounts/test_views.py` |
| CSRF | Toda mudança de estado é POST com token; logout também | testes de view (GET → 405) |
| XSS | Autoescape do Django; CSP sem script inline e só de `'self'` | `tests/test_project.py` |
| Clickjacking | `X-Frame-Options: DENY` e `frame-ancestors 'none'` | idem |
| Arquivo malicioso como foto | Pillow confere o formato real; nome aleatório; limite de tamanho | `tests/pets/test_views.py` |
| Interceptação | HSTS, cookies `Secure`, redirecionamento para HTTPS fora do modo debug | `check --deploy` no portão |
| Senha fraca | Validadores do Django, inclusive semelhança com nome e usuário | `tests/accounts/test_views.py` |
| Segredo no repositório | Chave só por ambiente; sem ela e sem debug a aplicação não sobe | `tests/test_project.py` |

## Riscos assumidos

- **Sem limite de tentativas de login nem de pedidos.** Depende do proxy até entrar no roadmap.
- **E-mail não é confirmado no cadastro.** Alguém pode se cadastrar com o e-mail de outra pessoa.
- **Fotos são servidas pela própria aplicação** quando `DJANGO_SERVE_MEDIA=1`; o ideal em produção é
  o proxy ou um storage de objetos.
- **O tutor vê o telefone e o e-mail de quem pede.** É o que permite decidir; está dito na tela de cadastro.
