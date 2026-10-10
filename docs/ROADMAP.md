# Roadmap

## Estado atual

A versão `0.1.0` está em preparação (seção "Não lançado" do [changelog](../CHANGELOG.md)). Ela cobre
o ciclo completo de adoção: divulgar um pet, pedir para adotar, aprovar ou recusar, cancelar um
pedido, com avisos por e-mail, painel da comunidade e interface para computador e celular.

Limitações conhecidas desta versão:

- A imagem Docker não tem build automatizado no CI; o processo de build está descrito em
  [runbooks/deploy.md](runbooks/deploy.md).
- Bancos da versão anterior à reescrita não são migrados: o esquema é novo
  ([ADR 0007](decisions/0007-fresh-schema.md)).

## Próximos marcos

- **0.1.0:** primeira versão publicada e primeira instância em produção.
- **Build da imagem no CI**, publicada no GitHub Container Registry a cada versão.

## Depois

- **Recuperação de senha** por e-mail.
- **Confirmação de e-mail** no cadastro, antes de permitir pedir ou divulgar.
- **Mais de uma foto por pet**, com ordenação e recorte.
- **Idade e porte** como campos do pet, com filtro (hoje vão na descrição e nas características).
- **Limite de pedidos** por conta e por janela de tempo, contra abuso.
- **Exclusão de conta pela própria pessoa** (hoje feita pela administração), com o efeito sobre o
  histórico de adoções descrito em [privacy.md](privacy.md).

## Em estudo

- Página pública do pet, sem login, para compartilhamento fora da plataforma (exige rever a privacidade).
- Organizações protetoras como conta própria, com vários membros.
- Acompanhamento pós-adoção, com foto do pet 30 dias depois da entrega.
- API JSON para um aplicativo móvel.
