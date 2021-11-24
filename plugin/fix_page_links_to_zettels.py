from plugin.patterns import WIKI_LINK, MD_LINK


def fix_page_links_to_zettels(markdown, page, config, files, zettels):
    def process_match(m):
        if "url" in m.groupdict().keys():
            url = m.groupdict()["url"]

        if "title" in m.groupdict().keys():
            title = m.groupdict()["title"]
        else:
            title = url

        for z in zettels:
            if not url.endswith(".md"):
                url_with_suffix = url + ".md"
            else:
                url_with_suffix = url

            if url_with_suffix in z.src_path:
                if title == url_with_suffix or title + ".md" == url_with_suffix:
                    title = z.zettel.title
                new_url = config["site_url"] + z.url

                return f"[{title}]({new_url})"

        return f"[{title}]({url})"

    markdown = WIKI_LINK.sub(process_match, markdown)
    markdown = MD_LINK.sub(process_match, markdown)

    return markdown
