# Telas

Uma imagem por tela e por situação, com a semente de demonstração (`manage.py seed_demo`).
**Gerado** por `uv run poe screens` ([scripts/screens.py](../../scripts/screens.py)):
não é editado à mão. Cada tela aparece em computador (1280 px de largura) e em celular (390 px).

Na semente, Ana divulgou Thor, Mel e Bidu; Bruno divulgou Luna e Pipoca. Bruno e Carla pediram
Thor (pendentes), Ana pediu Luna (pendente), Carla teve Pipoca aprovada e Bruno teve Bidu recusado.

| # | Tela | Quem está vendo | Rota |
|---|---|---|---|
| 01 | [Entrar](#01-login) | sem login | `/conta/entrar/` |
| 02 | [Cadastro](#02-signup) | sem login | `/conta/cadastro/` |
| 03 | [Cadastro com erros](#03-signup-errors) | sem login | `/conta/cadastro/` |
| 04 | [Mural de pets](#04-board) | Carla (adotante) | `/` |
| 05 | [Mural filtrado](#05-board-filtered) | Carla (adotante) | `/?species=dog&state=DF` |
| 06 | [Página do pet: pedir para adotar](#06-pet-request) | Carla (adotante) | `/pets/<id>/` |
| 07 | [Página do pet: pedido em aberto](#07-pet-pending) | Carla (adotante) | `/pets/<id>/` |
| 08 | [Página do pet: pedido aprovado](#08-pet-approved) | Carla (adotante) | `/pets/<id>/` |
| 09 | [Meus pedidos](#09-sent) | Carla (adotante) | `/pedidos/enviados/` |
| 10 | [Divulgar um pet](#10-publish) | Ana (tutora) | `/pets/divulgar/` |
| 11 | [Divulgar com erros](#11-publish-errors) | Ana (tutora) | `/pets/divulgar/` |
| 12 | [Meus pets](#12-my-pets) | Ana (tutora) | `/pets/meus/` |
| 13 | [Pedidos recebidos](#13-received) | Ana (tutora) | `/pedidos/recebidos/` |
| 14 | [Perfil de quem quer adotar](#14-adopter) | Ana (tutora) | `/pedidos/<id>/adotante/` |
| 15 | [Página do pet vista por quem divulgou](#15-pet-owner) | Ana (tutora) | `/pets/<id>/` |
| 16 | [Painel](#16-dashboard) | Ana (tutora) | `/painel/` |
| 17 | [Perfil](#17-profile) | Bruno | `/conta/perfil/` |
| 18 | [Editar perfil](#18-profile-edit) | Bruno | `/conta/perfil/editar/` |
| 19 | [Trocar senha](#19-password) | Bruno | `/conta/senha/` |
| 20 | [Página não encontrada](#20-not-found) | Bruno | `/pets/<id>/` |

<a id="01-login"></a>

## 01. Entrar

**Quem:** sem login · **Rota:** `/conta/entrar/`

Porta de entrada. Ver pets exige conta, para que telefones e cidades não fiquem abertos para robôs.

![Entrar](desktop/01-login.webp)

<img src="mobile/01-login.webp" alt="Entrar no celular" width="300">

<a id="02-signup"></a>

## 02. Cadastro

**Quem:** sem login · **Rota:** `/conta/cadastro/`

Cadastro com perfil completo. O CEP preenche cidade, bairro e estado pelo ViaCEP; telefone e CEP aceitam qualquer máscara. O "sobre você" é obrigatório: é o que o tutor lê antes de aprovar um pedido.

![Cadastro](desktop/02-signup.webp)

<img src="mobile/02-signup.webp" alt="Cadastro no celular" width="300">

<a id="03-signup-errors"></a>

## 03. Cadastro com erros

**Quem:** sem login · **Rota:** `/conta/cadastro/`

Enviar o formulário vazio: cada campo obrigatório é marcado e explica o que falta, sem perder o que já foi digitado.

![Cadastro com erros](desktop/03-signup-errors.webp)

<img src="mobile/03-signup-errors.webp" alt="Cadastro com erros no celular" width="300">

<a id="04-board"></a>

## 04. Mural de pets

**Quem:** Carla (adotante) · **Rota:** `/`

O mural para quem quer adotar. Não mostra os pets da própria pessoa nem os já adotados; o selo "Você já pediu" marca os pets com pedido em aberto da pessoa. Os cards entram em sequência e sobem ao passar o mouse.

![Mural de pets](desktop/04-board.webp)

<img src="mobile/04-board.webp" alt="Mural de pets no celular" width="300">

<a id="05-board-filtered"></a>

## 05. Mural filtrado

**Quem:** Carla (adotante) · **Rota:** `/?species=dog&state=DF`

Abas por espécie e filtros por raça, sexo, estado, cidade e característica, combináveis e guardados na URL. Filtro inválido nunca dá erro: só deixa de filtrar. No celular os filtros ficam recolhidos em "Mais filtros", com a contagem dos ativos.

![Mural filtrado](desktop/05-board-filtered.webp)

<img src="mobile/05-board-filtered.webp" alt="Mural filtrado no celular" width="300">

<a id="06-pet-request"></a>

## 06. Página do pet: pedir para adotar

**Quem:** Carla (adotante) · **Rota:** `/pets/<id>/`

Quem ainda não pediu vê a descrição, as características e o painel do pedido, com uma mensagem para quem divulgou. O telefone de quem divulgou não aparece. No celular, uma barra fixa "Quero adotar" leva ao painel e some quando ele está na tela.

![Página do pet: pedir para adotar](desktop/06-pet-request.webp)

<img src="mobile/06-pet-request.webp" alt="Página do pet: pedir para adotar no celular" width="300">

<a id="07-pet-pending"></a>

## 07. Página do pet: pedido em aberto

**Quem:** Carla (adotante) · **Rota:** `/pets/<id>/`

Com o pedido aguardando resposta, a página mostra a situação e permite cancelar.

![Página do pet: pedido em aberto](desktop/07-pet-pending.webp)

<img src="mobile/07-pet-pending.webp" alt="Página do pet: pedido em aberto no celular" width="300">

<a id="08-pet-approved"></a>

## 08. Página do pet: pedido aprovado

**Quem:** Carla (adotante) · **Rota:** `/pets/<id>/`

Depois da aprovação, e só para o adotante aprovado, aparece o telefone de quem divulgou, com um botão de WhatsApp quando é celular. O painel comemora com uma chuva de patinhas.

![Página do pet: pedido aprovado](desktop/08-pet-approved.webp)

<img src="mobile/08-pet-approved.webp" alt="Página do pet: pedido aprovado no celular" width="300">

<a id="09-sent"></a>

## 09. Meus pedidos

**Quem:** Carla (adotante) · **Rota:** `/pedidos/enviados/`

Todos os pedidos da pessoa, com a situação de cada um: cancelar enquanto está pendente, ver o contato quando foi aprovado.

![Meus pedidos](desktop/09-sent.webp)

<img src="mobile/09-sent.webp" alt="Meus pedidos no celular" width="300">

<a id="10-publish"></a>

## 10. Divulgar um pet

**Quem:** Ana (tutora) · **Rota:** `/pets/divulgar/`

Formulário de divulgação. Estado, cidade e telefone vêm do perfil. Raças agrupadas por espécie; a foto é conferida pelo formato real (JPEG, PNG ou WEBP, até 5 MB).

![Divulgar um pet](desktop/10-publish.webp)

<img src="mobile/10-publish.webp" alt="Divulgar um pet no celular" width="300">

<a id="11-publish-errors"></a>

## 11. Divulgar com erros

**Quem:** Ana (tutora) · **Rota:** `/pets/divulgar/`

Enviar sem preencher: cada problema aparece no próprio campo.

![Divulgar com erros](desktop/11-publish-errors.webp)

<img src="mobile/11-publish-errors.webp" alt="Divulgar com erros no celular" width="300">

<a id="12-my-pets"></a>

## 12. Meus pets

**Quem:** Ana (tutora) · **Rota:** `/pets/meus/`

Os pets que a pessoa divulgou, com a situação e quantos pedidos aguardam resposta. Só pet ainda não adotado pode ser removido, e a remoção pede confirmação.

![Meus pets](desktop/12-my-pets.webp)

<img src="mobile/12-my-pets.webp" alt="Meus pets no celular" width="300">

<a id="13-received"></a>

## 13. Pedidos recebidos

**Quem:** Ana (tutora) · **Rota:** `/pedidos/recebidos/`

Os pedidos para os pets da pessoa, separados entre os que aguardam resposta e os já respondidos, com a mensagem de cada interessado. Aprovar pede confirmação, recusa os outros pendentes do mesmo pet, e cada interessado recebe um e-mail.

![Pedidos recebidos](desktop/13-received.webp)

<img src="mobile/13-received.webp" alt="Pedidos recebidos no celular" width="300">

<a id="14-adopter"></a>

## 14. Perfil de quem quer adotar

**Quem:** Ana (tutora) · **Rota:** `/pedidos/<id>/adotante/`

O perfil e a mensagem do interessado. Só o tutor do pet pedido vê esta página; para qualquer outra pessoa ela responde como se não existisse.

![Perfil de quem quer adotar](desktop/14-adopter.webp)

<img src="mobile/14-adopter.webp" alt="Perfil de quem quer adotar no celular" width="300">

<a id="15-pet-owner"></a>

## 15. Página do pet vista por quem divulgou

**Quem:** Ana (tutora) · **Rota:** `/pets/<id>/`

Quem divulgou vê o próprio contato, quantos pedidos aguardam e o atalho para respondê-los.

![Página do pet vista por quem divulgou](desktop/15-pet-owner.webp)

<img src="mobile/15-pet-owner.webp" alt="Página do pet vista por quem divulgou no celular" width="300">

<a id="16-dashboard"></a>

## 16. Painel

**Quem:** Ana (tutora) · **Rota:** `/painel/`

Totais da plataforma (divulgados, esperando um lar, adotados, pedidos em aberto) e as adoções por raça, numa consulta só.

![Painel](desktop/16-dashboard.webp)

<img src="mobile/16-dashboard.webp" alt="Painel no celular" width="300">

<a id="17-profile"></a>

## 17. Perfil

**Quem:** Bruno · **Rota:** `/conta/perfil/`

O que a pessoa contou de si. É o que um tutor vê quando ela pede um pet.

![Perfil](desktop/17-profile.webp)

<img src="mobile/17-profile.webp" alt="Perfil no celular" width="300">

<a id="18-profile-edit"></a>

## 18. Editar perfil

**Quem:** Bruno · **Rota:** `/conta/perfil/editar/`

Edição do perfil. E-mail e telefone continuam únicos entre as contas.

![Editar perfil](desktop/18-profile-edit.webp)

<img src="mobile/18-profile-edit.webp" alt="Editar perfil no celular" width="300">

<a id="19-password"></a>

## 19. Trocar senha

**Quem:** Bruno · **Rota:** `/conta/senha/`

Troca de senha com a senha atual e os validadores do Django.

![Trocar senha](desktop/19-password.webp)

<img src="mobile/19-password.webp" alt="Trocar senha no celular" width="300">

<a id="20-not-found"></a>

## 20. Página não encontrada

**Quem:** Bruno · **Rota:** `/pets/<id>/`

Recurso inexistente, ou de outra pessoa: a resposta é a mesma, sem dizer se o identificador existe.

![Página não encontrada](desktop/20-not-found.webp)

<img src="mobile/20-not-found.webp" alt="Página não encontrada no celular" width="300">
