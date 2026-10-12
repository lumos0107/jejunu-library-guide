"""페이지의 모든 요소에 대해 주요 계산된 스타일을 JSON으로 뽑아 비교한다.
사용: python tools/css_snapshot.py <사이트폴더> <출력.json>
      python tools/css_snapshot.py --compare a.json b.json
"""
import json
import pathlib
import sys

from playwright.sync_api import sync_playwright

PROPS = ['display', 'position', 'color', 'background-color', 'font-size', 'font-weight', 'line-height',
         'margin-top', 'margin-bottom', 'padding-top', 'padding-left', 'gap', 'align-items',
         'justify-content', 'grid-template-columns', 'max-width', 'border-top-width', 'border-radius',
         'outline-style', 'overflow-wrap', 'text-align', 'width', 'height']
JS = """props => Array.from(document.querySelectorAll('body *')).map((el, i) => {
  const cs = getComputedStyle(el); const o = {i, tag: el.tagName, id: el.id, cls: el.className && String(el.className)};
  for (const p of props) o[p] = cs.getPropertyValue(p); return o; })"""


def snapshot(site, out):
    res = {}
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        # 800px: 561~850px 구간(두 미디어쿼리 사이)의 회귀를 잡는다(R20)
        for name, vp in (('desktop', {'width': 1440, 'height': 900}), ('tablet', {'width': 800, 'height': 1000}),
                         ('mobile', {'width': 390, 'height': 844})):
            p = b.new_page(viewport=vp)
            p.goto(pathlib.Path(site).resolve().joinpath('index.html').as_uri())
            p.wait_for_selector('#service-grid .service-card')
            res[name] = p.evaluate(JS, PROPS)
            p.close()
        b.close()
    pathlib.Path(out).write_text(json.dumps(res, ensure_ascii=False), encoding='utf-8')


def compare(a, b):
    A, B = (json.loads(pathlib.Path(x).read_text(encoding='utf-8')) for x in (a, b))
    diffs = []
    for vp in A:
        for ea, eb in zip(A[vp], B[vp]):
            for k in ea:
                if ea[k] != eb.get(k):
                    diffs.append(f'{vp} #{ea["i"]} {ea["tag"]}.{ea["cls"]} {k}: {ea[k]} → {eb.get(k)}')
        if len(A[vp]) != len(B[vp]):
            diffs.append(f'{vp}: 요소 수 {len(A[vp])} → {len(B[vp])}')
    print('\n'.join(diffs[:40]) or '차이 없음')
    return not diffs


if __name__ == '__main__':
    if sys.argv[1] == '--compare':
        sys.exit(0 if compare(sys.argv[2], sys.argv[3]) else 1)
    snapshot(sys.argv[1], sys.argv[2])
