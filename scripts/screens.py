"""Regenerates docs/screens/: one picture per screen and situation, and the README that explains them.

The app runs in production mode (gunicorn, WhiteNoise, manifest static files) over a throwaway
SQLite database filled by `seed_demo`, so every picture shows the real thing with the demo data.

    uv run poe screens                      # Playwright's own Chromium
    ADOTE_CHROMIUM=/path/to/chrome uv run poe screens
"""

import json
import os
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
from collections.abc import Callable, Generator
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from uuid import UUID

from PIL import Image
from playwright.sync_api import Browser, Page, sync_playwright

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "docs" / "screens"
PASSWORD = "adote-demo-2026"  # noqa: S105 - the demo seed's published password
DESKTOP = {"width": 1280, "height": 860}
MOBILE = {"width": 390, "height": 844}

IDS_SCRIPT = """
import json
from adote.pets.adapters.models import PetModel
from adote.adoption.adapters.models import AdoptionRequestModel
pets = {pet.name: str(pet.pk) for pet in PetModel.objects.all()}
rows = AdoptionRequestModel.objects.select_related("pet", "adopter")
requests = {f"{r.pet.name}:{r.adopter.username}": str(r.pk) for r in rows}
print(json.dumps({"pets": pets, "requests": requests}))
"""


@dataclass(frozen=True)
class Screen:
    slug: str
    title: str
    who: str  # a demo username, or "" for someone signed out
    path: str
    explanation: str
    mobile: bool = False
    before: Callable[[Page], None] | None = field(default=None, compare=False)


def _submit_empty(page: Page) -> None:
    page.locator("form[novalidate] button[type=submit]").first.click()
    page.wait_for_load_state("networkidle")


def screens(ids: dict[str, dict[str, str]]) -> list[Screen]:
    pet, request = ids["pets"], ids["requests"]
    return [
        Screen(
            "01-login",
            "Entrar",
            "",
            "/conta/entrar/",
            "Porta de entrada. Ver pets exige conta, para que telefones e cidades não fiquem abertos "
            "para robôs.",
            mobile=True,
        ),
        Screen(
            "02-signup",
            "Cadastro",
            "",
            "/conta/cadastro/",
            "Cadastro com perfil completo. O CEP preenche cidade, bairro e estado pelo ViaCEP; "
            'telefone e CEP aceitam qualquer máscara. O "sobre você" é obrigatório: é o que o '
            "tutor lê antes de aprovar um pedido.",
        ),
        Screen(
            "03-signup-errors",
            "Cadastro com erros",
            "",
            "/conta/cadastro/",
            "Enviar o formulário vazio: cada campo obrigatório é marcado e explica o que falta, sem "
            "perder o que já foi digitado.",
            before=_submit_empty,
        ),
        Screen(
            "04-board",
            "Mural de pets",
            "carla",
            "/",
            "O mural para quem quer adotar. Não mostra os pets da própria pessoa nem os já adotados; "
            'o selo "Você já pediu" marca os pets com pedido seu em aberto.',
            mobile=True,
        ),
        Screen(
            "05-board-filtered",
            "Mural filtrado",
            "carla",
            "/?species=dog&state=DF",
            "Filtros por espécie, raça, sexo, estado, cidade e característica, combináveis e guardados "
            "na URL. Filtro inválido nunca dá erro: só deixa de filtrar.",
        ),
        Screen(
            "06-pet-request",
            "Página do pet: pedir para adotar",
            "carla",
            f"/pets/{pet['Luna']}/",
            "Quem ainda não pediu vê a descrição, as características e o formulário do pedido, com uma "
            "mensagem para quem divulgou. O telefone de quem divulgou não aparece.",
            mobile=True,
        ),
        Screen(
            "07-pet-pending",
            "Página do pet: pedido em aberto",
            "carla",
            f"/pets/{pet['Thor']}/",
            "Com o pedido aguardando resposta, a página mostra a situação e permite cancelar.",
        ),
        Screen(
            "08-pet-approved",
            "Página do pet: pedido aprovado",
            "carla",
            f"/pets/{pet['Pipoca']}/",
            "Depois da aprovação, e só para o adotante aprovado, aparece o telefone de quem divulgou, "
            "com link de WhatsApp quando é celular.",
        ),
        Screen(
            "09-sent",
            "Meus pedidos",
            "carla",
            "/pedidos/enviados/",
            "Todos os pedidos da pessoa, com a situação de cada um: cancelar enquanto está pendente, "
            "ver o contato quando foi aprovado.",
        ),
        Screen(
            "10-publish",
            "Divulgar um pet",
            "ana",
            "/pets/divulgar/",
            "Formulário de divulgação. Estado, cidade e telefone vêm do perfil. Raças agrupadas por "
            "espécie; a foto é conferida pelo formato real (JPEG, PNG ou WEBP, até 5 MB).",
        ),
        Screen(
            "11-publish-errors",
            "Divulgar com erros",
            "ana",
            "/pets/divulgar/",
            "Enviar sem preencher: cada problema aparece no próprio campo.",
            before=_submit_empty,
        ),
        Screen(
            "12-my-pets",
            "Meus pets",
            "ana",
            "/pets/meus/",
            "Os pets que a pessoa divulgou, com a situação e quantos pedidos aguardam resposta. Só pet "
            "ainda não adotado pode ser removido, e a remoção pede confirmação.",
        ),
        Screen(
            "13-received",
            "Pedidos recebidos",
            "ana",
            "/pedidos/recebidos/",
            "Os pedidos para os pets da pessoa, pendentes primeiro e os mais antigos antes. Aprovar um "
            "recusa os outros pendentes do mesmo pet, e cada interessado recebe um e-mail.",
            mobile=True,
        ),
        Screen(
            "14-adopter",
            "Perfil de quem quer adotar",
            "ana",
            f"/pedidos/{request['Thor:bruno']}/adotante/",
            "O perfil e a mensagem do interessado. Só o tutor do pet pedido vê esta página; para "
            "qualquer outra pessoa ela responde como se não existisse.",
        ),
        Screen(
            "15-pet-owner",
            "Página do pet vista por quem divulgou",
            "ana",
            f"/pets/{pet['Thor']}/",
            "Quem divulgou vê o próprio contato, quantos pedidos aguardam e o atalho para respondê-los.",
        ),
        Screen(
            "16-dashboard",
            "Painel",
            "ana",
            "/painel/",
            "Totais da plataforma (divulgados, esperando um lar, adotados, pedidos em aberto) e as "
            "adoções por raça, numa consulta só.",
            mobile=True,
        ),
        Screen(
            "17-profile",
            "Perfil",
            "bruno",
            "/conta/perfil/",
            "O que a pessoa contou de si. É o que um tutor vê quando ela pede um pet.",
        ),
        Screen(
            "18-profile-edit",
            "Editar perfil",
            "bruno",
            "/conta/perfil/editar/",
            "Edição do perfil. E-mail e telefone continuam únicos entre as contas.",
        ),
        Screen(
            "19-password",
            "Trocar senha",
            "bruno",
            "/conta/senha/",
            "Troca de senha com a senha atual e os validadores do Django.",
        ),
        Screen(
            "20-not-found",
            "Página não encontrada",
            "bruno",
            "/pets/00000000-0000-0000-0000-000000000000/",
            "Recurso inexistente, ou de outra pessoa: a resposta é a mesma, sem dizer se o "
            "identificador existe.",
        ),
    ]


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _manage(env: dict[str, str], *args: str) -> str:
    result = subprocess.run(  # noqa: S603 - fixed interpreter and arguments
        [sys.executable, "manage.py", *args], cwd=REPO, env=env, check=True, capture_output=True, text=True
    )
    return result.stdout


