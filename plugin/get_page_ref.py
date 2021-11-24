from markdown import Markdown


def get_page_ref(markdown, page, config, files):
    content_lines = markdown.rstrip().split("\n")

    # process footer from bottom till --- delimiter

    if content_lines[-1] == "---":
        n = 2
        ref_lines = []

        while content_lines[-n] != "---" and n < len(content_lines):
            ref_lines.append(" - " + content_lines[-n])
            n = n + 1

        # remove footer from page's markdown source
        markdown = "\n".join(content_lines[: -n - 1])
        # restore the order of references (as we went bottom->up)
        ref_lines.reverse()
        page.ref = "\n".join(ref_lines)
        # convert the reference footer to HTML
        processor = Markdown(
            extensions=config["markdown_extensions"],
            extension_configs=config["mdx_configs"] or {},
        )

        return (markdown, processor.convert(page.ref))

    return (markdown, None)
