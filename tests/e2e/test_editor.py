"""E2E tests for markdown editor (testscript 062)."""

from playwright.sync_api import expect


def test_edit_button_visible_when_enabled(page, editor_site):
    page.goto(f"{editor_site}/20211122194827/")
    btn = page.locator("#zettel-edit-btn")
    assert btn.is_visible()


def test_edit_here_shows_token_dialog(page, editor_site):
    page.goto(f"{editor_site}/20211122194827/")
    page.click("#zettel-edit-btn")
    page.locator(".zettel-edit-dropdown-item", has_text="Edit here").click()
    dialog = page.locator("#zettel-token-dialog")
    assert dialog.get_attribute("open") is not None
    assert page.locator("#zettel-token-input").is_visible()
    assert page.locator("#zettel-token-submit").is_visible()


def test_cancel_button_restores_body(page, editor_site):
    page.goto(f"{editor_site}/20211122194827/")
    original = page.locator(".file-body").inner_text()

    # simulate editor-open state: show cancel, hide edit
    page.evaluate("""() => {
        document.getElementById('zettel-edit-btn').style.display = 'none';
        document.getElementById('zettel-cancel-btn').style.display = 'inline-block';
    }""")
    page.click("#zettel-cancel-btn")
    page.locator("#zettel-edit-btn").wait_for(state="visible")
    restored = page.locator(".file-body").inner_text()
    assert len(restored) > 0
    assert original[:50] in restored[:100]


def test_easymde_defined_when_enabled(page, editor_site):
    page.goto(f"{editor_site}/20211122194827/")
    defined = page.evaluate("typeof EasyMDE !== 'undefined'")
    assert defined is True


def test_no_edit_button_when_disabled(page, default_site):
    page.goto(f"{default_site}/20211122194827/")
    assert page.locator("#zettel-edit-btn").count() == 0


def test_easymde_undefined_when_disabled(page, default_site):
    page.goto(f"{default_site}/20211122194827/")
    defined = page.evaluate("typeof EasyMDE !== 'undefined'")
    assert defined is False


def test_single_edit_trigger_when_editor_enabled(page, editor_site):
    page.goto(f"{editor_site}/20211122194827/")
    assert page.locator("#zettel-edit-btn").count() == 1
    assert page.locator("a > svg.bi-pencil").count() == 0


def test_single_edit_trigger_when_editor_disabled(page, default_site):
    page.goto(f"{default_site}/20211122194827/")
    assert page.locator("a svg.bi-pencil").count() == 1
    assert page.locator("#zettel-edit-btn").count() == 0


def test_edit_click_shows_action_menu(page, editor_site):
    page.goto(f"{editor_site}/20211122194827/")
    page.click("#zettel-edit-btn")
    dropdown = page.locator("#zettel-edit-dropdown")
    assert dropdown.is_visible()
    items = dropdown.locator(".zettel-edit-dropdown-item")
    assert items.count() == 2


def test_edit_on_github_has_correct_url(page, editor_site):
    page.goto(f"{editor_site}/20211122194827/")
    page.click("#zettel-edit-btn")
    link = page.locator(".zettel-edit-dropdown-item", has_text="Edit on GitHub")
    href = link.get_attribute("href")
    assert "github.com" in href
    assert "20211122194827" in href


def test_dropdown_closes_on_outside_click(page, editor_site):
    page.goto(f"{editor_site}/20211122194827/")
    page.click("#zettel-edit-btn")
    assert page.locator("#zettel-edit-dropdown").is_visible()
    page.click(".file-body")
    expect(page.locator("#zettel-edit-dropdown")).to_have_count(0)


def test_dropdown_closes_on_toggle_click(page, editor_site):
    page.goto(f"{editor_site}/20211122194827/")
    page.click("#zettel-edit-btn")
    assert page.locator("#zettel-edit-dropdown").is_visible()
    page.click("#zettel-edit-btn")
    expect(page.locator("#zettel-edit-dropdown")).to_have_count(0)


def test_forget_token_clears_session_storage(page, editor_site):
    page.goto(f"{editor_site}/20211122194827/")
    page.evaluate("sessionStorage.setItem('zettel-pat', 'ghp_test')")
    page.reload()
    page.wait_for_load_state("domcontentloaded")
    forget_btn = page.locator("#zettel-forget-token-btn")
    assert forget_btn.is_visible()
    forget_btn.click()
    val = page.evaluate("sessionStorage.getItem('zettel-pat')")
    assert val is None
    assert not forget_btn.is_visible()


def test_forget_token_hidden_when_no_token(page, editor_site):
    page.goto(f"{editor_site}/20211122194827/")
    page.evaluate("sessionStorage.removeItem('zettel-pat')")
    page.reload()
    page.wait_for_load_state("domcontentloaded")
    assert not page.locator("#zettel-forget-token-btn").is_visible()


def test_token_dialog_closes_on_x(page, editor_site):
    page.goto(f"{editor_site}/20211122194827/")
    page.click("#zettel-edit-btn")
    page.locator(".zettel-edit-dropdown-item", has_text="Edit here").click()
    dialog = page.locator("#zettel-token-dialog")
    assert dialog.get_attribute("open") is not None
    page.locator("#zettel-token-dialog .modal-close").click()
    dialog.wait_for(state="hidden")
    assert dialog.get_attribute("open") is None


def test_pencil_links_to_github_when_editor_disabled(page, default_site):
    page.goto(f"{default_site}/20211122194827/")
    link = page.locator("a:has(svg.bi-pencil)")
    href = link.get_attribute("href")
    assert "github.com" in href
    assert page.locator("#zettel-edit-dropdown").count() == 0
