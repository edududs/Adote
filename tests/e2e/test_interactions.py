import re
from collections.abc import Callable
from uuid import UUID

import pytest
from django.urls import reverse
from playwright.sync_api import Browser, Page, expect

from adote.accounts.adapters.models import User
from adote.pets.adapters.models import PetModel
from tests.conftest import PASSWORD, make_pet, make_user, png_bytes

pytestmark = [pytest.mark.e2e, pytest.mark.django_db(transaction=True)]


class LiveServer:
    url: str


def sign_in(page: Page, live_server: LiveServer, user: User) -> None:
    page.goto(f"{live_server.url}{reverse('accounts:login')}")
    page.fill("#id_username", user.username)
    page.fill("#id_password", PASSWORD)
    page.click("form button[type=submit]")
    page.wait_for_url(f"{live_server.url}/")


def test_removing_a_pet_asks_in_a_dialog_first(page: Page, live_server: LiveServer) -> None:
    owner = make_user("tutora")
    make_pet(owner, name="Thor")
    sign_in(page, live_server, owner)
    page.goto(f"{live_server.url}{reverse('adoption:my_pets')}")

    page.get_by_role("button", name="Remover").click()
    dialog = page.locator("#confirm-dialog")
    expect(dialog).to_be_visible()
    expect(dialog.get_by_role("heading")).to_have_text("Remover Thor?")
    dialog.get_by_role("button", name="Voltar").click()
    expect(dialog).to_be_hidden()
    assert PetModel.objects.filter(name="Thor").exists()

    page.get_by_role("button", name="Remover").click()
    page.keyboard.press("Escape")
    expect(dialog).to_be_hidden()
    assert PetModel.objects.filter(name="Thor").exists()

    page.get_by_role("button", name="Remover").click()
    dialog.get_by_role("button", name="Remover pet").click()
    expect(page.get_by_role("status").filter(has_text="Pet removido.")).to_be_visible()
    assert not PetModel.objects.filter(name="Thor").exists()


def test_toasts_can_be_dismissed(page: Page, live_server: LiveServer) -> None:
    owner = make_user()
    make_pet(owner, name="Mel")
    sign_in(page, live_server, owner)
    page.goto(f"{live_server.url}{reverse('adoption:my_pets')}")
    page.get_by_role("button", name="Remover").click()
    page.locator("#confirm-dialog").get_by_role("button", name="Remover pet").click()
    toast = page.get_by_role("status").filter(has_text="Pet removido.")
    expect(toast).to_be_visible()
    toast.get_by_role("button", name="Fechar aviso").click()
    expect(toast).to_have_count(0)


def test_the_phone_menu_opens_as_a_drawer_and_closes_with_escape(
    browser: Browser, live_server: LiveServer
) -> None:
    user = make_user()
    page = browser.new_page(viewport={"width": 390, "height": 844}, locale="pt-BR")
    sign_in(page, live_server, user)
    drawer = page.locator("#app-drawer")
    expect(drawer).to_be_hidden()
    page.get_by_role("button", name="Abrir menu").click()
    expect(drawer).to_be_visible()
    expect(drawer.get_by_role("link", name="Meus pedidos")).to_be_visible()
    page.keyboard.press("Escape")
    expect(drawer).to_be_hidden()
    page.close()


def test_the_chosen_photo_is_previewed_and_a_non_image_is_refused(
    page: Page, live_server: LiveServer
) -> None:
    sign_in(page, live_server, make_user())
    page.goto(f"{live_server.url}{reverse('pets:publish')}")
    preview = page.locator("[data-photo-preview]")
    expect(preview).to_be_hidden()

    page.set_input_files(
        "#id_photo", files=[{"name": "a.png", "mimeType": "image/png", "buffer": png_bytes()}]
    )
    expect(preview).to_be_visible()
    expect(preview).to_have_attribute("src", re.compile(r"^blob:"))

    page.set_input_files("#id_photo", files=[{"name": "a.txt", "mimeType": "text/plain", "buffer": b"oi"}])
    expect(page.locator("[data-photo-error]")).to_have_text("Envie uma imagem JPEG, PNG ou WEBP.")
    expect(preview).to_be_hidden()


def test_phone_and_cep_are_masked_while_typing(page: Page, live_server: LiveServer) -> None:
    page.goto(f"{live_server.url}{reverse('accounts:signup')}")
    page.locator("#id_phone").press_sequentially("61999998888")
    expect(page.locator("#id_phone")).to_have_value("(61) 99999-8888")
    page.locator("#id_postal_code").press_sequentially("70040010")
    expect(page.locator("#id_postal_code")).to_have_value("70040-010")


def test_every_page_loads_without_javascript_errors(page: Page, live_server: LiveServer) -> None:
    """The `page` fixture fails the test on any uncaught error; this walks every screen."""
    owner, adopter = make_user("tutor"), make_user("adotante")
    pet_id: UUID = make_pet(owner)
    for path in (reverse("accounts:login"), reverse("accounts:signup")):
        page.goto(f"{live_server.url}{path}")
    sign_in(page, live_server, adopter)
    names: list[tuple[str, Callable[[], list[object]]]] = [
        ("adoption:board", list),
        ("adoption:sent", list),
        ("adoption:received", list),
        ("adoption:my_pets", list),
        ("adoption:dashboard", list),
        ("pets:publish", list),
        ("accounts:profile", list),
        ("accounts:edit_profile", list),
        ("accounts:password", list),
    ]
    for name, _ in names:
        page.goto(f"{live_server.url}{reverse(name)}")
        page.wait_for_load_state("networkidle")
    page.goto(f"{live_server.url}{reverse('adoption:pet', args=[pet_id])}")
    page.get_by_role("button", name="Quero adotar").click()
    expect(page.get_by_role("status").filter(has_text="Pedido enviado")).to_be_visible()


def test_the_confirmation_starts_on_the_safe_choice(page: Page, live_server: LiveServer) -> None:
    owner = make_user()
    make_pet(owner)
    sign_in(page, live_server, owner)
    page.goto(f"{live_server.url}{reverse('adoption:my_pets')}")
    page.get_by_role("button", name="Remover").click()
    expect(page.locator("#confirm-cancel")).to_be_focused()


def test_a_failed_submit_focuses_the_first_invalid_field_and_links_its_error(
    page: Page, live_server: LiveServer
) -> None:
    page.goto(f"{live_server.url}{reverse('accounts:signup')}")
    page.get_by_role("button", name="Criar conta").click()
    first = page.locator("#id_first_name")
    expect(first).to_be_focused()
    expect(first).to_have_attribute("aria-invalid", "true")
    described = first.get_attribute("aria-describedby") or ""
    assert "id_first_name_error" in described.split()
    expect(page.locator("#id_first_name_error")).to_contain_text("obrigatório")


def test_focus_is_always_visible(page: Page, live_server: LiveServer) -> None:
    page.goto(f"{live_server.url}{reverse('accounts:login')}")
    page.keyboard.press("Tab")  # the skip link
    page.keyboard.press("Tab")
    outline = page.evaluate("getComputedStyle(document.activeElement).outlineStyle")
    assert outline == "solid"