@contextmanager
def running_app() -> Generator[tuple[str, dict[str, dict[str, str]]]]:
    with tempfile.TemporaryDirectory(prefix="adote-screens-") as tmp:
        root = Path(tmp)
        env = {key: value for key, value in os.environ.items() if not key.startswith("DJANGO_")}
        port = _free_port()
        env |= {
            "DJANGO_SECRET_KEY": "screens-only-" + "x" * 40,
            "DJANGO_ALLOWED_HOSTS": "localhost",
            "DJANGO_SECURE_SSL_REDIRECT": "0",
            "DJANGO_HSTS_SECONDS": "0",
            "DJANGO_SERVE_MEDIA": "1",
            "DJANGO_MEDIA_ROOT": str(root / "media"),
            "DJANGO_STATIC_ROOT": str(root / "static"),
            "DATABASE_URL": f"sqlite:///{root / 'db.sqlite3'}",
        }
        _manage(env, "migrate", "--noinput")
        _manage(env, "collectstatic", "--noinput")
        _manage(env, "seed_demo")
        ids: dict[str, dict[str, str]] = json.loads(_manage(env, "shell", "--no-imports", "-c", IDS_SCRIPT))
        server = subprocess.Popen(  # noqa: S603 - fixed interpreter and arguments
            [
                sys.executable,
                "-m",
                "gunicorn",
                "adote.config.wsgi:application",
                "--bind",
                f"127.0.0.1:{port}",
            ],
            cwd=REPO,
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        base = f"http://localhost:{port}"
        try:
            _wait_for(f"{base}/saude/")
            yield base, ids
        finally:
            server.terminate()
            server.wait(timeout=10)


def _wait_for(url: str) -> None:
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1):  # noqa: S310 - local URL built above
                return
        except OSError:
            time.sleep(0.3)
    msg = f"the app did not answer at {url}"
    raise RuntimeError(msg)


