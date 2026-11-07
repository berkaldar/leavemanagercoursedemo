"""J-1: log in → "My requests" (spec 0001)."""

from playwright.sync_api import Page, Route, expect

from app.db import ALI_ID

LOADING = "Loading your requests…"
EMPTY = "You have no leave requests yet."
ERROR = "Could not load your requests."


def log_in(page: Page, full_name: str) -> None:
    page.get_by_label("Who are you?").select_option(label=full_name)
    page.get_by_role("button", name="Log in").click()


def expect_login_screen(page: Page) -> None:
    expect(page.get_by_label("Who are you?")).to_be_visible()
    expect(page.get_by_role("heading", name="My requests")).to_be_hidden()


def test_login_screen_lists_seeded_people(page: Page) -> None:
    page.goto("/")
    people = page.get_by_label("Who are you?")
    expect(people.locator("option")).to_have_text(
        ["Choose your name", "Ali Demir", "Deniz Kaya", "Elif Şahin"]
    )
    expect(people).to_have_value("")


def test_login_shows_name_and_requires_choice(page: Page) -> None:
    page.goto("/")
    page.get_by_role("button", name="Log in").click()
    expect(page.get_by_role("alert")).to_have_text("Choose who you are.")
    expect_login_screen(page)
    log_in(page, "Elif Şahin")
    expect(page.get_by_role("heading", name="My requests")).to_be_visible()
    expect(page.get_by_text("Signed in as Elif Şahin")).to_be_visible()


def test_my_requests_empty_state(page: Page) -> None:
    page.goto("/")
    log_in(page, "Ali Demir")
    expect(page.get_by_role("status")).to_have_text(EMPTY)


def test_my_requests_loading_state(page: Page) -> None:
    held: list[Route] = []
    page.route("**/api/my/requests", lambda route: held.append(route))
    page.goto("/")
    log_in(page, "Ali Demir")
    expect(page.get_by_role("status")).to_have_text(LOADING)
    held[0].continue_()
    expect(page.get_by_role("status")).to_have_text(EMPTY)


def test_my_requests_error_then_retry(page: Page) -> None:
    held: list[Route] = []

    def fail_first_then_hold(route: Route) -> None:
        if held:
            held.append(route)
        else:
            held.append(route)
            route.fulfill(status=500, json={"error": "INTERNAL", "message": "x"})

    page.route("**/api/my/requests", fail_first_then_hold)
    page.goto("/")
    log_in(page, "Ali Demir")
    expect(page.get_by_role("status")).to_have_text(ERROR)
    page.get_by_role("button", name="Try again").click()
    expect(page.get_by_role("status")).to_have_text(LOADING)
    expect(page.get_by_role("button", name="Try again")).to_be_hidden()
    held[1].continue_()
    expect(page.get_by_role("status")).to_have_text(EMPTY)


def test_no_session_shows_login(page: Page) -> None:
    page.goto("/")
    expect_login_screen(page)
    expect(page.get_by_text("Signed in as")).to_be_hidden()


def test_logout_and_logged_in_skips_login(page: Page) -> None:
    page.goto("/")
    log_in(page, "Deniz Kaya")
    expect(page.get_by_text("Signed in as Deniz Kaya")).to_be_visible()
    page.reload()  # logged in and opening the app again: straight to "My requests" (R-8)
    expect(page.get_by_text("Signed in as Deniz Kaya")).to_be_visible()
    page.get_by_role("button", name="Log out").click()
    expect_login_screen(page)
    page.reload()
    expect_login_screen(page)


def test_keyboard_only_flow_and_live_region(page: Page) -> None:
    page.goto("/")
    expect(page.get_by_label("Who are you?")).to_be_visible()
    page.keyboard.press("Tab")
    expect(page.get_by_label("Who are you?")).to_be_focused()
    page.keyboard.press("ArrowDown")
    expect(page.get_by_label("Who are you?")).to_have_value(ALI_ID)
    page.keyboard.press("Tab")
    expect(page.get_by_role("button", name="Log in")).to_be_focused()
    page.keyboard.press("Enter")
    expect(page.get_by_text("Signed in as Ali Demir")).to_be_visible()
    expect(page.get_by_role("status")).to_have_text(EMPTY)
    expect(page.get_by_role("status")).to_have_attribute("aria-live", "polite")
    page.keyboard.press("Tab")
    expect(page.get_by_role("button", name="Log out")).to_be_focused()
    page.keyboard.press("Enter")
    expect_login_screen(page)
