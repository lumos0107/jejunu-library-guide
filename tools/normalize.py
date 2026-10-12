"""JS LG.normalize와 같은 규칙의 Python 구현(검사용)."""
import unicodedata


def normalize(value):
    s = unicodedata.normalize('NFKC', str(value or '')).lower()
    return ''.join(ch for ch in s if not (ch.isspace() or unicodedata.category(ch)[0] in 'PS'))
