"""E2E tests for Folgezettel (sequence) navigation."""

EPISTEMOLOGY = "20260225100000"
JTB = "20260225100100"
GETTIER = "20260225100200"
RELIABILISM = "20260225100300"


class TestSequenceBreadcrumb:
    def test_leaf_shows_breadcrumb(self, page, default_site):
        """Gettier Problems should show: Epistemology > JTB Theory > Gettier Problems."""
        page.goto(f"{default_site}/{GETTIER}/")
        breadcrumb = page.locator(".sequence-breadcrumb")
        assert breadcrumb.count() >= 1
        text = breadcrumb.first.inner_text()
        assert "Epistemology" in text
        assert "JTB Theory" in text

    def test_mid_node_shows_breadcrumb(self, page, default_site):
        """JTB Theory should show: Epistemology > JTB Theory."""
        page.goto(f"{default_site}/{JTB}/")
        breadcrumb = page.locator(".sequence-breadcrumb")
        assert breadcrumb.count() >= 1
        text = breadcrumb.first.inner_text()
        assert "Epistemology" in text

    def test_root_has_no_breadcrumb(self, page, default_site):
        """Epistemology is the root — no sequence breadcrumb."""
        page.goto(f"{default_site}/{EPISTEMOLOGY}/")
        breadcrumb = page.locator(".sequence-breadcrumb")
        assert breadcrumb.count() == 0


class TestSequenceBranches:
    def test_root_shows_branches(self, page, default_site):
        """Epistemology should show JTB Theory and Reliabilism as branches."""
        page.goto(f"{default_site}/{EPISTEMOLOGY}/")
        branches = page.locator(".sequence-branches")
        assert branches.count() >= 1
        text = branches.first.inner_text()
        assert "JTB Theory" in text
        assert "Reliabilism" in text

    def test_mid_node_shows_branches(self, page, default_site):
        """JTB Theory should show Gettier Problems as a branch."""
        page.goto(f"{default_site}/{JTB}/")
        branches = page.locator(".sequence-branches")
        assert branches.count() >= 1
        text = branches.first.inner_text()
        assert "Gettier Problems" in text

    def test_leaf_has_no_branches(self, page, default_site):
        """Gettier Problems has no children — no branches section."""
        page.goto(f"{default_site}/{GETTIER}/")
        branches = page.locator(".sequence-branches")
        assert branches.count() == 0


class TestSequenceTree:
    def test_tree_visible_on_sequence_note(self, page, default_site):
        page.goto(f"{default_site}/{JTB}/")
        tree = page.locator(".sequence-tree")
        assert tree.count() >= 1

    def test_tree_contains_all_sequence_notes(self, page, default_site):
        page.goto(f"{default_site}/{JTB}/")
        tree = page.locator(".sequence-tree")
        text = tree.first.inner_text()
        assert "Epistemology" in text
        assert "JTB Theory" in text
        assert "Gettier Problems" in text
        assert "Reliabilism" in text

    def test_tree_highlights_current_note(self, page, default_site):
        page.goto(f"{default_site}/{JTB}/")
        current = page.locator(".sequence-tree .current strong")
        assert current.count() >= 1
        assert "JTB Theory" in current.first.inner_text()

    def test_tree_absent_on_non_sequence_note(self, page, default_site):
        page.goto(f"{default_site}/20211122194827/")
        tree = page.locator(".sequence-tree")
        assert tree.count() == 0

    def test_tree_collapsible(self, page, default_site):
        page.goto(f"{default_site}/{JTB}/")
        details = page.locator("details.sequence-tree")
        assert details.count() >= 1
        assert details.first.get_attribute("open") is not None


class TestSequenceLinks:
    def test_breadcrumb_links_navigate(self, page, default_site):
        """Clicking Epistemology in Gettier's breadcrumb should navigate there."""
        page.goto(f"{default_site}/{GETTIER}/")
        page.locator(".sequence-breadcrumb a", has_text="Epistemology").click()
        page.wait_for_url(f"**/{EPISTEMOLOGY}/")

    def test_branch_links_navigate(self, page, default_site):
        """Clicking JTB Theory in Epistemology's branches should navigate there."""
        page.goto(f"{default_site}/{EPISTEMOLOGY}/")
        page.locator(".sequence-branches a", has_text="JTB Theory").click()
        page.wait_for_url(f"**/{JTB}/")
