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
