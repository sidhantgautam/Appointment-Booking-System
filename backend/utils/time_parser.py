import dateparser


def normalize_time(time_text: str):

    parsed = dateparser.parse(time_text)

    if not parsed:
        return None

    return parsed.strftime("%Y-%m-%d %H:%M")