# Roadmap

## Agora

- Lançar a `v0.1.0` e publicar a primeira instância.

## Depois

- **Recuperação de senha** por e-mail (as views do Django cobrem; faltam templates e o teste).
- **Confirmação de e-mail** no cadastro, antes de permitir pedir ou divulgar.
- **Mais de uma foto por pet**, com ordenação e recorte.
- **Idade e porte** como campos do pet, e filtro por eles (hoje vão na descrição e em características).
- **Limite de pedidos** por conta e por janela de tempo, contra abuso.
- **Exclusão de conta pela própria pessoa** (hoje só pela administração), com o que isso faz com o
  histórico de adoções ([privacy.md](privacy.md)).

## Talvez

- Página pública do pet, sem login, para compartilhar o link fora da plataforma (exige rever a privacidade).
- Organizações protetoras como conta própria, com vários membros.
- Acompanhamento pós-adoção (o adotante manda uma foto depois de 30 dias).
- API JSON para um app móvel.
