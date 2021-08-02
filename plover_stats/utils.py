import locale

locale.setlocale(locale.LC_ALL, "")


def format_number(value: int) -> str:
    return f"{value:n}"
