"""Page adapters — transform markdown and page.meta during on_page_markdown.

Contract: each adapter is a function taking (markdown, page, config, ...) and
returning transformed markdown. Side effects on page.meta (e.g. setting
page.meta["ref"]) are intentional — they enrich the page object that templates
consume. PageTransformer chains adapters in a fixed order.
"""
