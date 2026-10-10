# Pets (`pets`)

| Termo | No código | Definição |
|---|---|---|
| Pet | `Pet` | Um animal divulgado para adoção, como o tutor o descreveu. Identificado por UUID. |
| Tutor | `Pet.owner_id` | A conta que divulgou o pet. Na tela, "quem divulgou". |
| Dados do pet | `PetDetails` | Tudo que o tutor preenche: nome, espécie, sexo, raça, características, descrição, cidade, UF e telefone de contato. |
| Espécie | `Species` | Cão ou gato (na tela, "Cachorro" e "Gato"). |
| Raça | `Breed` | Pertence a uma espécie; "SRD (vira-lata)" existe nas duas. |
| Característica | `TagId` | Etiqueta do catálogo (castrado, vacinado, porte...). No máximo 10 por pet. |
| Foto | `Pet.photo`, `PhotoStore` | Chave no armazenamento de fotos. O nome enviado nunca é usado. |
| Divulgar | `PublishPet` | Confere raça, espécie e características contra o catálogo, guarda a foto, grava o pet. |
| Remover | `RemovePet` | O tutor tira um pet ainda não adotado. Pedidos pendentes dele são descartados. |

## Invariantes

- A raça é da mesma espécie do pet.
- Toda característica existe no catálogo.
- A foto só fica guardada se o pet foi gravado; se a gravação falha, ela é apagada.
- Só o tutor remove, e nunca um pet adotado: a adoção é histórico e o painel a conta.
- "Disponível" ou "adotado" não é campo do pet. É calculado pelo contexto `adoption` e chega aqui
  pela porta `AdoptionLedger`.

## Erros

`UnknownBreedError`, `BreedOfAnotherSpeciesError`, `UnknownTagError`, `PetNotFoundError`,
`NotPetOwnerError`, `AdoptedPetError`.
