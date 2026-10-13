"""공식 링크 도착 점검(PRD 8장, 부록 A 도착 상태 분류표, 부록 B). 기록용이며 게이트에는 넣지 않는다.
사용: python tests/check_links.py [--only 주소일부] [--limit N] [--out .tmp/links-report.md]
- 해시 주소(https://lib.jejunu.ac.kr/#/…): 브라우저로 열어 최종 주소·제목을 기록하고 정상/경고/실패로 나눈다.
- 그 밖의 https 주소(매뉴얼 첨부 등): GET 응답 코드만 본다.
- 공식 사이트에 부담을 주지 않도록 하나씩, 요청 사이에 쉰다. 브라우저에서는 GET이 아닌 요청을 막는다.
- 공식 사이트 쪽 장애는 우리 테스트 실패로 치지 않는다(K1). 종료 코드는 항상 0이고, 결과는 보고서로 남긴다."""
import argparse
import collections
import pathlib
import sys
import time
import urllib.error
import urllib.request

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import datajs  # noqa: E402

BASE = 'https://lib.jejunu.ac.kr/'
NOT_FOUND = ('데이터가 존재하지 않습니다', '페이지를 찾을 수 없습니다')


def collect(d):
    """주소 → 그 주소를 쓰는 곳 목록."""
    used = collections.defaultdict(list)
    for kind in ('services', 'resources', 'directory'):
        for r in d[kind]:
            used[r['source']].append(f'{r["id"]}.source')
            for f in r.get('facts') or []:
                used[f['source']].append(f'{r["id"]}.facts')
            for m in r.get('materials') or []:
                used[m['url']].append(f'{r["id"]}.materials')
    for n in d.get('notices') or []:
        for key in ('link', 'source'):
            used[n[key]].append(f'notice {n["id"]}.{key}')
    return used


def classify_page(requested, final, title, text):
    if any(s in text for s in NOT_FOUND):
        return '실패', '오류 문구'
    if '#/login' in final and '#/login' not in requested:
        return '경고', '로그인 화면으로 전환'
    if final.rstrip('/') in (BASE.rstrip('/'), BASE + '#') or final.endswith('#/'):
        if requested.rstrip('/') not in (BASE.rstrip('/'), BASE + '#/'):
            return '실패', '홈으로 이동'
    req_path = requested.split('#', 1)[-1].split('?')[0].rstrip('/')
    fin_path = final.split('#', 1)[-1].split('?')[0].rstrip('/')
    if fin_path != req_path:
        if fin_path.startswith(req_path + '/'):
            return '정상', '기본 탭으로 이동'  # 예: #/service/facility → #/service/facility/all
        return '경고', '다른 주소로 이동'
    if ' | ' not in (title or ''):
        return '경고', '페이지 제목을 확인하지 못함(내용 확인 불가)'  # 공식 페이지 제목은 "이름 | 제주대학교 중앙도서관"
    return '정상', ''


def check_page(context, url):
    page = context.new_page()  # 주소마다 새 문서로 연다(같은 문서 안 해시 이동은 제목·상태가 남는다)
    try:
        page.goto(url, timeout=40000)
        try:  # 본문이 채워질 때까지 기다린다(빈 화면을 정상으로 치지 않게)
            page.wait_for_function('document.body && document.body.innerText.trim().length > 50', timeout=10000)
        except Exception:  # noqa: BLE001
            pass
        page.wait_for_timeout(1500)
        text = page.evaluate('document.body ? document.body.innerText : ""')
        title = page.title()
        state, why = classify_page(url, page.url, title, text)
        return state, why, page.url, title
    except Exception as e:  # noqa: BLE001
        return '실패', f'열기 실패: {str(e).splitlines()[0][:80]}', '', ''
    finally:
        page.close()


def check_file(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'library-guide-link-check', 'Range': 'bytes=0-0'})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return ('정상', '', str(r.status), '') if r.status < 400 else ('실패', f'HTTP {r.status}', str(r.status), '')
    except urllib.error.HTTPError as e:
        return '실패', f'HTTP {e.code}', str(e.code), ''
    except Exception as e:  # noqa: BLE001
        return '실패', f'요청 실패: {str(e)[:80]}', '', ''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--only', default='')
    ap.add_argument('--limit', type=int, default=0)
    ap.add_argument('--out', default=str(ROOT / '.tmp' / 'links-report.md'))
    a = ap.parse_args()
    used = collect(datajs.load(ROOT / 'data.js'))
    urls = sorted(u for u in used if a.only in u)
    if a.limit:
        urls = urls[:a.limit]
    rows = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        context = browser.new_context(locale='ko-KR')
        context.route('**/*', lambda r: r.abort() if r.request.method != 'GET' else r.continue_())
        for i, url in enumerate(urls, 1):
            if url.startswith(BASE) and '#/' in url:
                state, why, final, title = check_page(context, url)
                time.sleep(1.5)
            else:
                state, why, final, title = check_file(url)
                time.sleep(1)
            rows.append((state, url, why, final, title, used[url]))
            print(f'[{i}/{len(urls)}] {state} {url} {why}', flush=True)
        browser.close()
    count = collections.Counter(r[0] for r in rows)
    out = pathlib.Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    lines = [f'# 공식 링크 점검 ({time.strftime("%Y-%m-%d")})', '',
             f'정상 {count["정상"]} · 경고 {count["경고"]} · 실패 {count["실패"]} (주소 {len(rows)}개)', '',
             '| 상태 | 주소 | 이유 | 최종 주소 | 제목 | 쓰는 곳 |', '|---|---|---|---|---|---|']
    for state, url, why, final, title, where in sorted(rows, key=lambda r: ('실패', '경고', '정상').index(r[0])):
        cell = title.replace('|', '\\|')  # 제목의 |가 표 칸을 깨지 않게
        lines.append(f'| {state} | {url} | {why} | {final if final != url else ""} | {cell} | {", ".join(where[:4])}'
                     + (f' 외 {len(where) - 4}' if len(where) > 4 else '') + ' |')
    out.write_text('\n'.join(lines) + '\n', encoding='utf-8', newline='\n')
    print(f'\n정상 {count["정상"]} · 경고 {count["경고"]} · 실패 {count["실패"]} → {out}')


if __name__ == '__main__':
    main()
