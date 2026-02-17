import datetime
from unittest.mock import MagicMock, patch

from git import InvalidGitRepositoryError

from mkdocs_zettelkasten.plugin.utils.git_utils import GitUtil

GIT_DATE_ISO = "2025-01-15T10:30:00+01:00"


class TestGetRevisionDateForFile:
    def test_returns_datetime_from_git_log(self) -> None:
        util = GitUtil()
        with patch.object(util, "git") as mock_git:
            mock_git.log.return_value = GIT_DATE_ISO
            result = util.get_revision_date_for_file("/some/path.md")

        assert isinstance(result, datetime.datetime)
        assert result == datetime.datetime.fromisoformat(GIT_DATE_ISO)

    def test_returns_none_when_no_git_history(self) -> None:
        util = GitUtil()
        with patch.object(util, "git") as mock_git:
            mock_git.log.return_value = ""
            result = util.get_revision_date_for_file("/some/path.md")

        assert result is None


class TestIsTracked:
    def test_returns_true_for_tracked_file(self) -> None:
        with patch("mkdocs_zettelkasten.plugin.utils.git_utils.Repo") as mock_repo_cls:
            mock_repo = MagicMock()
            mock_repo.git.ls_files.return_value = "some/path.md"
            mock_repo_cls.return_value = mock_repo

            assert GitUtil.is_tracked("/repo/some/path.md") is True
            mock_repo_cls.assert_called_once_with(
                "/repo/some/path.md",
                search_parent_directories=True,
            )

    def test_returns_false_for_untracked_file(self) -> None:
        with patch("mkdocs_zettelkasten.plugin.utils.git_utils.Repo") as mock_repo_cls:
            mock_repo = MagicMock()
            mock_repo.git.ls_files.return_value = ""
            mock_repo_cls.return_value = mock_repo

            assert GitUtil.is_tracked("/repo/some/path.md") is False

    def test_returns_false_outside_git_repo(self) -> None:
        with patch("mkdocs_zettelkasten.plugin.utils.git_utils.Repo") as mock_repo_cls:
            mock_repo_cls.side_effect = InvalidGitRepositoryError("/not/a/repo")

            assert GitUtil.is_tracked("/not/a/repo/file.md") is False
