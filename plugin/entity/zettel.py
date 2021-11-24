import datetime
import os
import re
import yaml

from pathlib import Path

from plugin.patterns import WIKI_LINK, MD_LINK
from plugin.gitutil import GitUtil


class Zettel:
    def __init__(self, abs_src_path):
        self.id = 0
        self.title = ""
        self.path = abs_src_path
        self.backlinks = []
        self.links = []
        self._parse_file()

    def _parse_file(self):
        header = []
        is_reading_header = False
        is_reading_body = False
        alternative_title = ""
        try:
            with open(self.path, encoding="utf-8-sig", errors="strict") as f:
                while line := f.readline():
                    if line.strip() == "---":
                        if not is_reading_header and not is_reading_body:
                            is_reading_header = True

                            continue
                        elif not is_reading_body:
                            is_reading_header = False
                            is_reading_body = True

                            continue
                        else:
                            break

                    if is_reading_header:
                        header.append(line)

                    if is_reading_body:
                        if line.lstrip().startswith("# "):
                            alternative_title = line.strip()[2:]
                        match_wiki_link = WIKI_LINK.finditer(line)
                        match_md_link = MD_LINK.finditer(line)

                        for m in match_wiki_link:
                            self.links.append(m.groupdict()["url"])

                        for m in match_md_link:
                            self.links.append(m.groupdict()["url"])
            meta = yaml.load("".join(header), Loader=yaml.FullLoader)
        except OSError:
            raise ValueError("File is not in zettel format")
        except ValueError:
            raise ValueError("File is not in zettel format")
        except AttributeError:
            raise ValueError("File is not in zettel format")
        self._set_metadata(meta, alternative_title)

    def _set_metadata(self, meta, alternative_title):
        if not meta or "id" not in meta.keys():
            raise ValueError("File is not in zettel format")
        else:
            self.id = meta["id"]

        if "title" in meta.keys():
            self.title = meta["title"]
        elif alternative_title:
            print("Using alternative title " + self.path)
            self.title = alternative_title
        else:
            self.title = self._get_title_from_filename()

        self._set_last_update_date(meta)

    def _get_title_from_filename(self):
        title = Path(self.path).stem
        title = re.sub(r"^\d{14}", "", title)
        title = title.replace("_", " ").replace("-", " ")
        title = " ".join(title.split())
        title = title.strip()
        title = title.capitalize()

        return title

    def _set_last_update_date(self, meta):
        date = ""

        if "last_update" in meta.keys():
            date = _get_date_from_string(meta["last_update"])

        if not date and "date" in meta.keys():
            date = _get_date_from_string(meta["date"])

        if not date:
            date = _get_date_from_string(self.id)

        if not date:
            date = datetime.datetime.today()

        if "//github.com" in self.path or "//gitlab.com" in self.path:
            git = GitUtil()
            revision_date = git.get_revision_date_for_file(self.path)
        else:
            revision_date = datetime.datetime.fromtimestamp(os.path.getmtime(self.path))

        if revision_date.timestamp() > date.timestamp():
            date = revision_date

        self.last_update_date = date.strftime("%Y-%m-%d")

    def add_backlinks(self, sources):
        def is_valid(source):
            return (
                self.path != source.abs_src_path
                and source not in self.backlinks
                and source.is_zettel
            )

        self.backlinks = [s for s in sources if is_valid(s)]


def _get_date_from_string(string):
    string = str(string)
    try:
        date = datetime.datetime.strptime(string, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        try:
            date = datetime.datetime.strptime(string, "%Y%m%d%H%M%S")
        except ValueError:
            try:
                date = datetime.datetime.fromisoformat(string)
            except ValueError:
                date = ""

    return date
