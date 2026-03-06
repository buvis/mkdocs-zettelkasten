from conftest import ZETTEL_INSTALL


def test_graph_page_loads(page, graph_site):
    page.goto(f"{graph_site}/graph.html")
    assert "Graph View" in page.title()


def test_graph_renders_canvas(page, graph_site):
    page.goto(f"{graph_site}/graph.html")
    canvas = page.locator("#graph-container canvas")
    canvas.wait_for(state="attached", timeout=5000)
    assert canvas.count() == 1


def test_graph_has_nodes(page, graph_site):
    page.goto(f"{graph_site}/graph.html")
    page.locator("#graph-container[data-node-count]").wait_for(
        state="attached", timeout=5000
    )
    count = page.locator("#graph-container").get_attribute("data-node-count")
    assert count is not None
    assert int(count) > 0


def test_graph_nav_link_visible(page, graph_site):
    page.goto(graph_site)
    link = page.locator("a[href*='graph.html']")
    assert link.count() >= 1


def test_graph_nav_link_hidden_when_disabled(page, default_site):
    page.goto(default_site)
    link = page.locator("a[href*='graph.html']")
    assert link.count() == 0


def test_local_graph_visible_on_zettel_page(page, graph_site):
    page.goto(f"{graph_site}/{ZETTEL_INSTALL}/")
    container = page.locator("#local-graph-container")
    container.wait_for(state="attached", timeout=5000)
    canvas = container.locator("canvas")
    canvas.wait_for(state="attached", timeout=5000)
    assert canvas.count() == 1


def test_local_graph_hidden_when_disabled(page, default_site):
    page.goto(f"{default_site}/{ZETTEL_INSTALL}/")
    container = page.locator("#local-graph-container")
    assert container.count() == 0


class TestGraphToolbar:
    def test_toolbar_visible_on_graph_page(self, page, graph_site):
        page.goto(f"{graph_site}/graph.html")
        page.locator("#graph-container canvas").wait_for(state="attached", timeout=5000)
        toolbar = page.locator("#graph-toolbar")
        assert toolbar.inner_text() != ""

    def test_toolbar_has_node_count(self, page, graph_site):
        page.goto(f"{graph_site}/graph.html")
        page.locator("#graph-container canvas").wait_for(state="attached", timeout=5000)
        count = page.locator(".graph-node-count")
        assert count.count() >= 1
        text = count.first.inner_text()
        assert "notes" in text

    def test_search_input_present(self, page, graph_site):
        page.goto(f"{graph_site}/graph.html")
        page.locator("#graph-container canvas").wait_for(state="attached", timeout=5000)
        search = page.locator("#graph-search")
        assert search.count() == 1

    def test_tag_pills_rendered(self, page, graph_site):
        page.goto(f"{graph_site}/graph.html")
        page.locator("#graph-container canvas").wait_for(state="attached", timeout=5000)
        pills = page.locator(".graph-tag-pill")
        assert pills.count() >= 1

    def test_color_mode_selector_present(self, page, graph_site):
        page.goto(f"{graph_site}/graph.html")
        page.locator("#graph-container canvas").wait_for(state="attached", timeout=5000)
        select = page.locator(".graph-color-mode select")
        assert select.count() == 1

    def test_type_filter_checkbox_present(self, page, graph_site):
        """Fixture zettels have type metadata, so Type filter group should exist."""
        page.goto(f"{graph_site}/graph.html")
        page.locator("#graph-container canvas").wait_for(state="attached", timeout=5000)
        labels = page.locator(".graph-filter-label")
        texts = [labels.nth(i).inner_text() for i in range(labels.count())]
        assert "Type" in texts

    def test_toolbar_absent_on_local_graph(self, page, graph_site):
        """The toolbar should only appear on the full graph page, not on zettel pages."""
        page.goto(f"{graph_site}/{ZETTEL_INSTALL}/")
        page.locator("#local-graph-container canvas").wait_for(
            state="attached", timeout=5000
        )
        toolbar = page.locator("#graph-toolbar")
        # Toolbar div doesn't exist on zettel pages (only graph.html has it)
        assert toolbar.count() == 0

    def test_search_filters_nodes(self, page, graph_site):
        page.goto(f"{graph_site}/graph.html")
        page.locator("#graph-container canvas").wait_for(state="attached", timeout=5000)
        count_before = page.locator(".graph-node-count").first.inner_text()
        page.locator("#graph-search").fill("Install")
        # graph.js debounces search input by 200ms; wait 2x for filter + render
        page.wait_for_timeout(400)
        count_after = page.locator(".graph-node-count").first.inner_text()
        # Should show fewer nodes after filtering
        before_num = int(count_before.split("/")[0])
        after_num = int(count_after.split("/")[0])
        assert after_num < before_num
