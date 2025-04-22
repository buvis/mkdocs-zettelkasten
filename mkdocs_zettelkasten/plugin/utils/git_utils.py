from git import Git


class GitUtil:
    def __init__(self):
        self.git = Git()

    def get_revision_date_for_file(self, path: str):
        return self.git.log(path, n=1, date="short", format="%ad")
