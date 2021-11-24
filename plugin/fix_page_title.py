def fix_page_title(markdown, page, config, files):
    if not page.file.is_zettel:
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
