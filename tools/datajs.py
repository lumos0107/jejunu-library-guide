"""data.js(window.LIBRARY_GUIDE) 읽기·쓰기. v2 data.js와 바이트 단위로 같은 형식으로 쓴다."""
import json
import pathlib

PREFIX = 'window.LIBRARY_GUIDE = '


def load(path='data.js'):
    text = pathlib.Path(path).read_text(encoding='utf-8')
    if not text.startswith(PREFIX):
        raise ValueError(f'{path}: "{PREFIX}"로 시작하지 않습니다')
    body = text[len(PREFIX):].rstrip()
    if body.endswith(';'):
        body = body[:-1]
    return json.loads(body)


def dump(obj):
    return PREFIX + json.dumps(obj, ensure_ascii=False, indent=2) + ';\n'
