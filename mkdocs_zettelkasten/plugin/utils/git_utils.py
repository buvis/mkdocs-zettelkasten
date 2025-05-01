import datetime
import logging

from git import Git

logger = logging.getLogger(
    __name__.replace("mkdocs_zettelkasten.plugin.", "mkdocs.plugins.zettelkasten.")
)


class GitUtil:
    def __init__(self) -> None:
        self.git = Git()

    def get_revision_date_for_file(self, path: str) -> datetime.datetime:
        return self.git.log(path, n=1, date="short", format="%ad")
