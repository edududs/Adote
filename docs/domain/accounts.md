# Contas (`accounts`)

| Termo | No código | Definição |
|---|---|---|
| Conta | `User` (adaptador), `AccountId` | Quem entra no Adote. A mesma conta é tutor dos pets que divulga e adotante dos que pede. |
| Perfil | `Profile` | O que a pessoa conta de si: nome, e-mail, telefone, CEP, UF, cidade, bairro e "sobre você". |
| Sobre você | `Profile.about` | Apresentação obrigatória: é o que o tutor lê antes de aprovar. |
| Cadastrar | `RegisterAccount` | Cria a conta com usuário, senha e perfil. |
| Atualizar perfil | `UpdateProfile` | Troca o perfil inteiro de uma conta. |

## Invariantes

- Usuário, e-mail (sem diferenciar maiúsculas) e telefone são únicos entre as contas. O caso de uso
  confere antes, e o banco garante de novo (`UniqueConstraint` com `Lower("email")` e telefone
  único quando preenchido), para o caso de dois cadastros simultâneos.
- O cadastro nunca concede privilégio. Conta administrativa só pelo `createsuperuser`, e ela pode
  existir sem telefone nem UF.
- A força da senha é regra do adaptador: os validadores do Django rodam no formulário, inclusive
  contra semelhança com o nome e o usuário.

## Erros

`UsernameTakenError`, `EmailTakenError`, `PhoneTakenError` (nessa ordem no cadastro),
`AccountNotFoundError`.
