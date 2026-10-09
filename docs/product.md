# Produto

## O problema

Protetores independentes resgatam cães e gatos e divulgam em grupos de mensagem e redes sociais.
Os interessados chegam pelo mesmo canal, cada um numa conversa, e o protetor perde o controle: quem
perguntou primeiro, quem já foi recusado, se o animal já foi adotado. Quem quer adotar não sabe se
o pet ainda está disponível nem se o pedido foi visto.

## As pessoas

- **Tutor:** quem divulga um pet. Geralmente um protetor independente, às vezes uma família que não
  pode mais cuidar do animal. Quer escolher bem para quem o pet vai.
- **Adotante:** quem quer adotar. Quer achar um pet perto, com o perfil certo, e saber a resposta.

Uma mesma conta é tutor dos pets que divulgou e adotante dos pets que pediu.

## O que o produto faz

1. O tutor divulga um pet com foto, espécie, raça, sexo, características, descrição, local e
   telefone de contato.
2. O adotante encontra pets no mural, filtrando por espécie, raça, sexo, estado, cidade e
   característica. O mural não mostra os pets dele nem os já adotados.
3. O adotante pede para adotar, com uma mensagem. O tutor recebe um e-mail.
4. O tutor lê o perfil e a mensagem de cada interessado e aprova ou recusa. Aprovar um pedido
   recusa os outros automaticamente: o pet só tem um adotante. Cada interessado recebe um e-mail.
5. O adotante aprovado vê o telefone do tutor (com link de WhatsApp) e os dois combinam a entrega.
6. O adotante acompanha os seus pedidos e pode cancelar um que ainda não foi respondido.
7. O painel mostra quantos pets foram divulgados, adotados, quantos esperam e as adoções por raça.

## O que o produto não faz

- **Não intermedia a entrega** nem verifica a casa do adotante: a decisão e a responsabilidade são
  do tutor.
- **Não tem chat.** O contato direto começa depois da aprovação, por telefone ou WhatsApp.
- **Não é público.** É preciso conta para ver os pets: o telefone e a cidade de quem divulga não
  ficam abertos para robôs.
- **Não cobra nem recebe doações.**

## Métrica

Tempo entre a divulgação de um pet e a aprovação de um pedido, e a proporção de pedidos que recebem
resposta. As duas saem dos dados que o sistema já guarda (`requested_at` e `decided_at`).
