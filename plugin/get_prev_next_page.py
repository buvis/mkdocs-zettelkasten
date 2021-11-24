def get_prev_next_page(markdown, page, config, files, zettels):
    # handle special pages

    if page.file.src_path == "index.md":
        if len(zettels) > 0:
            return ("", zettels[0])
        else:
            return ("", "")
    elif page.file.src_path == "tags.md":
        return ("", "")

    # find the homepage

    for file in files:
        if file.src_path == "index.md":
            index_file = file

    # get previous/next zettel by ID

    if page.file.is_zettel:

        for index, item in enumerate(zettels):
            if item.zettel.id == page.file.zettel.id:
                break
        else:
            return ("", "")

        if index < len(zettels) - 1:
            next_file = zettels[index + 1]
        else:
            next_file = ""

        if index > 0:
            prev_file = zettels[index - 1]
        else:
            prev_file = index_file

        return (prev_file, next_file)

    return ("", "")
