# Deploy

A aplicação é uma imagem Docker com gunicorn e WhiteNoise. Precisa de um Postgres, de um volume para
as fotos e de um proxy que termine TLS e repasse `X-Forwarded-Proto`.

## Variáveis obrigatórias

| Variável | Exemplo |
|---|---|
| `DJANGO_SECRET_KEY` | `python -c "import secrets; print(secrets.token_urlsafe(50))"` |
| `DJANGO_ALLOWED_HOSTS` | `adote.exemplo.org` |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | `https://adote.exemplo.org` |
| `DATABASE_URL` | `postgres://adote:senha@db:5432/adote` |
| `ADOTE_SITE_URL` | `https://adote.exemplo.org` (links dos e-mails) |
| `EMAIL_HOST`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `DEFAULT_FROM_EMAIL` | dados do provedor SMTP |

As demais, com padrões seguros, estão em [.env.example](../../.env.example).

## Primeira vez

```sh
docker build -t adote:0.1.0 .
docker run --env-file .env -v adote-data:/data -p 8000:8000 adote:0.1.0
docker exec -it <container> python manage.py createsuperuser
```

As migrations rodam a cada partida do container (`scripts/docker-entrypoint.sh`); são idempotentes.
Os estáticos já vêm coletados na imagem.

Para um teste local parecido com produção, com Postgres: `docker compose up --build`.

## Verificações depois de subir

- `GET /saude/` responde `{"status": "ok", "version": "<versão>"}` (o healthcheck do container usa essa rota).
- `curl -I https://<host>/conta/entrar/` mostra `Strict-Transport-Security` e `Content-Security-Policy`.
- Divulgar um pet com foto e abrir a foto: confirma o volume e o caminho de mídia.

## Fotos

Ficam em `/data/media`. Com `DJANGO_SERVE_MEDIA=1` a própria aplicação as serve; com tráfego, sirva
`/media/` pelo proxy apontando para o mesmo volume e desligue a variável.

## Backup

Banco (`pg_dump`) e o volume `/data/media`, juntos: um sem o outro deixa pets sem foto ou fotos órfãs.

## Atualizar

Corte a versão ([release.md](release.md)), construa a imagem com a tag nova e troque o container.
Sem migração destrutiva, a troca não precisa de janela.
