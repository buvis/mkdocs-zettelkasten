from __future__ import annotations

import datetime
import logging

from git import Git, InvalidGitRepositoryError, Repo

logger = logging.getLogger(
    __name__.replace("mkdocs_zettelkasten.plugin.", "mkdocs.plugins.zettelkasten.")
)


class GitUtil:
    def __init__(self) -> None:
        self.git = Git()

    def get_revision_date_for_file(self, path: str) -> datetime.datetime | None:
        raw = self.git.log(path, n=1, format="%cI")
        if not raw:
            return None
        return datetime.datetime.fromisoformat(raw)

    @staticmethod
    def is_tracked(path: str) -> bool:
        try:
            repo = Repo(path, search_parent_directories=True)
            return bool(repo.git.ls_files(path))
        except InvalidGitRepositoryError:
            return False
