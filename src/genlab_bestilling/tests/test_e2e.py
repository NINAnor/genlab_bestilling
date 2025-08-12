import re

import pytest
from playwright.sync_api import expect


def do_login(page):
    page.get_by_label("Email").click()
    page.get_by_label("Email").fill("admin@nina.no")
    page.get_by_label("Email").press("Tab")
    page.get_by_label("Password").fill("admin")
    page.get_by_label("Password").press("Enter")


@pytest.mark.skip(reason="E2E tests skipped")
def test_login(page, live_server_url):
    page.goto(live_server_url)
    do_login(page)
    assert page.url == "{}{}".format(live_server_url, "/genrequests/")


def get_path(url, prefix):
    return url.replace(prefix, "")


@pytest.mark.skip(reason="E2E tests skipped")
def test_genrequest_flow(page, live_server_url):
    page.goto(live_server_url)
    do_login(page)

    # Test create
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

    # Test edit
    page.get_by_role("link", name="Edit").click()
    page.get_by_label("Expected total samples:").fill("500")
    page.get_by_role("button", name="Submit").click()
    page.get_by_role("link", name="Orders").wait_for()
    assert page.get_by_role("link", name="Orders").count() == 1

    # Test delete
    page.get_by_role("link", name="Delete").click()
    assert re.match(
        r"\/genrequests\/\d+\/delete\/", get_path(page.url, live_server_url)
    )
    page.get_by_role("button", name="Confirm").click()
    assert re.match(r"\/genrequests\/", get_path(page.url, live_server_url))


@pytest.mark.skip(reason="E2E tests skipped")
def test_equipment_flow(page, live_server_url):
    page.goto(live_server_url + "/genrequests/1/")
    page.get_by_role("link", name="Hide »").click()
    do_login(page)

    page.get_by_role("link", name="+ Equipment order").click()
    page.wait_for_load_state()

    page.get_by_label("Name:").click()
    page.get_by_label("Name:").fill("test equipment")
    page.get_by_text("Name: Needs guidSample types:").click()
    page.get_by_label("Needs guid").check()
    page.get_by_role("listbox").first.select_option("1")
    page.get_by_role("button", name="Move selected right").click()
    page.get_by_label("Tags:").click()
    page.get_by_label("Tags:").fill("test")
    page.get_by_role("button", name="Submit").click()
    page.wait_for_load_state()

    page.get_by_placeholder("Select").click()
    page.locator('[id="id_0\\.equipments\\.equipment-opt-1"]').click()
    page.get_by_label("Quantity:").click()
    page.get_by_label("Quantity:").fill("2")
    page.get_by_role("button", name="Add equipment").click()
    page.locator('[id="id_1\\.equipments\\.equipment-ts-control"]').click()
    page.locator('[id="id_1\\.equipments\\.equipment-opt-6"]').click()
    page.locator('[id="id_1\\.equipments\\.quantity"]').click()
    page.locator('[id="id_1\\.equipments\\.quantity"]').fill("3")
    page.get_by_role("button", name="Submit").click()
    page.wait_for_load_state()

    page.get_by_role("link", name="Edit", exact=True).click()
    page.wait_for_load_state()

    page.locator("div").filter(
        has_text=re.compile(r"^SkjellDNA-ekstrakt$")
    ).get_by_role("listbox").select_option("18")
    page.get_by_role("button", name="Move selected right").click()
    page.get_by_role("button", name="Submit").click()
    page.wait_for_load_state()

    page.get_by_role("link", name="Edit requested equipment").click()
    page.get_by_role("button", name="Add equipment").click()
    page.locator(
        "django-form-collection:nth-child(3) > .dj-form > div:nth-child(3)"
        " > .shadow-wrapper > .ts-wrapper > .ts-control"
    ).click()
    page.locator('[id="id_2\\.equipments\\.equipment-opt-7"]').click()
    page.locator('[id="id_2\\.equipments\\.quantity"]').click()
    page.locator('[id="id_2\\.equipments\\.quantity"]').fill("1")
    page.locator('[id="id_0\\.equipments\\.quantity"]').click()
    page.locator('django-form-collection[sibling-position="0"]').hover()
    page.locator(
        'django-form-collection[sibling-position="0"] > button.remove-collection'
    ).wait_for()
    page.locator(
        'django-form-collection[sibling-position="0"] > button.remove-collection'
    ).click()
    page.get_by_role("button", name="Submit").click()
    page.wait_for_load_state()

    page.get_by_role("button", name="Deliver order").click()
    page.wait_for_load_state()


@pytest.mark.skip()
def test_extraction_flow(page, live_server_url):
    page.goto(live_server_url + "/genrequests/1/")
    page.get_by_role("link", name="Hide »").click()
    do_login(page)

    page.get_by_role("link", name="+ Extraction order").click()
    page.get_by_label("Name:").click()
    page.get_by_label("Name:").fill("ext 1")
    page.get_by_label("Name:").dblclick()
    page.get_by_label("Name:").fill("test")
    page.locator("#id_needs_guid_1").check()
    page.get_by_role("listbox").first.select_option("3")
    page.get_by_role("listbox").first.select_option("1")
    page.get_by_role("button", name="Move selected right").first.click()
    page.get_by_role("listbox").nth(2).select_option("1")
    page.get_by_role("button", name="Move selected right").nth(1).click()
    page.get_by_label("Tags:").click()
    page.get_by_label("Tags:").fill("test")
    page.locator("#id_pre_isolated").get_by_text("No").click()
    page.locator("#id_return_samples").get_by_text("No").click()
    page.get_by_role("button", name="Submit").click()
    page.wait_for_load_state()

    page.locator("div").filter(has_text=re.compile(r"^Year$")).get_by_role(
        "textbox"
    ).click()
    page.locator("div").filter(has_text=re.compile(r"^Year$")).get_by_role(
        "textbox"
    ).fill("2050")
    page.get_by_role("button", name="Add 1 rows").click()
    page.get_by_role("textbox").nth(2).click()
    page.get_by_role("textbox").nth(2).fill("test")
    page.locator("div").filter(has_text="Sample NameSpeciesYearPop").nth(4).click()
    page.get_by_role("button", name="Validate samples").click()
    page.get_by_role("link", name="Summary").click()
    page.wait_for_load_state()
    page.get_by_role("link", name=" back to order").click()
    page.wait_for_load_state()
    page.get_by_role("button", name="Deliver order").click()
    page.wait_for_load_state()
    expect(page.locator("tbody")).to_contain_text("confirmed")