def _signed_in_page(browser: Browser, base: str, who: str, viewport: dict[str, int]) -> Page:
    page = browser.new_page(viewport=viewport, locale="pt-BR")  # pyright: ignore[reportArgumentType]
    if who:
        page.goto(f"{base}/conta/entrar/")
        page.fill("#id_username", who)
        page.fill("#id_password", PASSWORD)
        page.click("form button[type=submit]")
        page.wait_for_url(f"{base}/")
    return page


def capture(browser: Browser, base: str, screen: Screen, viewport: dict[str, int], name: str) -> list[str]:
    page = _signed_in_page(browser, base, screen.who, viewport)
    errors: list[str] = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.goto(f"{base}{screen.path}")
    page.wait_for_load_state("networkidle")
    if screen.before is not None:
        screen.before(page)
    # Lazy images below the fold would come out blank in a full-page picture: load them all first.
    page.evaluate(
        "document.querySelectorAll('img[loading=lazy]').forEach((img) => { img.loading = 'eager'; })"
    )
    page.wait_for_function("Array.from(document.images).every((img) => img.complete)")
    page.wait_for_timeout(400)  # the chart animates in
    png = OUT / name
    page.screenshot(path=png, full_page=True)
    page.close()
    # WebP at this quality is a fifth of the PNG and indistinguishable on a screen: the folder stays light.
    with Image.open(png) as image:
        image.save(png.with_suffix(".webp"), "WEBP", quality=82, method=6)
    png.unlink()
    return errors


def write_readme(items: list[Screen]) -> None:
    people = {"": "sem login", "ana": "Ana (tutora)", "bruno": "Bruno", "carla": "Carla (adotante)"}
    lines = [
        "# Telas",
        "",
        "Uma imagem por tela e por situação, com a semente de demonstração (`manage.py seed_demo`).",
        "**Gerado** por `uv run poe screens` ([scripts/screens.py](../../scripts/screens.py)):",
        "não edite à mão; mude o script e rode de novo. Desktop em 1280 px de largura; algumas telas",
        "também em celular (390 px).",
        "",
        "Na semente, Ana divulgou Thor, Mel e Bidu; Bruno divulgou Luna e Pipoca. Bruno e Carla pediram",
        "Thor (pendentes), Ana pediu Luna (pendente), Carla teve Pipoca aprovada e Bruno teve Bidu recusado.",
        "",
        "| # | Tela | Quem está vendo | Rota |",
        "|---|---|---|---|",
    ]
    for screen in items:
        number = screen.slug.split("-", 1)[0]
        lines.append(
            f"| {number} | [{screen.title}](#{screen.slug}) | {people[screen.who]} "
            f"| `{_route(screen.path)}` |"
        )
    for screen in items:
        lines += [
            "",
            f'<a id="{screen.slug}"></a>',
            "",
            f"## {screen.slug.split('-', 1)[0]}. {screen.title}",
            "",
            f"**Quem:** {people[screen.who]} · **Rota:** `{_route(screen.path)}`",
            "",
            screen.explanation,
            "",
            f"![{screen.title}](desktop/{screen.slug}.webp)",
        ]
        if screen.mobile:
            lines += [
                "",
                f'<img src="mobile/{screen.slug}.webp" alt="{screen.title} no celular" width="300">',
            ]
    (OUT / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _is_uuid(text: str) -> bool:
    try:
        return str(UUID(text)) == text
    except ValueError:
        return False


def _route(path: str) -> str:
    """Identifiers change on every run; the README shows the route's shape instead."""
    parts = ["<id>" if _is_uuid(part) else part for part in path.split("/")]
    return "/".join(parts)


def main() -> None:
    (OUT / "desktop").mkdir(parents=True, exist_ok=True)
    (OUT / "mobile").mkdir(parents=True, exist_ok=True)
    for old in [*OUT.glob("desktop/*.*"), *OUT.glob("mobile/*.*")]:
        old.unlink()
    with running_app() as (base, ids), sync_playwright() as playwright:
        executable = os.environ.get("ADOTE_CHROMIUM")
        browser = (
            playwright.chromium.launch(executable_path=executable)
            if executable
            else playwright.chromium.launch()
        )
        items = screens(ids)
        errors: list[str] = []
        for screen in items:
            errors += capture(browser, base, screen, DESKTOP, f"desktop/{screen.slug}.png")
            if screen.mobile:
                errors += capture(browser, base, screen, MOBILE, f"mobile/{screen.slug}.png")
            print(f"screens: {screen.slug}")  # noqa: T201 - progress for whoever runs the script
        browser.close()
    write_readme(items)
    if errors:
        sys.exit(f"screens: JavaScript errors on the pages: {errors}")


if __name__ == "__main__":
    main()
