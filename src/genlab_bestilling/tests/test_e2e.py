import re


def do_login(page):
    page.get_by_label("Email").click()
    page.get_by_label("Email").fill("admin@nina.no")
    page.get_by_label("Email").press("Tab")
    page.get_by_label("Password").fill("admin")
    page.get_by_label("Password").press("Enter")


def test_login(page, live_server_url):
    page.goto(live_server_url)
    do_login(page)
    assert page.url == "{}{}".format(live_server_url, "/genrequests/")


def get_path(url, prefix):
    return url.replace(prefix, "")


def test_genrequest_flow(page, live_server_url):
    page.goto(live_server_url)
    do_login(page)
    page.get_by_role("link", name="+ Request").click()
    page.locator("#id_project-ts-control").click()
    page.locator("#id_project-opt-1").click()
    page.get_by_label("Description:").click()
    page.get_by_label("Description:").fill("my request")
    page.locator(
        "div:nth-child(4) > .shadow-wrapper > .ts-wrapper > .ts-control"
    ).click()
    page.locator("#id_area-opt-1").click()
    page.locator("div").filter(
        has_text=re.compile(
            r"^Species:ElvemuslingSpissnutefroskSmåsalamanderStorsalamanderLaksØrret$"
        )
    ).get_by_role("listbox").first.select_option(["1", "3", "4"])
    page.get_by_role("button", name="Move selected right").first.click()
    page.locator(
        "div:nth-child(6) > .shadow-wrapper > .ts-wrapper > .ts-control"
    ).click()
    page.locator("#id_samples_owner-opt-1").click()
    page.locator(
        "div:nth-child(8) > .dj-dual-selector > div > .left-column > select"
    ).select_option(["Elvemusling A", "Spissnutefrosk A", "Salamander 2"])
    page.get_by_role("button", name="Move selected right").nth(2).click()
    page.get_by_label("Expected total samples:").click()
    page.get_by_label("Expected total samples:").fill("50")
    page.get_by_label("Tags:").fill("test")
    page.locator("#id_expected_samples_delivery_date").fill("2025-01-01")
    page.locator("#id_expected_analysis_delivery_date").fill("2025-06-01")
    page.get_by_role("button", name="Submit").click()
    page.get_by_role("link", name="Orders").wait_for()
    assert re.match(r"\/genrequests\/\d+\/", get_path(page.url, live_server_url))
    assert page.get_by_role("link", name="Orders").count() == 1

    page.get_by_role("link", name="Edit").click()
    page.get_by_label("Expected total samples:").fill("500")
    page.get_by_role("button", name="Submit").click()
    page.get_by_role("link", name="Orders").wait_for()
    assert page.get_by_role("link", name="Orders").count() == 1

    page.get_by_role("link", name="Delete").click()
    assert re.match(
        r"\/genrequests\/\d+\/delete\/", get_path(page.url, live_server_url)
    )
    page.get_by_role("button", name="Confirm").click()
    assert re.match(r"\/genrequests\/", get_path(page.url, live_server_url))
