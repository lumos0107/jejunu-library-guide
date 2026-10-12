"""v2 데이터를 data/*.json으로 옮기고(--write) 기준 커밋과 같은지 확인한다(--verify). 1회용.
기준 커밋: tools/v2-base.txt
"""
import argparse
import collections
import io
import json
import pathlib
import subprocess
import sys
import tarfile
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import build_data  # noqa: E402
import datajs  # noqa: E402

DATA = ROOT / 'data'
BASE = (ROOT / 'tools' / 'v2-base.txt').read_text().strip()


def git_show(path):
    return subprocess.run(['git', 'show', f'{BASE}:{path}'], cwd=ROOT, capture_output=True, check=True).stdout.decode('utf-8')


def js_const(source, name):
    start = source.index(f'const {name} =')
    i = source.index('{', start)
    depth = 0
    for j in range(i, len(source)):
        depth += {'{': 1, '}': -1}.get(source[j], 0)
        if depth == 0:
            literal = source[i:j + 1]
            break
    code = 'const vm=require("vm");process.stdout.write(JSON.stringify(vm.runInNewContext("("+process.argv[1]+")")))'
    out = subprocess.run(['node', '-e', code, literal], capture_output=True, check=True).stdout.decode('utf-8')
    return json.loads(out)


def base_data():
    text = git_show('data.js')
    return json.loads(text[len(datajs.PREFIX):].rstrip().rstrip(';'))


def common_text(d):
    res = {}
    for field, kinds in (('caution', ('resources', 'directory')), ('steps', ('resources', 'directory')), ('question', ('directory',))):
        counter = collections.Counter()
        for k in kinds:
            for r in d[k]:
                vals = r.get(field) or []
                counter.update(v for v in (vals if isinstance(vals, list) else [vals]) if v)
        res[field] = sorted(v for v, n in counter.items() if n >= 10)
    res['keywordSuffix'] = '공식 메뉴'
    return res


def write(name, obj):
    (DATA / name).write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')


def do_write():
    DATA.mkdir(exist_ok=True)
    d = base_data()
    app = git_show('js/app.js')
    write('meta.json', {'checkedAt': d['checkedAt'], 'metadata': d['metadata']})
    for k in ('categories', 'services', 'resources', 'directory'):
        write(f'{k}.json', d[k])
    write('related.json', js_const(app, 'relatedMap'))
    write('book-cases.json', js_const(app, 'bookCases'))
    write('notices.json', [])
    write('common-text.json', common_text(d))
    print('data/*.json 작성 완료')


def render_dump(site_dir):
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        p = b.new_page()
        p.goto((pathlib.Path(site_dir) / 'index.html').resolve().as_uri())
        p.wait_for_selector('#service-grid .service-card')
        ids = p.evaluate('window.LIBRARY_GUIDE.services.map(s => s.id)')
        related = {}
        for rid in ids:
            p.evaluate("""rid => { const b = document.createElement('button'); b.dataset.open = rid; b.hidden = true;
                document.body.append(b); b.click(); b.remove(); }""", rid)
            related[rid] = p.eval_on_selector_all('#detail-content .related button', 'els => els.map(e => e.textContent)')
            p.keyboard.press('Escape')
        books = {}
        for key in p.eval_on_selector_all('[data-book]', 'els => els.map(e => e.dataset.book)'):
            p.click(f'[data-book="{key}"]')
            books[key] = p.inner_text('#book-result')
        b.close()
    return related, books


def do_verify():
    ok = True
    d = base_data()
    new = build_data.assemble()
    for k in d:
        if d[k] != new[k]:
            ok = False
            print('불일치:', k)
    app = git_show('js/app.js')
    if new['related'] != js_const(app, 'relatedMap'):
        ok = False
        print('불일치: related')
    if new['bookCases'] != js_const(app, 'bookCases'):
        ok = False
        print('불일치: bookCases')
    archive = subprocess.run(['git', 'archive', '--format=tar', BASE], cwd=ROOT, capture_output=True, check=True).stdout
    with tempfile.TemporaryDirectory() as tmp:
        tarfile.open(fileobj=io.BytesIO(archive)).extractall(tmp)
        if render_dump(tmp) != render_dump(ROOT):
            ok = False
            print('불일치: 관련 안내·책 상황 렌더 결과')
    print('추출 검증 통과' if ok else '추출 검증 실패')
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--write', action='store_true')
    ap.add_argument('--verify', action='store_true')
    a = ap.parse_args()
    if a.write:
        do_write()
    if a.verify:
        do_verify()
