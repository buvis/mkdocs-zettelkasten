class TestWorkflow:
    def test_workflow_page_loads(self, page, workflow_site):
        response = page.goto(f"{workflow_site}/workflow.html")
        assert response.status == 200

    def test_stats_section_visible(self, page, workflow_site):
        page.goto(f"{workflow_site}/workflow.html")
        content = page.locator(".file-body").inner_text()
        assert "notes" in content

    def test_inbox_section_visible(self, page, workflow_site):
        """Fixture 20260227100200 is type: fleeting -> appears in inbox."""
        page.goto(f"{workflow_site}/workflow.html")
        content = page.locator(".file-body").inner_text()
        assert "Inbox" in content
        assert "Quick idea on tagging" in content

    def test_review_queue_visible(self, page, workflow_site):
        """Fixture 20250101000000 is maturity: developing, old -> review queue."""
        page.goto(f"{workflow_site}/workflow.html")
        content = page.locator(".file-body").inner_text()
        assert "Review Queue" in content
        assert "Developing note on learning" in content

    def test_navbar_icon_visible(self, page, workflow_site):
        page.goto(f"{workflow_site}/workflow.html")
        icon = page.locator(".fa-inbox")
        assert icon.count() >= 1

    def test_navbar_badge_shows_inbox_count(self, page, workflow_site):
        page.goto(f"{workflow_site}/workflow.html")
        badge = page.locator(".nav-icon-badge .badge-warning")
        assert badge.count() >= 1

    def test_workflow_absent_when_disabled(self, page, default_site):
        response = page.goto(f"{default_site}/workflow.html")
        assert response.status == 404
