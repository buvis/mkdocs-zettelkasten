from plugin.entity.zettel import Zettel


def get_zettels(files, config):
    backlinks = {}
    zettels = []

    for file in files:
        try:
            file.zettel = Zettel(file.abs_src_path)
        except ValueError:
            file.is_zettel = False
        else:
            file.is_zettel = True

        if file.is_zettel:
            zettels.append(file)

            links_with_extension = []

            for link in file.zettel.links:
                if not link.endswith(".md"):
                    link += ".md"
                links_with_extension.append(link)

            links_with_extension = list(set(links_with_extension))

            for target in links_with_extension:
                if target not in backlinks:
                    backlinks[target] = []
                backlinks[target].append(file)

    for target, sources in backlinks.items():
        for file in zettels:
            if target in file.src_path:
                file.zettel.add_backlinks(sources)

    zettels.sort(key=lambda x: x.zettel.id)

    return zettels
