from mkdocs.plugins import BasePlugin

from plugin.fix_page_links_to_zettels import fix_page_links_to_zettels
from plugin.fix_page_title import fix_page_title
from plugin.get_page_ref import get_page_ref
from plugin.get_prev_next_page import get_prev_next_page
from plugin.get_zettels import get_zettels


class ZettelkastenPlugin(BasePlugin):

    config_scheme = ()

    def __init__(self):
        self.zettels = set()

    def on_files(self, files, config):
        self.zettels = get_zettels(files, config)

    def on_page_markdown(self, markdown, page, config, files):
        markdown = fix_page_title(markdown, page, config, files)
        markdown = fix_page_links_to_zettels(
            markdown, page, config, files, self.zettels
        )
        page.previous_page, page.next_page = get_prev_next_page(
            markdown, page, config, files, self.zettels
        )
        markdown, page.ref = get_page_ref(markdown, page, config, files)

        return markdown
