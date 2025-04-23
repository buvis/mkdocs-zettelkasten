import datetime


def convert_string_to_date(string):
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
