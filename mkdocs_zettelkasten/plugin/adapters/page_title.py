def adapt_page_title(markdown: str, page, config, files) -> str:
    """
    Adapt the page title in the markdown.
    """
    if not getattr(page.file, "is_zettel", None):
        return markdown

    has_h1_title = False

    for line in markdown.split("\n"):
        if line.strip() != "":
            if not line.lstrip().startswith("# "):
                alternative_markdown = "# " + page.file.zettel.title + "\n" + markdown
            else:
                has_h1_title = True

                break

    if not has_h1_title:
        return alternative_markdown
    else:
        return markdown
