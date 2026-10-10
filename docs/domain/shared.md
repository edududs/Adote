# Núcleo compartilhado (`shared`)

Value objects que mais de um contexto usa. Nenhum conhece Django.

| Termo | No código | Definição |
|---|---|---|
| Telefone | `PhoneNumber` | Número brasileiro guardado como dígitos nacionais: DDD válido + 8 dígitos (fixo, começa com 2 a 5) ou 9 dígitos (celular, começa com 9). `parse` aceita máscara, espaços, `+55` e o `0` de longa distância. Formata como `(61) 99999-0000`; só celular tem link de WhatsApp. |
| CEP | `PostalCode` | Oito dígitos, não todos zero. Formata como `70000-000`. |
| UF | `State` | As 27 unidades federativas, conjunto fechado: um `StrEnum`, não uma tabela. `full_name` dá o nome por extenso. |
| Relógio | `Clock` (porta) | Hora atual com fuso. Injetado para que regras de tempo sejam testáveis. |
| Correio | `Mailer` (porta) | Envia uma mensagem de texto. Nunca levanta erro para quem chama. |

## Invariantes

- Um `PhoneNumber` ou `PostalCode` existente é sempre válido: o construtor valida, e `evolve` valida de novo.
- Formatar e interpretar de volta devolve o mesmo valor (`parse(x.formatted()) == x`).
