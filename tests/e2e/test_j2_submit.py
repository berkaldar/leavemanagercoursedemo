"""J-2: submit a request — a valid one is listed, one that breaks a rule shows why (spec 0002)."""

from playwright.sync_api import Locator, Page, Route, expect

from tests.e2e.test_j1_login import log_in

MISSING = "Choose a leave type, a start date and an end date."
FAILED = "Could not submit your request. Try again."


def fill(page: Page, leave_type: str, start: str, end: str) -> None:
    page.get_by_label("Leave type").select_option(leave_type)
    page.get_by_label("Start date").fill(start)
    page.get_by_label("End date").fill(end)


def submit(page: Page) -> None:
    page.get_by_role("button", name="Submit request").click()


def expect_values(page: Page, leave_type: str, start: str, end: str) -> None:
    expect(page.get_by_label("Leave type")).to_have_value(leave_type)
    expect(page.get_by_label("Start date")).to_have_value(start)
    expect(page.get_by_label("End date")).to_have_value(end)


def message(page: Page) -> Locator:
    return page.locator("#request-message")


def test_submit_valid_request_shows_row(page: Page) -> None:
    page.goto("/")
    log_in(page, "Ali Demir")
    fill(page, "Annual", "2026-11-16", "2026-11-20")
    submit(page)
    expect(message(page)).to_have_text("Request submitted.")
    expect_values(page, "", "", "")
    expect(page.get_by_role("row")).to_have_text(
        ["TypeStartEndWorking daysStatus", "Annual2026-11-162026-11-205Pending"]
    )
    expect(page.get_by_role("status")).to_have_text("")


def test_refused_request_shows_reason(page: Page) -> None:
    page.goto("/")
    log_in(page, "Ali Demir")
    submit(page)
    expect(message(page)).to_have_text(MISSING)
    fill(page, "Unpaid", "2026-11-20", "2026-11-19")
    submit(page)
    expect(message(page)).to_have_text("The end date must be on or after the start date.")
    expect_values(page, "Unpaid", "2026-11-20", "2026-11-19")
    expect(page.get_by_role("status")).to_have_text("You have no leave requests yet.")


def test_submitting_then_error_keeps_values(page: Page) -> None:
    held: list[Route] = []
    page.route(
        "**/api/my/requests",
        lambda r: held.append(r) if r.request.method == "POST" else r.continue_(),
    )
    page.goto("/")
    log_in(page, "Ali Demir")
    fill(page, "Annual", "2026-11-16", "2026-11-20")
    submit(page)
    expect(message(page)).to_have_text("Submitting…")
    expect(page.get_by_role("button", name="Submit request")).to_be_disabled()
    held[0].fulfill(status=500, json={"error": "INTERNAL", "message": "Something went wrong."})
    expect(message(page)).to_have_text(FAILED)
    expect(page.get_by_role("button", name="Submit request")).to_be_enabled()
    expect_values(page, "Annual", "2026-11-16", "2026-11-20")
    submit(page)
    expect(message(page)).to_have_text("Submitting…")
    held[1].abort()  # network failure
    expect(message(page)).to_have_text(FAILED)
    expect_values(page, "Annual", "2026-11-16", "2026-11-20")
    expect(page.get_by_role("status")).to_have_text("You have no leave requests yet.")


def test_next_user_sees_nothing_of_the_previous_one(page: Page) -> None:
    page.goto("/")
    log_in(page, "Ali Demir")
    fill(page, "Annual", "2026-11-16", "2026-11-20")
    submit(page)
    expect(page.get_by_role("row")).to_have_count(2)
    fill(page, "Annual", "2026-11-18", "2026-11-19")
    submit(page)
    expect(message(page)).to_have_text(
        "You already have a pending or approved request on these dates."
    )
    held: list[Route] = []
    page.route("**/api/my/requests", lambda r: held.append(r))
    page.get_by_role("button", name="Log out").click()
    log_in(page, "Elif Şahin")
    expect(page.get_by_text("Signed in as Elif Şahin")).to_be_visible()
    expect(page.get_by_role("row")).to_have_count(0)  # while her list is still loading
    expect(message(page)).to_have_text("")
    expect_values(page, "", "", "")
    held[0].fulfill(status=500, json={"error": "INTERNAL", "message": "Something went wrong."})
    expect(page.get_by_role("status")).to_have_text("Could not load your requests.")
    expect(page.get_by_role("row")).to_have_count(0)


def tab_to(page: Page, target: str, via: str) -> None:
    # Tab also visits a date field's own parts (its picker), so it may take a few presses.
    for _ in range(4):
        page.keyboard.press("Tab")
        focused = page.evaluate("document.activeElement.id")
        if focused == target:
            return
        assert focused == via, f"Tab left {via} for {focused}, not {target}"
    raise AssertionError(f"Tab never reached {target}")


def test_keyboard_only_submit_and_live_region(page: Page) -> None:
    page.goto("/")
    log_in(page, "Ali Demir")
    expect(message(page)).to_have_attribute("aria-live", "polite")
    page.get_by_role("button", name="Log out").focus()
    page.keyboard.press("Tab")
    expect(page.get_by_label("Leave type")).to_be_focused()
    page.keyboard.press("ArrowDown")  # Choose a type → Annual
    page.keyboard.press("Tab")
    expect(page.get_by_label("Start date")).to_be_focused()
    page.keyboard.type("11162026")  # en-US: mm dd yyyy
    tab_to(page, "end-date", via="start-date")
    page.keyboard.type("11202026")
    page.keyboard.press("Enter")
    expect(message(page)).to_have_text("Request submitted.")
    expect(page.get_by_role("row")).to_have_count(2)
