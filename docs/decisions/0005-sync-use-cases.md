# 0005. Casos de uso síncronos

**Status:** decidido · **Data:** 2026-10-09

## Contexto

Casos de uso `async` compensam em APIs ASGI com conexões longas (SSE, WebSocket). O Adote é
renderizado no servidor, sem conexões longas, e o Django 6 ainda não tem transação em modo async.

## Decisão

Casos de uso e portas síncronos; servidor WSGI (gunicorn). O `asgi.py` existe, mas não é o caminho
de produção.

## Consequências

- `transaction.atomic` e `select_for_update` são usados direto no adaptador, sem `sync_to_async`.
- Se um dia houver atualização em tempo real (SSE), essa decisão é revista junto.
