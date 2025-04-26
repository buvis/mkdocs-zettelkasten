import datetime

from git import Git


class GitUtil:
    def __init__(self) -> None:
        self.git = Git()

    def get_revision_date_for_file(self, path: str) -> datetime.datetime:
        return self.git.log(path, n=1, date="short", format="%ad")
