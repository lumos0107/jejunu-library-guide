"""data/*.json → data.js 생성.
사용: python tools/build_data.py          # data.js를 쓴다
      python tools/build_data.py --check  # 생성 결과가 저장된 data.js와 같은지만 확인(쓰지 않음)
"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import datajs  # noqa: E402

DATA = ROOT / 'data'


def load(name):
    return json.loads((DATA / name).read_text(encoding='utf-8'))


def assemble():
    meta = load('meta.json')
    return {
        'checkedAt': meta['checkedAt'],
        'categories': load('categories.json'),
        'services': load('services.json'),
        'resources': load('resources.json'),
        'directory': load('directory.json'),
        'metadata': meta['metadata'],
        'related': load('related.json'),
        'bookCases': load('book-cases.json'),
        'notices': load('notices.json'),
        'commonText': load('common-text.json'),
    }


def main():
    text = datajs.dump(assemble())
    target = ROOT / 'data.js'
    if '--check' in sys.argv:
        same = target.exists() and target.read_text(encoding='utf-8') == text
        print('data.js 일치' if same else 'data.js가 data/*.json과 다릅니다. python tools/build_data.py 로 다시 만드세요')
        sys.exit(0 if same else 1)
    target.write_text(text, encoding='utf-8', newline='\n')
    print('data.js 생성', len(text.encode('utf-8')), 'bytes')


if __name__ == '__main__':
    main()
