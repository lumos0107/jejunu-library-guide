"""PRD 7장 성능 측정: 첫 화면(first-render)과 검색(input → search-rendered), 5회 중앙값. data.js 크기도 출력.
사용: python tools/perf.py   (로컬 file://, Chromium, 1440×900)"""
import pathlib
import statistics
import sys

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[1]
URL = (ROOT / 'index.html').as_uri()
SEARCH = """q => { const input = document.querySelector('#search-input'); input.value = q;
  const t0 = performance.now(); input.dispatchEvent(new Event('input', { bubbles: true }));
  const marks = performance.getEntriesByName('search-rendered'); return marks[marks.length - 1].startTime - t0; }"""


def main():
    first, search = [], []
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        for _ in range(5):
            page = browser.new_page(viewport={'width': 1440, 'height': 900})
            page.goto(URL)
            page.wait_for_function("performance.getEntriesByName('first-render').length > 0")
            first.append(page.evaluate("performance.getEntriesByName('first-render')[0].startTime"))
            search.append(page.evaluate(SEARCH, '통계'))
            page.close()
        browser.close()
    f, s = statistics.median(first), statistics.median(search)
    size = (ROOT / 'data.js').stat().st_size
    print(f'첫 화면 {f:.0f}ms(기준 1000) · 검색 {s:.1f}ms(기준 50) · data.js {size:,}B(예산 313,537)')
    sys.exit(0 if f <= 1000 and s <= 50 else 1)


if __name__ == '__main__':
    main()
