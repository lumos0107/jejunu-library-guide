"""Playwright 스모크 테스트 실행기(외부 패키지 없음).
사용: python tests/smoke.py --stage 1 [--browsers chromium,webkit] [--modes file,http] [--base URL] [-k 이름일부]
"""
import argparse
import functools
import http.server
import importlib
import pathlib
import sys
import threading

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tests'))
sys.path.insert(0, str(ROOT / 'tools'))
import harness  # noqa: E402
from helpers import Site, VIEWPORTS  # noqa: E402


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def start_server(root):
    handler = functools.partial(QuietHandler, directory=str(root))
    httpd = http.server.ThreadingHTTPServer(('127.0.0.1', 0), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd, f'http://127.0.0.1:{httpd.server_address[1]}/'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--stage', type=int, default=1)
    ap.add_argument('--browsers', default='chromium')
    ap.add_argument('--modes', default='file')
    ap.add_argument('--base')
    ap.add_argument('-k', default='')
    a = ap.parse_args()

    for mod in sorted((ROOT / 'tests').glob('test_*.py')):
        importlib.import_module(mod.stem)
    tests = [t for t in harness.REGISTRY if t['stage'] <= a.stage and a.k in t['name']]

    bases = []
    if a.base:
        bases.append(('deploy', a.base.rstrip('/') + '/'))
    else:
        if 'file' in a.modes:
            bases.append(('file', ROOT.as_uri() + '/'))
        if 'http' in a.modes:
            _, url = start_server(ROOT)
            bases.append(('http', url))

    total = failures = 0
    with sync_playwright() as pw:
        for bname in a.browsers.split(','):
            browser = getattr(pw, bname).launch()
            for mode, base in bases:
                for t in tests:
                    total += 1
                    ctx = browser.new_context(viewport=VIEWPORTS[t['viewport']], locale='ko-KR',
                                              timezone_id='Asia/Seoul', reduced_motion=t['motion'])
                    page = ctx.new_page()
                    # PRD 부록 A 기준일로 시계를 고정한다. 날짜를 다루는 테스트는 page.clock으로 다시 정한다(S13)
                    if t['clock']:
                        page.clock.set_fixed_time('2026-10-15T10:00:00+09:00')
                    errors = []
                    page.on('pageerror', lambda e, errs=errors: errs.append(str(e)))
                    page.on('console', lambda m, errs=errors: errs.append(f'{m.text} @ {m.location.get("url", "")}')
                            if m.type == 'error' else None)
                    label = f'[{bname}/{mode}] {t["name"]}'
                    try:
                        site = Site(page, base, errors)
                        t['fn'](site)
                        # 지난 35개 항목의 '콘솔·페이지 오류 없음'을 모든 테스트에 적용한다(RESEARCH 6장)
                        harness.check(not site.console_errors(), f'콘솔·페이지 오류: {site.console_errors()[:3]}')
                        print('PASS', label)
                    except Exception as e:  # noqa: BLE001
                        failures += 1
                        print('FAIL', label, '-', (str(e).splitlines() or [repr(e)])[0][:300])  # 메시지 없는 예외도 출력
                    finally:
                        ctx.close()
            browser.close()
    print(f'\n{total - failures}/{total} 통과')
    sys.exit(1 if failures else 0)


if __name__ == '__main__':
    main()
