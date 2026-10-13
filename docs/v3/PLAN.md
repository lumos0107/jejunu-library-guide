# v3 ① 공개 전 필수 — 구현 계획 (PLAN)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** PRD v1.1의 ①(P1-01~P1-15)을 구현해, 틀린 정보·검색·상세·모바일·접근성 문제를 고친 정적 사이트를 조용히 배포할 수 있는 상태로 만든다.

**Architecture:** 빌드 도구 없는 정적 사이트를 유지한다. 데이터는 `data/*.json`(편집 원본)에서 `tools/build_data.py`가 `data.js`를 만들고, 화면 코드는 일반 스크립트 `js/config.js` → `js/lib.js`(순수 함수, `window.LG`) → `js/app.js`(DOM) 순서로 읽는다. 검증은 외부 패키지 없는 Python 테스트 실행기(`tests/smoke.py`)와 Playwright로 한다.

**Tech Stack:** HTML·CSS·바닐라 JS(일반 `<script defer>`), Python 3.14(도구·테스트), Playwright 1.62(Chromium·WebKit), Node 24(P1-03 일회성 추출만).

**Spec:** [PRD.md](PRD.md) v1.1, [RESEARCH.md](RESEARCH.md), [research/code_map.md](research/code_map.md), [research/official_facts.md](research/official_facts.md), [DECISIONS.md](DECISIONS.md), [REVIEW-2026-10-13-3.md](REVIEW-2026-10-13-3.md)(3차 평가의 R 번호), [REVIEW-2026-10-13-4.md](REVIEW-2026-10-13-4.md)(4차 평가의 S 번호)

## Global Constraints

- 로그인·회원가입·개인정보 수집 없음. 사이트 안 입력은 검색어뿐(PRD 2장 1번).
- 비공식 표시 유지, 공식 사이트로 착각할 표현 금지(2장 2번).
- 확인하지 않은 사실 단정 금지. "무료"·"이용 가능"·만료일 추측 금지(2장 3번).
- 빌드 도구·프레임워크·ES 모듈·fetch 금지. 일반 `<script>`만. file://과 배포 주소에서 검색·필터·상세가 같게 동작(2장 5번).
- 주소(#) 상태·뒤로가기는 ②부터. ①에서는 만들지 않는다(D15).
- 편집 원본은 `data/*.json`. `data.js`는 생성물이며 직접 고치지 않는다(2장 6번).
- 기존 자료 98개·메뉴 89개 ID 유실 금지. 기준 목록 `tests/fixtures/v2-ids.json`(2장 7번, M1).
- `_비공개/`는 커밋 금지(2장 8번).
- push 전 검사 순서: 작업 트리 깨끗함(`git status --porcelain`이 비어 있음) → 생성 → `git diff --exit-code data.js` → 데이터 검사 → Playwright → `_비공개/` 제외 확인(2장 9번, K17, D16).
- 로컬 자동 검사는 file://과 `http://127.0.0.1` 서버로 한다. https는 배포 주소에서 검사한다(D16).
- 사실 하나에 출처 하나: 고치는 변동 사실(시간·요금·대상·위치·인증)은 `facts`에 출처·확인일과 함께 넣는다. 확인하지 못한 것은 쓰지 않거나 "확인하지 못함"으로 쓴다. `audience` 값은 바꾸지 않는다(RESEARCH 5장).
- 도구가 저장소 파일을 쓸 때는 `newline='\n'`(LF)으로 쓴다. 이 저장소는 `core.autocrlf=true`이고 작업 폴더의 data.js는 LF다. 파일 비교는 텍스트(줄바꿈 정규화)로 한다.
- 데이터·주소 값을 믿지 않는다. 화면 삽입은 이스케이프, 링크는 https만(2장 10번).
- 공식 사이트 기준 주소: `https://lib.jejunu.ac.kr/`.
- 날짜는 `YYYY-MM-DD` 문자열, 기기 로컬 날짜 기준, 시작·종료일 당일 포함. `new Date('YYYY-MM-DD')`·`toISOString()`으로 오늘 날짜를 만들지 않는다(5장 날짜 규칙).
- 검색어 "무료"·"무제한"은 생성 키워드로만 일치하며 ①에서는 0건(K10).
- 커밋 메시지는 한국어, 끝에 `Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>`.

## Review Focus

1. **기호·공백만 입력** (`!!!`, `   `, `“”`): 결과 234건이 아니라 "검색어를 입력하세요" 안내가 보여야 한다 → Task 6 `t_symbol_only_query`.
2. **필터가 걸린 채 다른 범위로 이동했다가 돌아옴**: 숨은 필터가 남아 결과가 줄면 안 된다 → Task 9 `t_scope_change_resets_hidden_filters`.
3. **데이터에 악성 문자열**(id에 따옴표, 이름에 `<img onerror>`, `javascript:` 링크): 실행되거나 링크로 열리면 안 된다 → Task 4 `t_malicious_data_is_inert`.
4. **공지 기간 경계**(첫날·마지막 날·다음 날): 첫날과 마지막 날은 보이고 다음 날은 숨겨진다 → Task 7 `t_notice_boundaries`.
5. **모바일에서 긴 상세**(그룹스터디룸·NICE·JSTOR, 390×844): 스크롤하기 전에 대화상자의 보이는 영역 안에 공식 버튼과 대상·비용·인증 요약(목록형이면 찾는 방법)이 보여야 하고, 예외는 그 바로 아래에 있어야 한다 → Task 8 `t_detail_above_fold_mobile`, `t_detail_order_exceptions_below_summary`.

---

## 파일 구조 (① 완료 후)

| 경로 | 역할 | 만드는 작업 |
|---|---|---|
| `index.html` | 화면 골격. 스크립트 로딩 순서 | 수정: Task 2·4·7·9·10·11·12·13 |
| `styles.css` | 스타일(읽기 좋게 풀고 중복 정리) | Task 2, 수정 8~13 |
| `data.js` | **생성물** (`window.LIBRARY_GUIDE`) | Task 3부터 생성 |
| `js/config.js` | 사이트 설정(배포 주소·제보 폼) | Task 13 |
| `js/lib.js` | 순수 함수(`window.LG`): 이스케이프·URL·정규화·검색·날짜·공지 | Task 4, 확장 6·7·13 |
| `js/app.js` | DOM: 렌더·이벤트·상세 | Task 2(옮김), 수정 3~13 |
| `favicon.svg` | 파비콘 | Task 13 |
| `data/meta.json` | `checkedAt`, `metadata` | Task 3 |
| `data/categories.json`, `services.json`, `resources.json`, `directory.json` | v2 레코드(구조 유지) | Task 3, 수정 5·8 |
| `data/related.json`, `book-cases.json` | 코드 안에 있던 내용 데이터 | Task 3, 수정 5 |
| `data/notices.json` | 공지 | Task 3(빈 배열), 7 |
| `data/common-text.json` | 검색에서 뺄 공통 문장 | Task 3 |
| `data/normalize-cases.json` | 정규화 테스트 벡터(JS·Python 공용) | Task 6 |
| `tools/datajs.py` | data.js 읽기·쓰기 | Task 1 |
| `tools/make_v2_ids.py` | v2 ID 기준 목록 생성(1회) | Task 1 |
| `tools/format_css.py` | CSS 풀기(1회) | Task 2 |
| `tools/css_snapshot.py` | 계산된 스타일 스냅숏 비교 | Task 2 |
| `tools/extract_v2.py` | v2 → data/*.json 추출·검증(1회) | Task 3 |
| `tools/build_data.py` | data/*.json → data.js, `--check` | Task 3 |
| `tools/normalize.py` | Python 정규화(검사용) | Task 6 |
| `tools/perf.py` | 첫 화면·검색 시간과 data.js 크기 측정(PRD 7장, 기록용) | Task 6 |
| `tools/gate.py` | push 전 검사 순서 실행 | Task 13 |
| `tools/deploy_check.py` | 배포본 = HEAD 확인 후 배포 주소 테스트 | Task 13 |
| `tools/v2-base.txt` | 추출 기준 커밋 | Task 3 |
| `tests/harness.py`, `helpers.py`, `smoke.py` | 테스트 실행기·행동 도우미(M2) | Task 1 |
| `tests/test_*.py` | 테스트 모음 | Task 1~13 |
| `tests/check_data.py` | 데이터 검사(stage 1) | Task 4, 확장 5·6·7 |
| `tests/fixtures/v2-ids.json` | v2 ID 234개 | Task 1 |
| `docs/DEV.md` | 로딩 순서·전역·명령·배포 방법 | Task 2, 갱신 13 |
| `docs/v3/QA-1.md` | ① 검증 기록(성능·크기·교차 리뷰·실제 기기 체크리스트) | Task 14 |

## 실행 명령 요약

```bash
python tools/build_data.py            # data/*.json → data.js
python tools/build_data.py --check    # 생성물 일치 확인(쓰지 않음)
python tests/check_data.py --stage 1  # 데이터 검사
python tests/smoke.py --stage 1 --browsers chromium,webkit --modes file,http
python tools/gate.py                  # push 전 전체 검사(Task 13부터)
python tools/perf.py                  # 성능·크기 측정(Task 6부터, 기록용)
```

---

## To-do 요약

- [ ] Task 1: 회귀 테스트 기반 (P1-01)
- [ ] Task 2: 코드 포맷 정리와 기준 커밋 (P1-02)
- [ ] Task 3: JSON 추출과 data.js 생성 (P1-03)
- [ ] Task 4: 데이터 검사와 화면 안전 (P1-04)
- [ ] Task 5: 공식 사실로 콘텐츠 수정·반납 안내 추가 (P1-05, P1-07 데이터, P1-13)
- [ ] Task 6: 검색 기본 정비 (P1-08)
- [ ] Task 7: 최소 공지 기능 (P1-06)
- [ ] Task 8: 상세의 마지막 한 걸음과 조건 표시 (P1-07 화면, P1-11)
- [ ] Task 9: 필터·검색어 유지 (P1-09)
- [ ] Task 10: 상단 검색 (P1-10)
- [ ] Task 11: 접근성 결함 수정 (P1-12)
- [ ] Task 12: 화면 용어 정리 (P1-15)
- [ ] Task 13: 배포 준비와 push 게이트 (P1-14)
- [ ] Task 14: 최종 검증·코드 교차 리뷰·문서·push

---

### Task 1: 회귀 테스트 기반 (P1-01)

**Files:**
- Create: `tools/datajs.py`, `tools/make_v2_ids.py`, `tests/harness.py`, `tests/helpers.py`, `tests/smoke.py`, `tests/test_regression.py`, `tests/fixtures/v2-ids.json`
- Modify: `.gitignore` (`.tmp/` 추가)

**Interfaces:**
- Produces:
  - `datajs.load(path='data.js') -> dict`, `datajs.dump(obj) -> str`, `datajs.PREFIX = 'window.LIBRARY_GUIDE = '`
  - `harness.test(stage=1, viewport='desktop', motion='reduce', clock=True)` 데코레이터, `harness.check(cond, msg)`, `harness.REGISTRY`
  - 실행기 기본 환경(S13): 시계 2026-10-15 10:00 Asia/Seoul 고정(PRD 부록 A 기준일. 날짜 테스트는 `page.clock`으로 다시 정함), 동작 줄이기(`reduced_motion='reduce'`. 기본 동작 검사는 `motion='no-preference'`로 따로)
  - `helpers.Site(page, base, errors)`: `open(hash_='')`, `search(q)`, `count()`, `result_ids()`, `scope(s)`, `category_tab(cid)`, `category_card(cid)`, `select(sel_id, value)`, `load_more()`, `card_count()`, `open_detail(rid)`, `open_any(rid)`, `detail_text()`, `official_href()`, `close_detail()`, `dialog_open()`, `book_case(key)`, `console_errors()`, `data()`, `query_value()`, `close_with_button()`, `open_from_hero(rid)`, `material_links()`, `category_card_count()`, `resource_filters_visible()`
  - `helpers.VIEWPORTS = {'desktop': {'width':1440,'height':900}, 'mobile': {'width':390,'height':844}}`
  - `smoke.py` CLI: `--stage N --browsers a,b --modes file,http --base URL -k 이름`

- [ ] **Step 1: WebKit 설치와 임시 폴더 제외**

```bash
python -m playwright install webkit
printf '\n# 테스트 임시 산출물·파이썬 캐시(없으면 게이트의 작업 트리 검사가 늘 실패한다)\n.tmp/\n__pycache__/\n*.pyc\n' >> .gitignore
```

- [ ] **Step 2: data.js 읽기·쓰기 도구 작성** — `tools/datajs.py`

```python
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
```

- [ ] **Step 3: 형식 왕복 확인**

Run: `python -c "import sys;sys.path.insert(0,'tools');import datajs,pathlib;t=pathlib.Path('data.js').read_text(encoding='utf-8');print(datajs.dump(datajs.load())==t)"`
Expected: `True` (False면 PREFIX·들여쓰기를 data.js 첫 줄과 맞춘다)

줄바꿈: 비교는 `read_text`(줄바꿈 정규화)로 하고, 쓸 때는 `newline='\n'`으로 LF를 쓴다(Global Constraints).

- [ ] **Step 4: v2 ID 기준 목록 생성 도구** — `tools/make_v2_ids.py`

```python
"""v2 data.js에서 ID 기준 목록(tests/fixtures/v2-ids.json)을 만든다. 1회만 실행."""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import datajs  # noqa: E402

data = datajs.load(ROOT / 'data.js')
ids = {k: [r['id'] for r in data[k]] for k in ('services', 'resources', 'directory')}
out = ROOT / 'tests' / 'fixtures' / 'v2-ids.json'
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(ids, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
print(out, {k: len(v) for k, v in ids.items()})
```

Run: `python tools/make_v2_ids.py`
Expected: `{'services': 47, 'resources': 98, 'directory': 89}`

- [ ] **Step 5: 테스트 등록 도구** — `tests/harness.py`

```python
"""외부 패키지 없는 테스트 등록·판정 도구."""
REGISTRY = []


class Fail(AssertionError):
    pass


def test(stage=1, viewport='desktop', motion='reduce', clock=True):
    # clock=False: 시계를 고정하지 않는다. Playwright의 가짜 시계는 performance.mark도 아무 일 안 하게 바꾼다
    def deco(fn):
        REGISTRY.append({'fn': fn, 'stage': stage, 'viewport': viewport, 'motion': motion, 'clock': clock,
                         'name': f'{fn.__module__}::{fn.__name__}'})
        return fn
    return deco


def check(cond, msg):
    if not cond:
        raise Fail(msg)
```

- [ ] **Step 6: 행동 단위 도우미** — `tests/helpers.py` (M2: ②에서는 이 파일만 바꾼다)

```python
"""화면을 '행동' 단위로 다루는 도우미. 테스트는 선택자를 직접 쓰지 않고 이 클래스를 쓴다."""
import re

VIEWPORTS = {'desktop': {'width': 1440, 'height': 900}, 'mobile': {'width': 390, 'height': 844}}


class Site:
    def __init__(self, page, base, errors):
        self.page, self.base, self.errors = page, base, errors

    def open(self, hash_=''):
        self.page.goto(self.base + 'index.html' + hash_)
        self.page.wait_for_selector('#service-grid .service-card')

    def search(self, q):
        self.page.fill('#search-input', q)
        self.page.press('#search-input', 'Enter')
        self.page.wait_for_timeout(120)

    def query_value(self):
        return self.page.input_value('#search-input')

    def count(self):
        m = re.search(r'(\d+)개 결과', self.page.inner_text('#result-count'))
        return int(m.group(1)) if m else None

    def result_ids(self):
        return self.page.eval_on_selector_all('#service-grid [data-open]', 'els => els.map(e => e.dataset.open)')

    def card_count(self):
        return self.page.locator('#service-grid .service-card').count()

    def scope(self, s):
        self.page.click(f'#scope-tabs [data-scope="{s}"]')
        self.page.wait_for_timeout(80)

    def category_tab(self, cid):
        self.page.click(f'#category-tabs [data-category="{cid}"]')
        self.page.wait_for_timeout(80)

    def category_card(self, cid):
        self.page.click(f'#category-grid [data-category="{cid}"]')
        self.page.wait_for_timeout(150)

    def select(self, sel_id, value):
        self.page.select_option(f'#{sel_id}', value)
        self.page.wait_for_timeout(80)

    def load_more(self):
        self.page.click('#load-more')
        self.page.wait_for_timeout(80)

    def open_detail(self, rid):
        self.page.locator(f'#service-grid [data-open="{rid}"]').first.click()
        self.page.wait_for_selector('#detail-dialog[open]')

    def open_any(self, rid):
        """목록에 없어도 상세를 연다(앱의 클릭 위임을 그대로 사용)."""
        self.page.evaluate("""rid => { const b = document.createElement('button');
            b.dataset.open = rid; b.hidden = true; document.body.append(b); b.click(); b.remove(); }""", rid)
        self.page.wait_for_selector('#detail-dialog[open]')

    def detail_text(self):
        return self.page.inner_text('#detail-content')

    def official_href(self):
        return self.page.get_attribute('#detail-content a.primary', 'href')

    def close_detail(self):
        self.page.keyboard.press('Escape')
        self.page.wait_for_timeout(120)

    def close_with_button(self):
        self.page.click('#close-dialog')
        self.page.wait_for_timeout(120)

    def dialog_open(self):
        return self.page.locator('#detail-dialog[open]').count() == 1

    def book_case(self, key):
        self.page.click(f'[data-book="{key}"]')
        self.page.wait_for_timeout(80)

    def open_from_hero(self, rid):
        self.page.click(f'.hero-aside [data-open="{rid}"]')
        self.page.wait_for_selector('#detail-dialog[open]')

    def material_links(self):
        return self.page.eval_on_selector_all('#detail-content .material-list a', 'els => els.map(e => e.getAttribute("href"))')

    def category_card_count(self):
        return self.page.locator('#category-grid .category-card').count()

    def resource_filters_visible(self):
        return self.page.locator('#resource-filters').is_visible()

    def console_errors(self):
        return [e for e in self.errors if 'favicon' not in e]

    def data(self):
        return self.page.evaluate('window.LIBRARY_GUIDE')
```

- [ ] **Step 7: 실행기** — `tests/smoke.py`

```python
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
```

- [ ] **Step 8: 회귀 테스트 작성** — `tests/test_regression.py`

`q*` = 유지할 약속(수치는 데이터에서 계산), `d*` = v2 동작 고정값(해당 작업에서 기대값을 바꾼다). 지난 Playwright 확인 35개 항목과의 대응은 RESEARCH 6장 표다. 표의 모든 항목이 q01~q12나 실행기의 오류 검사(Step 7)에 들어 있어야 한다.

```python
"""① 회귀 테스트. q* = 유지할 약속, d* = v2 동작 고정값(표시된 작업에서 기대값을 바꾼다)."""
import json
import pathlib

from harness import check, test

FIX = pathlib.Path(__file__).resolve().parent / 'fixtures'
KINDS = ('services', 'resources', 'directory')


def total(d):
    return sum(len(d[k]) for k in KINDS)


@test()
def q01_ids_preserved(site):
    site.open()
    d = site.data()
    ids = [r['id'] for k in KINDS for r in d[k]]
    check(len(ids) == len(set(ids)), 'id 중복')
    fixture = json.loads((FIX / 'v2-ids.json').read_text(encoding='utf-8'))
    have = set(ids)
    missing = [i for k in fixture for i in fixture[k] if i not in have]
    check(not missing, f'v2 id 누락: {missing[:5]}')


@test()
def q02_required_fields_https_console(site):
    site.open()
    d = site.data()
    for k in KINDS:
        for r in d[k]:
            for f in ('id', 'name', 'description', 'source', 'recordKind'):
                check(r.get(f), f'{r.get("id")}: {f} 없음')
            check(r['steps'], f'{r["id"]}: steps 없음')
            check(r['source'].startswith('https://'), f'{r["id"]}: source가 https 아님')
    check(not site.console_errors(), f'콘솔 오류: {site.console_errors()[:3]}')


@test()
def q03_initial_list_and_load_more(site):
    site.open()
    d = site.data()
    check(site.count() == total(d), f'첫 화면 {site.count()} != {total(d)}')
    check(site.card_count() == 12, '처음 카드 12개')
    site.load_more()
    check(site.card_count() == 24, '더 보기 뒤 24개')
    check(site.page.inner_text('#checked-at').strip() != '', '확인일 표시 없음')
    check(site.category_card_count() == len(d['categories']), f'상황 카드 {site.category_card_count()}')


@test()
def q04_representative_searches(site):
    site.open()
    cases = [('무선인터넷', 2, {'wifi', 'menu-046'}), ('SDI', 3, {'sdi'}), ('외국어 교정', 4, {'editage', 'enago'}),
             ('Naxos', 2, {'culture', 'er-055'}), ('CAS BioFinder', 1, {'er-096'}), ('크레마클럽', 2, {'ebook', 'er-098'})]
    for q, n, must in cases:
        site.search(q)
        ids = set(site.result_ids())
        check(site.count() == n, f'{q}: {site.count()}건(기대 {n})')
        check(must <= ids, f'{q}: {must - ids} 없음')


@test()
def q05_resource_and_menu_filters(site):
    site.open()
    site.scope('resource')
    check(site.count() == 98, f'전자정보원 {site.count()}')
    check(site.resource_filters_visible(), '전자정보원 필터 영역이 안 보임')
    site.select('resource-access', '공개자료 안내')
    check(site.count() == 6, f'공개자료 {site.count()}')
    site.select('resource-access', '시범서비스')
    check(site.count() == 4, f'시범서비스 {site.count()}')
    site.select('resource-access', 'all')
    site.select('resource-subject', '통계·기업')
    check(site.count() == 5, f'통계·기업 {site.count()}')
    site.select('resource-subject', 'all')
    site.scope('menu')
    check(site.count() == 89, f'메뉴 {site.count()}')
    site.select('menu-group', 'My Library')
    check(site.count() == 17, f'My Library {site.count()}')


@test()
def q06_statista_detail(site):
    site.open()
    site.scope('resource')
    site.search('Statista')
    ids = site.result_ids()
    check(ids, 'Statista 결과 없음')
    site.open_detail(ids[0])
    check('Statista' in site.detail_text(), '상세에 Statista 없음')
    check(len(site.material_links()) >= 1, '매뉴얼 링크 없음')
    check(site.official_href() == 'https://lib.jejunu.ac.kr/#/search/er', f'공식 링크 {site.official_href()}')
    site.close_detail()
    check(not site.dialog_open(), 'Escape로 닫히지 않음')


@test()
def q07_undergrad_filter(site):
    site.open()
    d = site.data()
    grad = sum(1 for s in d['services'] if s.get('audience') == 'grad')
    grad_all = sum(1 for k in KINDS for r in d[k] if r.get('audience') == 'grad')  # 메뉴에도 대학원 대상이 있다(S20)
    site.scope('guide')
    check(site.count() == len(d['services']), f'가이드 {site.count()}')
    site.select('audience', 'undergrad')
    check(site.count() == len(d['services']) - grad, f'가이드+학부생 {site.count()}')
    site.scope('all')
    check(site.count() == total(d) - grad_all, f'전체+학부생 {site.count()}')


@test()
def q08_space_category(site):
    site.open()
    d = site.data()
    site.category_card('space')
    space = [s['id'] for s in d['services'] if s['category'] == 'space']
    check(site.count() == len(space), f'공부 공간 {site.count()} != {len(space)}')
    site.select('audience', 'undergrad')
    expect = {s['id'] for s in d['services'] if s['category'] == 'space' and s.get('audience') != 'grad'}
    check(set(site.result_ids()) == expect, f'공부 공간+학부생 {site.result_ids()}')


@test()
def q09_empty_and_reset(site):
    site.open()
    d = site.data()
    site.search('zzzz없는검색어qq')
    check(site.page.locator('#empty').is_visible(), '빈 결과 화면 없음')
    site.page.click('#empty-reset')
    site.page.wait_for_timeout(100)
    check(site.count() == total(d), '초기화 뒤 전체로 돌아오지 않음')


@test()
def q10_book_case_not_owned(site):
    site.open()
    site.book_case('not-owned')
    ids = site.page.eval_on_selector_all('#book-result [data-open]', 'els => els.map(e => e.dataset.open)')
    check(ids == ['wish', 'dds'], f'책 상황 결과 {ids}')
    check(site.page.get_attribute('[data-book="not-owned"]', 'aria-pressed') == 'true', 'aria-pressed')


@test(viewport='mobile')
def q11_mobile_basics(site):
    site.open()
    sw = site.page.evaluate('document.documentElement.scrollWidth')
    check(sw <= 390, f'가로 넘침 {sw}')
    site.scope('resource')
    site.search('JSTOR')
    check(site.count() == 1, f'JSTOR {site.count()}')
    site.open_detail(site.result_ids()[0])
    box = site.page.locator('#detail-dialog').bounding_box()
    check(box['x'] >= 0 and box['x'] + box['width'] <= 390, f'상세 폭 {box}')
    site.close_detail()
    check(not site.dialog_open(), 'Escape로 닫히지 않음')


@test()
def q12_hero_button_and_close(site):
    site.open()
    site.open_from_hero('maker')
    check('메이커' in site.detail_text(), '히어로 버튼으로 메이커 상세가 열리지 않음')
    site.close_with_button()
    check(not site.dialog_open(), '닫기 버튼으로 닫히지 않음')


# ---- v2 동작 고정값: 표시된 작업에서 기대값을 바꾼다 ----

@test()
def d01_symbol_only_query(site):  # → Task 6
    site.open()
    d = site.data()
    site.search('!!!')
    check(site.count() == total(d), 'v2: 기호만 입력해도 전체가 나옴')


@test()
def d02_free_word(site):  # → Task 5에서 삭제
    site.open()
    site.search('무료')
    check(site.count() == 89, f'v2: 무료 {site.count()}건')


@test()
def d03_remote_noise(site):  # → Task 6
    site.open()
    site.search('교외접속')
    check(site.count() >= 90, f'v2: 교외접속 {site.count()}건')


@test()
def d04_quote_and_joined_words(site):  # → Task 6
    site.open()
    site.search('“통계”')
    check(site.count() == 0, 'v2: 둥근 따옴표 검색 0건')
    site.search('영어논문')
    check(site.count() == 0, 'v2: 영어논문 0건')


@test()
def d05_book_return_missing(site):  # → Task 5
    site.open()
    site.search('책 반납')
    check('book-return' not in site.result_ids(), 'v2: 반납 안내 없음')


@test()
def d06_category_tab_clears_query(site):  # → Task 9
    site.open()
    site.search('통계')
    site.category_tab('assignment')
    check(site.query_value() == '', 'v2: 상황 탭이 검색어를 지움')


@test()
def d07_official_button_at_end(site):  # → Task 8
    # 1440×900에서는 버튼이 이미 화면 안(y≈861)이라 좌표로는 결함이 재현되지 않는다. 결함은 '맨 끝 배치'다(S20)
    site.open()
    site.open_any('stats')
    at_end = site.page.evaluate("document.querySelector('#detail-content').lastElementChild.querySelector('a.primary') !== null")
    check(at_end, 'v2: 공식 버튼이 상세의 맨 끝 블록에 있음')


@test()
def d08_a11y_structure(site):  # → Task 11
    site.open()
    check(site.page.locator('#category-grid button h3').count() == 6, 'v2: button 안 h3')
    check(site.page.get_attribute('#scope-tabs', 'role') is None, 'v2: 탭 묶음 role 없음')


@test(viewport='mobile')
def d09_mobile_search_far(site):  # → Task 10
    site.open()
    top = site.page.locator('#search-input').bounding_box()['y']
    check(top > 844, f'v2: 검색창 {top}px')


@test()
def d10_vague_badge(site):  # → Task 8
    site.open()
    check(site.page.locator('.badge', has_text='세부 조건 확인').count() > 0, "v2: '세부 조건 확인' 배지")
```

- [ ] **Step 9: 실행해 전부 통과 확인 (v2 그대로)**

Run: `python tests/smoke.py --stage 1 --browsers chromium,webkit --modes file,http`
Expected: 모든 줄 `PASS`, 실패 0(마지막 줄의 두 숫자가 같음) (22개 × 브라우저 2 × 모드 2 = 88줄). 실패하면 사이트가 아니라 테스트의 선택자·기대값을 v2 실측에 맞춘다.

- [ ] **Step 10: 커밋**

```bash
git add .gitignore tools/datajs.py tools/make_v2_ids.py tests/
git commit -m "v3①: 회귀 테스트 기반 추가 (P1-01)" -m "행동 단위 도우미, 외부 의존성 없는 실행기, 유지할 약속 12개(지난 35개 항목 포함)와 v2 고정값 10개, 모든 테스트 끝의 콘솔 오류 검사, v2 ID 기준 목록" -m "Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
```

---

### Task 2: 코드 포맷 정리와 기준 커밋 (P1-02)

**Files:**
- Create: `tools/format_css.py`, `tools/css_snapshot.py`, `js/app.js`(app.js를 옮겨 풀어 씀), `docs/DEV.md`
- Modify: `styles.css`(풀고 중복 정리), `index.html`(스크립트 경로)
- Delete: `app.js`(→ `js/app.js`로 이동, `git mv`)

**Interfaces:**
- Consumes: Task 1의 `tests/smoke.py`
- Produces: `js/app.js`(동작은 v2와 같음). 이 작업의 커밋이 **JSON 추출 기준 커밋**이 된다(Task 3에서 `tools/v2-base.txt`에 기록).

- [ ] **Step 1: 계산된 스타일 스냅숏 도구** — `tools/css_snapshot.py`

```python
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
```

- [ ] **Step 2: 정리 전 기준 스냅숏 저장**

Run: `mkdir -p .tmp && python tools/css_snapshot.py . .tmp/css-before.json`
Expected: `.tmp/css-before.json` 생성

- [ ] **Step 3: CSS 풀기 도구** — `tools/format_css.py`

```python
"""CSS를 규칙·값 변경 없이 한 줄에 선언 하나로 푼다. 사용: python tools/format_css.py styles.css"""
import pathlib
import sys


def format_css(src):
    out, cur, depth, paren, i = [], '', 0, 0, 0
    while i < len(src):
        if src.startswith('/*', i):
            j = src.index('*/', i) + 2
            if cur.strip():
                out.append('  ' * depth + cur.strip())
                cur = ''
            out.append('  ' * depth + src[i:j].strip())
            i = j
            continue
        ch = src[i]
        if ch in '"\'':
            j = i + 1
            while src[j] != ch:
                j += 2 if src[j] == '\\' else 1
            cur += src[i:j + 1]
            i = j + 1
            continue
        if ch == '(':
            paren += 1
        elif ch == ')':
            paren -= 1
        if ch == '{' and not paren:
            out.append('  ' * depth + ' '.join(cur.split()) + ' {')
            cur, depth = '', depth + 1
        elif ch == ';' and not paren:
            if cur.strip():
                out.append('  ' * depth + ' '.join(cur.split()) + ';')
            cur = ''
        elif ch == '}' and not paren:
            if cur.strip():
                out.append('  ' * depth + ' '.join(cur.split()) + ';')
            cur, depth = '', depth - 1
            out.append('  ' * depth + '}')
        else:
            cur += ch
        i += 1
    return '\n'.join(line.rstrip() for line in out) + '\n'


if __name__ == '__main__':
    p = pathlib.Path(sys.argv[1])
    p.write_text(format_css(p.read_text(encoding='utf-8')), encoding='utf-8', newline='\n')
```

Run: `python tools/format_css.py styles.css && python tools/css_snapshot.py . .tmp/css-after.json && python tools/css_snapshot.py --compare .tmp/css-before.json .tmp/css-after.json`
Expected: `차이 없음`

- [ ] **Step 4: 중복 규칙 정리**

RESEARCH 7장·code_map 4장의 중복 6곳(`.result-heading`, `.result-heading p`, `.service-card h3`, `.coverage`, `.kind-note`, `button`)을 하나씩 처리한다. 먼저 중복마다 앞 블록의 속성을 둘로 나눠 `.tmp/css-dedupe.txt`에 한 줄씩 적는다(R20): **덮어씀**(나중 블록에 같은 속성이 있어 이미 지는 값 → 지운다), **추가**(앞 블록에만 있는 값 → 나중 블록으로 옮긴다). 형식: `선택자 — 덮어씀: 속성들 / 추가: 속성들`. 규칙: **나중 블록의 선언이 이기므로**, 추가 속성을 나중 블록으로 옮기고 앞 블록을 지운다. 한 곳을 고칠 때마다 아래를 실행하고, `차이 없음`이 아니면 그 한 곳만 되돌린 뒤 `/* 중복 유지: 미디어쿼리 순서 때문 */` 주석을 단다.

Run: `python tools/css_snapshot.py . .tmp/css-after.json && python tools/css_snapshot.py --compare .tmp/css-before.json .tmp/css-after.json`
Expected: `차이 없음`

- [ ] **Step 5: app.js를 js/app.js로 옮겨 풀어 쓰기** (동작 변경 없음)

```bash
mkdir -p js && git mv app.js js/app.js
```

`js/app.js` 전체를 아래로 바꾼다(v2 로직을 그대로 풀어 쓴 것).

```js
// 도서관의 쓸모 — 화면 코드
// 로딩 순서(index.html, 모두 defer): data.js → js/app.js
(() => {
  'use strict';

  const { categories, services, resources = [], directory = [], checkedAt } = window.LIBRARY_GUIDE;
  const records = [...services, ...resources, ...directory];

  const $ = selector => document.querySelector(selector);
  const escape = value => String(value ?? '').replace(/[&<>"']/g, c => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  }[c]));
  const byId = id => records.find(s => s.id === id);
  const categoryName = id => categories.find(c => c.id === id)?.name || id;
  const kindName = kind => ({ guide: '이용 가이드', resource: '전자정보원', menu: '공식 메뉴 위치' }[kind] || '이용 가이드');
  const normalized = value => String(value ?? '').toLocaleLowerCase().normalize('NFKC')
    .replace(/[\s’'·.,!?()\[\]{}_:;/-]/g, '');

  const DEFAULT_STATE = { scope: 'all', category: 'all', query: '', audience: 'all', subject: 'all',
    sourceType: 'all', access: 'all', menuGroup: 'all', limit: 12 };
  const state = { ...DEFAULT_STATE };
  let currentMatches = [];

  const notes = {
    all: '이용 가이드 ' + services.length + '개 · 전자정보원 ' + resources.length + '개 · 공식 메뉴 위치 ' + directory.length
      + '개를 함께 검색해요. 같은 서비스가 가이드와 공식 메뉴에 각각 표시될 수 있어요.',
    guide: '공개 상세 안내를 학생의 질문으로 풀어쓴 가이드예요. 실제 서비스의 이용 대상·비용·인증 조건은 공식 안내를 다시 확인해주세요.',
    resource: '전자정보원 원목록 97개에서 중복 1개를 합친 96개 + 전자책 목록의 추가 2개예요. 공개자료·시범서비스·나머지 목록 등재 항목은 이용조건이 다릅니다.',
    menu: '공식 상위 6개 메뉴의 하위 메뉴 89개예요. 메뉴 위치·링크를 확인했지만 모든 하위 본문이나 로그인 후 기능을 검증한 것은 아닙니다.'
  };

  function card(s) {
    const resource = s.recordKind === 'resource';
    const menu = s.recordKind === 'menu';
    const badges = resource
      ? '<span class="badge">' + escape(s.subject) + '</span><span class="badge '
        + (s.accessType === '시범서비스' ? 'trial' : s.accessType === '공개자료 안내' ? 'open' : '') + '">'
        + escape(s.accessType) + '</span>'
      : '<span class="badge">' + escape(s.channel) + '</span><span class="badge' + (s.audience === 'grad' ? ' target' : '')
        + '">' + (s.audience === 'grad' ? '대학원 대상' : '세부 조건 확인') + '</span>';
    return '<article class="service-card"><div class="record-kind"><span>' + kindName(s.recordKind) + '</span><span>'
      + escape(resource ? s.sourceType : menu ? s.menuGroup : categoryName(s.category)) + '</span></div><h3>'
      + escape(s.name) + '</h3>'
      + (!menu ? '<p class="service-question">' + escape(resource ? s.subject + ' 분야에서 활용하기' : s.question) + '</p>' : '')
      + '<p class="service-description' + (menu ? ' official-path' : '') + '">' + escape(s.description) + '</p>'
      + '<div class="badges">' + badges + '</div><button type="button" data-open="' + s.id + '" aria-label="'
      + escape(s.name) + ' ' + kindName(s.recordKind) + ' 보기">'
      + (resource ? '설명·매뉴얼 보기' : menu ? '공식 메뉴 위치 보기' : '이용 방법 보기')
      + '<span aria-hidden="true">↗</span></button></article>';
  }

  function matchesFilters(s) {
    return (state.scope === 'all' || s.recordKind === state.scope)
      && (state.category === 'all' || s.category === state.category)
      && (state.audience !== 'undergrad' || s.audience !== 'grad')
      && (state.scope !== 'resource' || ((state.subject === 'all' || s.subject === state.subject)
        && (state.sourceType === 'all' || s.sourceType === state.sourceType)
        && (state.access === 'all' || s.accessType === state.access)))
      && (state.scope !== 'menu' || state.menuGroup === 'all' || s.menuGroup === state.menuGroup);
  }

  function render() {
    const terms = state.query.trim().split(/\s+/).filter(Boolean).map(normalized);
    currentMatches = records.filter(s => matchesFilters(s) && terms.every(term => normalized([
      s.name, s.question, s.description, s.officialDescription, s.keywords, s.caution, s.subject, s.sourceType,
      s.menuGroup, s.menuSubgroup, ...(s.steps || [])
    ].join(' ')).includes(term)));

    $('#service-grid').innerHTML = currentMatches.slice(0, state.limit).map(card).join('');
    $('#empty').hidden = currentMatches.length !== 0;
    $('#load-more').hidden = currentMatches.length <= state.limit;
    $('#load-more').textContent = '더 보기 · ' + Math.min(state.limit, currentMatches.length) + ' / ' + currentMatches.length;

    const kinds = { guide: 0, resource: 0, menu: 0 };
    currentMatches.forEach(s => kinds[s.recordKind]++);
    $('#result-count').textContent = (state.scope === 'all' ? '전체 검색' : kindName(state.scope)) + ' · '
      + currentMatches.length + '개 결과' + (state.query ? ' · “' + state.query + '”' : '')
      + (state.scope === 'all' ? ' (가이드 ' + kinds.guide + ' · 자료 ' + kinds.resource + ' · 메뉴 ' + kinds.menu + ')' : '');

    $('#scope-note').textContent = notes[state.scope];
    $('#resource-filters').hidden = state.scope !== 'resource';
    $('#menu-filter').hidden = state.scope !== 'menu';
    $('#category-tabs').hidden = state.scope === 'resource' || state.scope === 'menu';
    document.querySelectorAll('button[data-category]').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.category === state.category)));
    document.querySelectorAll('button[data-scope]').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.scope === state.scope)));
  }

  function reset() {
    Object.assign(state, DEFAULT_STATE);
    $('#search-input').value = '';
    ['audience', 'resource-subject', 'resource-type', 'resource-access', 'menu-group'].forEach(id => { $('#' + id).value = 'all'; });
    render();
  }

  function changeScope(scope) {
    state.scope = scope;
    state.category = 'all';
    state.limit = 12;
    render();
  }

  // 첫 그리기
  $('#category-grid').innerHTML = categories.map((c, i) => '<button type="button" class="category-card" data-category="' + c.id
    + '"><span class="category-index"><span>0' + (i + 1) + ' / ' + escape(c.name)
    + '</span><span aria-hidden="true">↗</span></span><h3>' + escape(c.question) + '</h3><p>' + escape(c.desc) + '</p></button>').join('');
  $('#category-tabs').innerHTML = [{ id: 'all', name: '모든 상황' }, ...categories].map(c => '<button type="button" data-category="'
    + c.id + '" aria-pressed="' + (c.id === 'all') + '">' + escape(c.name) + '</button>').join('');
  $('#scope-tabs').innerHTML = [['all', '전체 검색', records.length], ['guide', '이용 가이드', services.length],
    ['resource', '전자정보원', resources.length], ['menu', '공식 메뉴', directory.length]]
    .map(([id, label, count]) => '<button type="button" data-scope="' + id + '" aria-pressed="' + (id === 'all') + '">' + label
      + '<span class="scope-count">' + count + '</span></button>').join('');
  for (const [id, values] of [['resource-subject', [...new Set(resources.map(r => r.subject))]],
    ['resource-type', [...new Set(resources.map(r => r.sourceType))]],
    ['menu-group', [...new Set(directory.map(r => r.menuGroup))]]]) {
    $('#' + id).insertAdjacentHTML('beforeend', values.map(v => '<option value="' + escape(v) + '">' + escape(v) + '</option>').join(''));
  }
  $('#coverage').textContent = services.length + '개 활용 안내 · ' + resources.length + '개 전자정보원 · 공식 메뉴 '
    + directory.length + '개도 검색할 수 있어요';
  $('#checked-at').textContent = checkedAt.replaceAll('-', '.');

  const relatedMap = {
    loan: ['night', 'wish'], wish: ['dds', 'campus'], campus: ['dds', 'wish'], missing: ['loan', 'storage'],
    storage: ['priority'], priority: ['night'], night: ['loan', 'mobile'], seat: ['group', 'locker', 'hours'],
    group: ['maker', 'seat'], maker: ['print', 'group'], stats: ['business', 'domestic'],
    remote: ['domestic', 'overseas', 'ebook'], domestic: ['remote', 'citation', 'similarity'],
    overseas: ['remote', 'citation', 'dds'], citation: ['similarity', 'training'], similarity: ['citation', 'training'],
    ebook: ['oreilly', 'lectures'], oreilly: ['ebook', 'discipline'], dds: ['wish', 'other'],
    mobile: ['entry', 'seat', 'loan'], culture: ['ebook', 'programs'], training: ['domestic', 'citation'],
    sdi: ['trend'], trend: ['journal-index'], hours: ['floor', 'seat', 'bus'], floor: ['classification', 'hours'],
    entry: ['mobile', 'training'], lost: ['help'], wifi: ['help'], classification: ['missing', 'storage'],
    editage: ['enago'], enago: ['editage']
  };

  const dialog = $('#detail-dialog');

  function openDetail(id) {
    const s = byId(id);
    if (!s) return;
    const resource = s.recordKind === 'resource';
    const menu = s.recordKind === 'menu';
    $('#detail-category').textContent = kindName(s.recordKind) + ' · ' + (resource ? s.subject : menu ? s.menuGroup : categoryName(s.category));
    const kindNote = resource
      ? '공식 목록의 설명과 매뉴얼 링크를 정리한 항목이에요. 실제 외부 접속·회원가입·자료 이용은 시험하지 않았어요.'
      : menu
        ? '이 항목은 상세 사용설명서가 아닌 공식 메뉴 위치 안내입니다. 메뉴명·경로·링크를 확인했어요.'
        : '공개 상세 안내를 바탕으로 정리한 가이드입니다. 현재 운영·개인 이용자격은 이용 직전 확인해주세요.';
    const sourceLabel = resource
      ? (s.source.endsWith('er-ebook') ? '공식 전자책 목록에서 확인하기' : '공식 전자정보원 목록에서 이름 검색하기')
      : menu ? '공식 메뉴로 이동하기' : '공식 안내에서 확인하기';
    const materials = (s.materials || []).filter(m => /^https?:\/\//i.test(m.url));
    $('#detail-content').innerHTML = '<h2 id="detail-title">' + escape(s.name) + '</h2><p class="detail-question">'
      + escape(resource ? s.subject + ' · ' + s.sourceType : menu ? s.description : s.question) + '</p><p class="kind-note">'
      + escape(kindNote) + '</p><p class="detail-summary">' + escape(s.description) + '</p><dl class="detail-facts"><div><dt>이용 경로</dt><dd>'
      + escape(s.channel) + '</dd></div><div><dt>실제 서비스 로그인</dt><dd>' + escape(s.login) + '</dd></div><div><dt>비용</dt><dd>'
      + escape(s.cost) + '</dd></div></dl>'
      + (resource ? '<h3>공식 목록의 설명</h3><div class="official-excerpt">' + escape(s.officialDescription)
        + '</div><p class="material-note">원문 표기에 오류·과거 정보가 있을 수 있습니다. 제공 연도·수량·조건은 공식 안내를 재확인하세요.</p>' : '')
      + '<h3>' + (menu ? '이 메뉴를 찾으려면' : '이렇게 확인해요') + '</h3><ol>' + s.steps.map(step => '<li>' + escape(step) + '</li>').join('')
      + '</ol><h3>이용 전 확인할 점</h3><p class="detail-warning">' + escape(s.caution)
      + (s.duplicateCount > 1 ? '<br>원목록의 같은 이름 ' + s.duplicateCount + '개 항목을 합쳤습니다.' : '') + '</p>'
      + (materials.length ? '<h3>공식 제공 매뉴얼·관련 링크</h3><div class="material-list">' + materials.map(m => '<a href="'
        + escape(m.url) + '" target="_blank" rel="noopener noreferrer">' + escape(m.label) + ' ↗</a>').join('')
        + '</div><p class="material-note">목록에서 링크를 확인했으며 각 파일의 내용을 모두 읽거나 다운로드한 것은 아닙니다.</p>' : '')
      + (relatedMap[id] ? '<h3>함께 보면 좋은 안내</h3><div class="related">' + relatedMap[id].map(key => '<button type="button" data-open="'
        + key + '">' + escape(byId(key).name) + '</button>').join('') + '</div>' : '')
      + '<div class="detail-source"><a class="primary" href="' + escape(s.source) + '" target="_blank" rel="noopener noreferrer">'
      + sourceLabel + ' ↗</a><p>공개 안내 확인일 ' + escape(s.checkedAt) + ' · 비공식 학생용 가이드<br>이 사이트는 학교 계정·개인정보를 수집하지 않습니다. 실제 서비스는 별도 인증이 필요할 수 있습니다.</p></div>';
    if (!dialog.open) dialog.showModal();
    dialog.scrollTop = 0;
    $('#close-dialog').focus();
  }

  $('#close-dialog').addEventListener('click', () => dialog.close());
  dialog.addEventListener('click', e => {
    if (e.target !== dialog) return;
    const r = dialog.getBoundingClientRect();
    if (e.clientX < r.left || e.clientX > r.right || e.clientY < r.top || e.clientY > r.bottom) dialog.close();
  });

  const bookCases = {
    loan: { text: '대출 중인 책은 예약을 검토해보세요. 반납되면 우선 대출할 수 있습니다.', ids: ['loan'] },
    missing: { text: '검색에는 대출가능인데 서가에 없다면, 부재도서 신고로 찾아달라고 요청할 수 있어요.', ids: ['missing'] },
    campus: { text: '다른 분관에 있는 대출가능 도서는 캠퍼스대출 조건을 확인해보세요.', ids: ['campus'] },
    priority: { text: '정리중인 단행본은 우선정리 요청을 검토할 수 있어요.', ids: ['priority'] },
    storage: { text: '보존서고 자료는 홈페이지에서 먼저 신청하고 제공 알림 후 이용해요.', ids: ['storage'] },
    'not-owned': { text: '구입을 요청하려면 희망도서, 다른 기관 자료를 이용하려면 상호대차를 검토하세요.', ids: ['wish', 'dds'] }
  };

  document.addEventListener('click', e => {
    const open = e.target.closest('[data-open]');
    if (open) { openDetail(open.dataset.open); return; }
    const scope = e.target.closest('[data-scope]');
    if (scope) {
      e.preventDefault();
      changeScope(scope.dataset.scope);
      if (scope.tagName === 'A') $('#services').scrollIntoView({ behavior: 'smooth' });
      return;
    }
    const cat = e.target.closest('[data-category]');
    if (cat) {
      state.category = cat.dataset.category;
      state.query = '';
      state.limit = 12;
      $('#search-input').value = '';
      if (cat.classList.contains('category-card')) {
        state.scope = 'guide';
        $('#services').scrollIntoView({ behavior: 'smooth' });
      }
      render();
      return;
    }
    const book = e.target.closest('[data-book]');
    if (book) {
      const result = bookCases[book.dataset.book];
      document.querySelectorAll('[data-book]').forEach(b => b.setAttribute('aria-pressed', String(b === book)));
      $('#book-result').hidden = false;
      $('#book-result').innerHTML = '<p>' + escape(result.text) + '</p>' + result.ids.map(id => '<button type="button" data-open="'
        + id + '">' + escape(byId(id).name) + ' 이용 방법 ↗</button>').join('');
    }
  });

  $('#search-input').addEventListener('input', e => { state.query = e.target.value.trim(); state.limit = 12; render(); });
  $('#search-form').addEventListener('submit', e => {
    e.preventDefault();
    state.query = $('#search-input').value.trim();
    state.limit = 12;
    render();
  });
  $('#audience').addEventListener('change', e => { state.audience = e.target.value; state.limit = 12; render(); });
  for (const [id, key] of [['resource-subject', 'subject'], ['resource-type', 'sourceType'], ['resource-access', 'access'], ['menu-group', 'menuGroup']]) {
    $('#' + id).addEventListener('change', e => { state[key] = e.target.value; state.limit = 12; render(); });
  }
  $('#load-more').addEventListener('click', () => { state.limit += 12; render(); });
  $('#reset').addEventListener('click', reset);
  $('#empty-reset').addEventListener('click', () => { reset(); $('#search-input').focus(); });

  render();
})();
```

`index.html`의 `<script src="app.js" defer></script>`를 `<script src="js/app.js" defer></script>`로 바꾼다.

- [ ] **Step 6: 회귀 테스트로 동작 동일 확인**

Run: `python tests/smoke.py --stage 1 --browsers chromium,webkit --modes file,http`
Expected: 실패 0(마지막 줄의 두 숫자가 같음)

- [ ] **Step 7: 개발 문서** — `docs/DEV.md`

```markdown
# 개발 안내

## 로딩 순서와 전역
index.html이 아래 순서로 읽는다(모두 `defer`라 문서 순서대로 실행).
1. `data.js` → `window.LIBRARY_GUIDE` (생성물, 직접 고치지 않음)
2. `js/app.js` → 전역을 만들지 않는 IIFE

새 스크립트는 이 목록에 추가하고, 전역은 `window.LG`(순수 함수)·`window.LG_CONFIG`(설정) 외에는 만들지 않는다.

## 명령
- 테스트: `python tests/smoke.py --stage 1 --browsers chromium,webkit --modes file,http`
```

- [ ] **Step 8: 커밋 (이 커밋이 추출 기준)**

```bash
git add styles.css index.html js/app.js tools/format_css.py tools/css_snapshot.py docs/DEV.md
git commit -m "v3①: 코드 포맷 정리 (P1-02)" -m "app.js를 js/app.js로 옮겨 풀어 쓰고 styles.css를 풀어 중복 정리. 계산된 스타일 스냅숏(1440·800·390px)과 회귀 테스트로 동작 동일 확인" -m "$(cat .tmp/css-dedupe.txt)" -m "Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
```

---

### Task 3: JSON 추출과 data.js 생성 (P1-03)

**Files:**
- Create: `tools/extract_v2.py`, `tools/build_data.py`, `tools/v2-base.txt`, `data/meta.json`, `data/categories.json`, `data/services.json`, `data/resources.json`, `data/directory.json`, `data/related.json`, `data/book-cases.json`, `data/notices.json`, `data/common-text.json`
- Modify: `js/app.js` (상수 → 데이터), `data.js`(생성물로 대체), `docs/DEV.md`

**Interfaces:**
- Consumes: `datajs.load/dump`
- Produces:
  - `build_data.assemble() -> dict` (키 순서: `checkedAt, categories, services, resources, directory, metadata, related, bookCases, notices, commonText`)
  - `window.LIBRARY_GUIDE.related: {id: [id,…]}`, `.bookCases: {key: {text, ids}}`, `.notices: []`, `.commonText: {caution:[], steps:[], question:[], keywordSuffix:'공식 메뉴'}`

- [ ] **Step 1: 기준 커밋 기록**

Run: `git rev-parse HEAD > tools/v2-base.txt && cat tools/v2-base.txt`
Expected: Task 2 커밋 해시 한 줄

- [ ] **Step 2: 생성 도구** — `tools/build_data.py`

```python
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
```

- [ ] **Step 3: 추출 도구** — `tools/extract_v2.py`

```python
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
```

- [ ] **Step 4: 추출 실행**

Run: `python tools/extract_v2.py --write && python -c "import json;print(json.load(open('data/common-text.json',encoding='utf-8')).keys())"`
Expected: `data/*.json 작성 완료`, `dict_keys(['caution', 'steps', 'question', 'keywordSuffix'])`

- [ ] **Step 5: app.js가 데이터에서 읽도록 변경**

`js/app.js`에서 `const relatedMap = { … };` 블록 전체를 아래 한 줄로 바꾼다.

```js
  const relatedMap = window.LIBRARY_GUIDE.related || {};
```

`const bookCases = { … };` 블록 전체를 아래 한 줄로 바꾼다.

```js
  const bookCases = window.LIBRARY_GUIDE.bookCases || {};
```

- [ ] **Step 6: data.js를 생성물로 교체하고 검증**

Run: `python tools/build_data.py && python tools/build_data.py --check && python tools/extract_v2.py --verify`
Expected: `data.js 생성 …`, `data.js 일치`, `추출 검증 통과`

- [ ] **Step 7: 회귀 테스트**

Run: `python tests/smoke.py --stage 1 --browsers chromium,webkit --modes file,http`
Expected: 실패 0(마지막 줄의 두 숫자가 같음)

- [ ] **Step 8: DEV.md에 데이터 흐름 추가**

`docs/DEV.md` 끝에 추가:

```markdown
## 데이터
- 편집 원본은 `data/*.json`이다. 고친 뒤 `python tools/build_data.py`로 data.js를 다시 만든다.
- `python tools/build_data.py --check`: data.js가 원본과 같은지 확인(쓰지 않음).
- `data/common-text.json`: 검색 색인에서 뺄 공통 문장(10회 이상 반복되는 caution·steps·메뉴 question). 화면 표시는 그대로다.
```

- [ ] **Step 9: 커밋**

```bash
git add tools/extract_v2.py tools/build_data.py tools/v2-base.txt data/ data.js js/app.js docs/DEV.md
git commit -m "v3①: 데이터를 data/*.json 원본으로 추출 (P1-03)" -m "relatedMap·bookCases를 코드에서 데이터로 옮김. 기준 커밋 대비 내용·렌더 결과 동일 검증" -m "Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
```

---

### Task 4: 데이터 검사와 화면 안전 (P1-04)

**Files:**
- Create: `js/lib.js`, `tests/check_data.py`, `tests/test_safety.py`
- Modify: `js/app.js`, `index.html`(스크립트 추가), `docs/DEV.md`

**Interfaces:**
- Produces:
  - `window.LG.escapeHtml(v) -> string`, `window.LG.safeUrl(u) -> string`('https://'로 시작하면 그대로, 아니면 `''`)
  - `check_data.py --stage 1 [--today YYYY-MM-DD]` → 문제 목록 출력, 있으면 종료 코드 1. 함수 `run_checks(data, stage, today) -> list[str]`

- [ ] **Step 1: 실패하는 안전 테스트 작성** — `tests/test_safety.py`

```python
"""화면 안전: 데이터의 악성 문자열이 실행되거나 링크로 열리지 않는다."""
from harness import check, test

# facts·찾는 방법·대상·공지 경로도 미리 넣어 둔다. 뒤 Task가 이 필드를 화면에 그리기 시작하면 이 테스트가 자동으로 그 경로까지 검사한다(S11)
EVIL = r"""(() => { let v; Object.defineProperty(window, 'LIBRARY_GUIDE', { configurable: true,
  get() { return v; },
  set(x) { x.services.unshift({ id: 'x"onmouseover="window.__xss=2', name: '<img src=x onerror="window.__xss=1">',
    question: 'q', category: 'start', description: '<b>d</b>', audience: 'all', channel: 'c', login: 'l', cost: 'c',
    caution: '<img src=x onerror="window.__xss=4">', steps: ['s'], source: 'javascript:window.__xss=3', keywords: 'evil',
    checkedAt: '2026-10-13', recordKind: 'guide', materials: [{ label: 'm', url: 'http://insecure.example' }],
    findHint: '<img src=x onerror="window.__xss=5">', eligibilityNote: '<img src=x onerror="window.__xss=6">',
    facts: [{ text: '<img src=x onerror="window.__xss=7">', source: 'javascript:window.__xss=8', checkedAt: '2026-10-13' }] });
    x.notices = [{ id: 'evil-notice', text: '<img src=x onerror="window.__xss=9">', link: 'javascript:window.__xss=10',
      source: 'javascript:window.__xss=11', checkedAt: '2026-10-13', startsOn: '2026-10-01', endsOn: '2026-12-31',
      taskIds: ['x"onmouseover="window.__xss=2'] }];
    v = x; } }); })();"""


@test()
def t_malicious_data_is_inert(site):
    site.page.add_init_script(EVIL)
    site.open()
    site.search('evil')
    site.page.locator('#service-grid .service-card').first.hover()
    site.page.locator('#service-grid button').first.click()
    site.page.wait_for_selector('#detail-dialog[open]')  # 상세가 실제로 열린 상태에서 검사한다(S11)
    site.page.wait_for_timeout(200)
    check(site.page.evaluate('window.__xss') is None, f'스크립트가 실행됨: {site.page.evaluate("window.__xss")}')
    hrefs = site.page.eval_on_selector_all('a[href]', 'els => els.map(e => e.getAttribute("href"))')
    bad = [h for h in hrefs if h.lower().startswith(('javascript:', 'http:'))]
    check(not bad, f'안전하지 않은 링크: {bad}')
```

- [ ] **Step 2: 실패 확인**

Run: `python tests/smoke.py --stage 1 -k t_malicious`
Expected: `FAIL … 안전하지 않은 링크: ['javascript:window.__xss=3', 'http://insecure.example']`

- [ ] **Step 3: 순수 함수 모듈** — `js/lib.js`

```js
// 도서관의 쓸모 — 순수 함수 모음(window.LG). DOM을 만지지 않는다.
(() => {
  'use strict';
  const LG = (window.LG = window.LG || {});

  LG.escapeHtml = value => String(value ?? '').replace(/[&<>"']/g, c => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  }[c]));

  // https 링크만 허용한다. 그 밖에는 빈 문자열.
  LG.safeUrl = url => (/^https:\/\//i.test(String(url ?? '')) ? String(url) : '');
})();
```

`index.html`에서 `<script src="js/app.js" defer></script>` 바로 앞에 `<script src="js/lib.js" defer></script>`를 넣는다. `js/app.js` 맨 위 주석의 로딩 순서도 `data.js → js/lib.js → js/app.js`로 고친다.

- [ ] **Step 4: app.js를 lib.js로 통일**

`js/app.js` 맨 위 상수 부분을 다음으로 바꾼다(`escape` 정의 삭제).

```js
  const { escapeHtml: escape, safeUrl } = window.LG;
```

그리고 아래 다섯 곳을 고친다.

1. `card()`의 버튼: `data-open="' + s.id + '"` → `data-open="' + escape(s.id) + '"`
2. 상황 카드·탭: `data-category="' + c.id + '"` → `data-category="' + escape(c.id) + '"` (두 곳)
3. `openDetail()`의 매뉴얼 필터: `/^https?:\/\//i.test(m.url)` → `safeUrl(m.url)`
4. 관련 안내·책 상황 버튼: `data-open="' + key + '"`·`data-open="' + id + '"` → `escape(key)`·`escape(id)`. 대상이 없으면 건너뛴다: `relatedMap[id].filter(byId).map(…)`, `result.ids.filter(byId).map(…)`
5. 공식 버튼: `href="' + escape(s.source) + '"` → `href="' + escape(safeUrl(s.source)) + '"`이고, `safeUrl(s.source)`가 빈 문자열이면 버튼 대신 `<p>공식 링크를 확인할 수 없어요.</p>`

- [ ] **Step 5: 안전 테스트 통과 확인**

Run: `python tests/smoke.py --stage 1 -k t_malicious --browsers chromium,webkit`
Expected: `PASS` 2줄

- [ ] **Step 6: 데이터 검사 도구** — `tests/check_data.py`

```python
"""데이터 검사. 사용: python tests/check_data.py --stage 1 [--today YYYY-MM-DD] [--data data.js]
--today는 테스트에서만 쓴다. 운영 점검과 push 게이트는 실제 날짜로 돌린다(PRD K18)."""
import argparse
import datetime
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import datajs  # noqa: E402

KINDS = ('services', 'resources', 'directory')
ID_RE = re.compile(r'^[a-z0-9-]+$')


def https(u):
    return isinstance(u, str) and u.startswith('https://')


def run_checks(d, stage, today):
    errs = []
    recs = [r for k in KINDS for r in d[k]]
    ids = [r['id'] for r in recs]
    have = set(ids)
    if len(ids) != len(have):
        errs.append('id 중복')
    for r in recs:
        rid = r.get('id', '?')
        if not ID_RE.match(rid):
            errs.append(f'{rid}: id 형식(영문 소문자·숫자·하이픈)')
        for f in ('name', 'description', 'source', 'recordKind'):
            if not r.get(f):
                errs.append(f'{rid}: {f} 없음')
        if not r.get('steps'):
            errs.append(f'{rid}: steps 없음')
        if not https(r.get('source')):
            errs.append(f'{rid}: source가 https 아님')
        for m in r.get('materials') or []:
            if not https(m.get('url')):
                errs.append(f'{rid}: 매뉴얼 링크가 https 아님 {m.get("url")}')
    fixture = json.loads((ROOT / 'tests' / 'fixtures' / 'v2-ids.json').read_text(encoding='utf-8'))
    missing = [i for k in fixture for i in fixture[k] if i not in have]
    if missing:
        errs.append(f'v2 id 누락 {len(missing)}개: {missing[:5]}')
    for key, targets in (d.get('related') or {}).items():
        for t in [key, *targets]:
            if t not in have:
                errs.append(f'related: 없는 id {t}')
    for key, case in (d.get('bookCases') or {}).items():
        for t in case.get('ids', []):
            if t not in have:
                errs.append(f'bookCases.{key}: 없는 id {t}')
    return errs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--stage', type=int, default=1)
    ap.add_argument('--today', default=datetime.date.today().isoformat())
    ap.add_argument('--data', default=str(ROOT / 'data.js'))
    a = ap.parse_args()
    errs = run_checks(datajs.load(a.data), a.stage, a.today)
    for e in errs:
        print('ERROR', e)
    print(f'데이터 검사: 문제 {len(errs)}건')
    sys.exit(1 if errs else 0)


if __name__ == '__main__':
    main()
```

- [ ] **Step 7: 검사 실행**

Run: `python tests/check_data.py --stage 1`
Expected: `데이터 검사: 문제 0건`

- [ ] **Step 8: 회귀 테스트와 DEV.md**

Run: `python tests/smoke.py --stage 1 --browsers chromium,webkit --modes file,http`
Expected: 실패 0(마지막 줄의 두 숫자가 같음)

`docs/DEV.md`의 로딩 순서 목록을 `data.js` → `js/lib.js`(window.LG) → `js/app.js`로 고치고, 명령에 `python tests/check_data.py --stage 1`을 추가한다.

- [ ] **Step 9: 커밋**

```bash
git add js/lib.js js/app.js index.html tests/check_data.py tests/test_safety.py docs/DEV.md
git commit -m "v3①: 데이터 검사와 화면 안전 (P1-04)" -m "이스케이프·https 도우미를 lib.js로 통일, id 속성 이스케이프, 악성 데이터 테스트, check_data stage 1" -m "Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
```

---

### Task 5: 공식 사실로 콘텐츠 수정·반납 안내 추가 (P1-05, P1-07 데이터, P1-13)

근거는 RESEARCH 5장(사실별 출처)과 `research/official_facts.md`다. 이 작업은 표·스크립트에 있는 사실만 넣고, 새 사실을 지어내지 않는다.

**Files:**
- Modify: `data/services.json`, `data/resources.json`, `data/related.json`, `data/meta.json`, `tests/check_data.py`, `tests/test_regression.py`
- Create: `tests/test_content.py`, `.tmp/apply_content.py`(일회성, git 제외 폴더)

**Interfaces:**
- Produces (데이터 필드, ① 보조 필드, PRD P1-05·P1-07·D16):
  - 레코드 선택 필드 `facts: [{kind?, text, source, checkedAt}]`. `kind`는 `location`(상세의 위치)·`auth`(상세의 인증·로그인 요약)·`hours`(시간) 중 하나이거나 생략(상세의 "확인한 사실")
  - `eligibilityNote: string`(대상 요약), `costNote: string`(비용 요약). 이 둘이 있는 레코드는 근거 `facts`가 하나 이상 있어야 한다
  - 새 가이드 id `book-return`(`loan` 바로 뒤)
- 바꾸지 않는 것: `audience`(학부/대학원 필터용, R10), 레코드 id. `findHint`는 Task 8에서 넣는다.

- [ ] **Step 1: 실패하는 콘텐츠 테스트** — `tests/test_content.py`

```python
"""공식 사실 기반 콘텐츠(2026-10-13 확인)가 데이터에 들어 있는지 확인한다. 근거: RESEARCH 5장."""
from harness import check, test

SRC = 'https://lib.jejunu.ac.kr/'
COMMON_CAUTION = '목록에 등재되어 있다는 사실만으로'


def rec(d, rid):
    return next(r for k in ('services', 'resources', 'directory') for r in d[k] if r['id'] == rid)


def facts(d, rid, kind=None):
    return [f for f in rec(d, rid).get('facts', []) if kind is None or f.get('kind') == kind]


def texts(d, rid, kind=None):
    return ' '.join(f['text'] for f in facts(d, rid, kind))


@test()
def t_content_hours_print(site):
    site.open()
    d = site.data()
    hours = rec(d, 'hours')
    rule = texts(d, 'hours', 'hours')
    check('3주간 24시간 개방' in rule and '1~4열람실' in rule, f'hours: 24시간 개방 규칙과 적용 공간 {rule}')
    check('교대분관' in hours['caution'], 'hours: 교대분관 미확인 표시 없음')
    check(not hours.get('materials'), 'hours: 지난 공지 링크가 카드에 남아 있음(M3)')
    loc = texts(d, 'print', 'location')
    check('3층 3열람실' in loc and '미디어라운지' in loc, f'print 위치 {loc}')
    check('09:00~20:00' in texts(d, 'print', 'hours'), 'print: 미디어라운지 시간 없음')


@test()
def t_content_spaces(site):
    site.open()
    d = site.data()
    for rid, note in (('group', '재학생·교직원'), ('maker', '재학생·교직원'), ('carrel', '대학원생·교직원'),
                      ('locker', '재학생'), ('delivery', '장애인')):
        check(note in (rec(d, rid).get('eligibilityNote') or ''), f'{rid}: eligibilityNote')
        check(facts(d, rid), f'{rid}: 대상 근거(facts) 없음')
    group_loc = texts(d, 'group', 'location')
    check('201~210호' in group_loc and '층' not in group_loc, f'group 위치는 호실만(층은 미확인): {group_loc}')
    check(any(f['source'].endswith('#/guide/hoo/floor') for f in facts(d, 'maker', 'location')), 'maker 층의 출처는 층별안내')
    check('미소장' in texts(d, 'delivery') and '확인하지 못했' in rec(d, 'delivery')['caution'], '책나래: 범위 차이·미확인 표시 없음')
    check('3월' in texts(d, 'locker') and len(facts(d, 'locker')) >= 3, '사물함: 신청 시기·경로 없음')
    check('미확인' in (rec(d, 'seat').get('eligibilityNote') or ''), '일반열람실: 대상 미확인 표시 없음(PRD 2장 3번)')
    check('09:00~20:00' in texts(d, 'group', 'hours') and '30분' in texts(d, 'group'), '그룹스터디룸: 운영시간·예약 방법 없음')
    check('자동 취소' in texts(d, 'maker'), '메이커: 예약 방법 없음')
    for rid, page in (('group', 'studyroom'), ('maker', 'makerstudio'), ('carrel', 'carrel'), ('seat', 'readingroom')):
        check(rec(d, rid)['source'] == SRC + '#/service/facility/' + page, f'{rid}: 공식 링크가 개별 시설 페이지가 아님')


@test()
def t_content_remote_and_resources(site):
    site.open()
    d = site.data()
    check('무료' not in rec(d, 'remote')['keywords'], 'remote 키워드에 무료')
    check(facts(d, 'remote', 'auth'), 'remote: 인증 예외 요약 없음')
    check('WSJ' in texts(d, 'culture', 'auth'), 'culture: 고친 WSJ 문구의 근거 없음')
    for rid in ('er-007', 'er-010', 'er-035'):
        check('로그인' in texts(d, rid, 'auth'), f'{rid}: 새 주의 문구의 로그인 근거 없음')
    check('openlink' in texts(d, 'remote'), 'remote: 공식 이용법(openlink) 없음')
    for rid, word in (('er-085', '학내 IP'), ('er-057', '초대링크'), ('er-090', '로그인 후'), ('er-093', '학교 이메일'),
                      ('er-094', '학교 이메일'), ('er-095', '학교 이메일'), ('er-096', '학교 이메일')):
        check(word in texts(d, rid, 'auth'), f'{rid}: 인증 사실({word}) 없음')
    for rid in ('er-093', 'er-094', 'er-095', 'er-096'):
        check(rec(d, rid)['name'].endswith(' Trial'), f'{rid}: 공식 목록 표기(Trial) 아님')
    for rid in ('er-007', 'er-010', 'er-017', 'er-035'):
        check(COMMON_CAUTION not in rec(d, rid)['caution'], f'{rid}: 성격에 맞지 않는 공통 주의 문구')
    for rid in ('editage', 'enago'):
        check('협약가' in texts(d, rid), f'{rid}: 비용 근거 없음')


@test()
def t_content_sources(site):
    site.open()
    d = site.data()
    for r in [r for k in ('services', 'resources') for r in d[k]]:
        for f in r.get('facts', []):
            check(f['source'].startswith(SRC) and f['checkedAt'] >= '2026-10-13', f'{r["id"]}: facts 출처·확인일')
            check(f.get('kind') in (None, 'location', 'auth', 'hours'), f'{r["id"]}: facts.kind {f.get("kind")}')


@test()
def t_book_return_guide(site):
    site.open()
    d = site.data()
    g = rec(d, 'book-return')
    check(g['source'] == SRC + '#/service/circulation/return', f'반납 source {g["source"]}')
    check(g['category'] == 'books', '반납 분류')
    check('제증명' in texts(d, 'book-return'), '연체 시 제증명 발급 제한 없음')
    check('확인하지 못함' in g['cost'], f'반납 비용 칸이 연체료를 단정함: {g["cost"]}')
    check('반납 처리' in g['caution'] and '자동반납기' in g['caution'], '반납함 처리 시점·자동반납기 위치 미확인 표시 없음')
    check('book-return' in d['related'].get('loan', []), 'loan → book-return 관련 안내 없음')
```

`tests/test_regression.py`에서 `d02_free_word`를 **삭제**한다. 이 작업이 "무료"가 든 키워드와 공통 주의 문구를 바꾸므로 89건 고정값이 깨진다. "무료" 0건 검사는 Task 6의 `t_free_word_zero`가 맡는다(S15).

`d05_book_return_missing`은 아래로 바꾼다(기대값 전환).

```python
@test()
def d05_book_return_found(site):  # Task 5에서 전환
    site.open()
    site.search('책 반납')
    check('book-return' in site.result_ids()[:3], f'책 반납 상위 3개 {site.result_ids()[:3]}')
```

Run: `python tests/smoke.py --stage 1 -k test_content` 그리고 `python tests/smoke.py --stage 1 -k d05`
Expected: `FAIL`(facts·book-return 없음)

- [ ] **Step 2: 콘텐츠 수정 스크립트** — `.tmp/apply_content.py`(일회성. `.tmp/`는 git 제외)

```python
"""Task 5 일회성 콘텐츠 수정(RESEARCH 5장의 사실만). 사용: python .tmp/apply_content.py"""
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
SRC = 'https://lib.jejunu.ac.kr/'
DAY = '2026-10-13'


def fact(text, page, kind=None):
    f = {'kind': kind} if kind else {}
    f.update({'text': text, 'source': SRC + page, 'checkedAt': DAY})
    return f


SERVICES = {
    'hours': {
        'caution': '중앙도서관 1~4열람실·PC zone은 06:00~24:00(연중무휴)이고, 시험기간(중간·기말)에는 3주간 24시간 개방한다고 안내됩니다. '
                   '중앙디지털도서관은 학기 중 평일 09~20·토 09~13, 방학 중 평일 09~18이고 일요일·공휴일은 휴관입니다. '
                   '제주자료실 시간은 이용시간 페이지와 시험 공지의 표기가 달라 확인이 필요합니다. '
                   '교대분관 열람실이 시험기간 24시간 개방에 포함되는지는 확인하지 못했습니다. 실시간 운영 상태는 표시하지 않습니다.',
        'materials': None,
        'facts': [
            fact('중앙도서관 1~4열람실(2·3층)·PC zone: 06:00~24:00(연중무휴). 시험기간(중간·기말)은 3주간 24시간 개방',
                 '#/guide/hoo/hoo', 'hours'),
            fact('중앙디지털도서관 1·2자료실·그룹스터디라운지·미디어라운지 등: 학기 중 평일 09:00~20:00, 토 09:00~13:00'
                 '(방학 중 평일 09:00~18:00), 일요일·공휴일 휴관', '#/guide/hoo/hoo', 'hours'),
        ],
    },
    'print': {
        'description': '중앙도서관 3층 3열람실과 중앙디지털도서관 1층 미디어라운지에서 인쇄·복사를, 지정석에서 스캔을 할 수 있어요.',
        'steps': ['인쇄·복사는 중앙도서관 3층 3열람실 또는 중앙디지털도서관 1층 미디어라운지로 이동',
                  '스캔은 스캔 지정석에서 직접 이용', '인쇄·복사는 신용카드·교통카드로 결제'],
        'costNote': '인쇄 100원 · 복사 50원 · 스캔 무료',
        'facts': [
            fact('인쇄·복사: 중앙도서관 3층 3열람실, 중앙디지털도서관 1층 미디어라운지', '#/service/print', 'location'),
            fact('스캔: 중앙도서관 1층 PC존·1층 제주자료실·3층 3열람실, 중앙디지털도서관 1층 미디어라운지', '#/service/print', 'location'),
            fact('요금: 인쇄 100원, 복사 50원(신용카드·교통카드). 스캔은 무료', '#/service/print'),
            fact('이용시간은 자료실(열람실) 운영시간과 같음', '#/service/print', 'hours'),
            fact('중앙디지털도서관 미디어라운지: 학기 중 평일 09:00~20:00, 토 09:00~13:00, 일요일·공휴일 휴관', '#/guide/hoo/hoo', 'hours'),
        ],
    },
    'group': {
        'eligibilityNote': '재학생·교직원',
        'source': SRC + '#/service/facility/studyroom',
        'facts': [
            fact('중앙디지털도서관 201~210호', '#/service/facility/studyroom', 'location'),
            fact('운영시간: 중앙디지털도서관과 같음(학기 중 평일 09:00~20:00, 토 09:00~13:00 / 방학 중 평일 09:00~18:00)',
                 '#/service/facility/studyroom', 'hours'),
            fact('이용 대상 재학생·교직원, 1일 3시간', '#/service/facility/studyroom'),
            fact('예약: 모바일 앱 로그인 후 7일 전부터 당일까지, 30분 단위. 예약 20분 뒤까지 입실하지 않으면 자동 취소, '
                 '한 학기 3회 이상 예약 부도 시 그 학기 사용 제한', '#/service/facility/studyroom'),
        ],
    },
    'maker': {
        'eligibilityNote': '재학생·교직원',
        'source': SRC + '#/service/facility/makerstudio',
        'facts': [
            fact('중앙도서관 2층', '#/guide/hoo/floor', 'location'),
            fact('평일 09:00~18:00, 1일 3시간', '#/service/facility/makerstudio', 'hours'),
            fact('이용 대상 재학생·교직원', '#/service/facility/makerstudio'),
            fact('예약: 모바일 앱 로그인 후 7일 전부터 당일까지. 예약 10분 뒤까지 입실하지 않으면 자동 취소, '
                 '한 학기 3회 이상 예약 부도 시 그 학기 사용 제한', '#/service/facility/makerstudio'),
        ],
    },
    'carrel': {
        'eligibilityNote': '대학원생·교직원(학부생 이용 불가)',
        'source': SRC + '#/service/facility/carrel',
        'facts': [
            fact('중앙디지털도서관 2층', '#/service/facility/carrel', 'location'),
            fact('이용 대상 대학원생·교직원', '#/service/facility/carrel'),
            fact('학부생 안내: 캐럴 이용 불가', '#/service/user/user01'),
        ],
    },
    'seat': {
        'eligibilityNote': '대상 미확인',
        'source': SRC + '#/service/facility/readingroom',
        'facts': [
            fact('중앙도서관 1층 PC zone, 2층 1열람실, 3층 2·3·4열람실, 교대분관 3층 열람실', '#/service/facility/readingroom', 'location'),
            fact('좌석발급시스템으로 배정받아 이용. 최초 4시간, 1일 1회 4시간 연장', '#/service/facility/readingroom'),
            fact('일반열람실 안내에 이용 대상 문구가 없음(대상 미확인)', '#/service/facility/readingroom'),
        ],
    },
    'locker': {
        'eligibilityNote': '재학생(휴학생·연체도서가 있는 경우 신청 불가)',
        'facts': [
            fact('중앙도서관 2층 210개, 3층 309개', '#/service/locker', 'location'),
            fact('이용 대상 재학생(신청 불가: 휴학생, 연체도서가 있는 경우). 신청은 매 학기초(3월·9월), 사용 기간 1학기(약 6개월)',
                 '#/service/locker'),
            fact('2026-2학기 신청 경로는 "도서관서비스 - 프로그램 신청 - 사물함 신청"으로 공지됨(서비스 페이지의 메뉴 이름과 다름)',
                 '#/bbs/notice/6547'),
        ],
    },
    'delivery': {
        'eligibilityNote': '도서관 방문이 어려운 장애인 이용자(담당자 승인 후)',
        'caution': '모든 학생에게 제공되는 일반 배송 서비스는 아닙니다. 이용자격과 담당자 승인 절차를 확인하세요. '
                   '대상 자료가 서비스 페이지에는 "도서관 자료", 장애학생 안내에는 "미소장 자료"로 다르게 적혀 있고, '
                   '어느 범위가 맞는지는 확인하지 못했습니다.',
        'facts': [
            fact('도서관 방문이 어려운 장애인 이용자에게 도서관 자료를 우체국 택배로 무료 제공. 도서관 담당자 승인 후 이용', '#/service/booknarae'),
            fact('장애학생 안내에는 책나래가 "제주대학교 도서관 미소장 자료" 대상으로 적혀 있음(소장 자료는 장애학생 One Stop 서비스)',
                 '#/service/user/user04'),
        ],
    },
    'remote': {
        'description': '교외에서도 도서관 전자정보원을 이용하도록 안내돼요. 일부 자료는 교내 등록이나 별도 계정이 필요해요.',
        'keywords': '집 밖 교외 학교 밖 논문 접근 원격',
        'facts': [
            fact('일부 자료는 예외(WSJ·CAS·NICE bizLINE·Value-Search)', '#/search/er', 'auth'),
            fact('공식 이용법: DB 주소 앞에 교외접속(openlink) 주소를 붙여 접속. 별도 프로그램이나 설정은 필요 없음', '#/research/offacess'),
            fact('예외: WSJ는 학내 IP 대역에서만 회원가입 등록, CAS는 교내에서 학교 이메일로 계정 생성, '
                 'NICE bizLINE은 회사직원 초대링크 입력, Value-Search는 개인 ID 등록(ID/PW는 도서관 로그인 후 확인)', '#/search/er'),
        ],
    },
    'culture': {
        'caution': 'WSJ는 회원가입 후 이용하며 학내 IP 대역에서만 등록할 수 있다고 안내됩니다. Naxos는 동시 이용자수 제한이 있습니다.',
        'facts': [fact('WSJ: 회원가입 후 이용, 학내 IP 대역에서만 등록 가능', '#/search/er', 'auth')],
    },
    'mobile': {
        'caution': '앱 이름은 제주대학교 모바일 도서관입니다. 2026년 9월 iOS 27 기기에서 앱 호환성 오류 공지가 있었으니, '
                   '앱이 동작하지 않으면 최신 공지를 확인하세요.',
        'facts': [fact('iOS 27 기기 앱 호환성 오류 공지(2026.09.17). 복구 여부는 확인하지 못함', '#/bbs/notice/6648')],
    },
    'editage': {
        'costNote': '유료 협약가 · 견적 확인',
        'facts': [fact('공동웹페이지로 의뢰한 연구자에게 협약가로 교정 제공. 무료는 저자 질문 답변·학술지 서식 설정(일반교정 1회) 같은 일부 부가서비스',
                       '#/research/correction')],
    },
    'enago': {
        'costNote': '유료 협약가 · VAT 별도',
        'facts': [fact('공동웹페이지로 의뢰한 연구자에게 협약가 제공(VAT 별도). 제주대 웹메일 외 계정도 사용 가능', '#/research/correction-enago')],
    },
}

CAS_AUTH = [fact('계정은 교내에서 학교 이메일(@jejunu.ac.kr)로 생성', '#/search/er', 'auth')]
RESOURCES = {
    'er-007': {'caution': '표절 검사 서비스입니다. 도서관 홈페이지 로그인 후 이용하도록 안내됩니다. 검사 결과를 어떻게 제출하는지는 과제 안내를 따르세요.',
               'facts': [fact('이용방법: 도서관 홈페이지 로그인 후 사용', '#/search/er', 'auth')]},
    'er-010': {'caution': '공무원 시험 동영상 강의 서비스입니다. 도서관 홈페이지 로그인 후 이용하도록 안내됩니다. 들을 수 있는 강의 범위는 공식 안내에서 확인하세요.',
               'facts': [fact('도서관 홈페이지 로그인 후 이용 가능', '#/search/er', 'auth')]},
    'er-017': {'caution': '도서관이 구독하는 저널을 알파벳순으로 찾는 도구입니다. 저널이 목록에 있어도 구독 연도에 따라 원문을 볼 수 있는 범위가 다를 수 있습니다.'},
    'er-035': {'caution': '참고문헌 관리 프로그램입니다. 도서관 홈페이지 로그인 후 설치 파일을 받아 개인 PC에 설치하도록 안내되며, '
                          '설치 순서(파일 저장 → 압축 해제 → 설치)를 지켜야 합니다.',
               'facts': [fact('로그인 후 설치 파일을 받아 개인 PC에 설치한 뒤 이용', '#/search/er', 'auth')]},
    'er-037': {'keywords': '공개 오픈액세스 의학 저널'},
    'er-098': {'keywords': '예스24 yes24 크레마클럽 신간 전자책 ebook'},
    'er-085': {'facts': [fact('회원가입 후 이용, 학내 IP 대역에서만 등록 가능', '#/search/er', 'auth')]},
    'er-057': {'facts': [fact('개인 ID 등록 때 기관계정 대신 회사직원 초대링크 입력(문의 research@jejunu.ac.kr, 064-754-2229~30)',
                              '#/search/er', 'auth')]},
    'er-090': {'facts': [fact('개인별 ID 등록. 이용을 위한 ID/PW는 도서관 홈페이지 로그인 후 확인', '#/search/er', 'auth')]},
    'er-093': {'name': 'CAS SciFinder Trial', 'facts': CAS_AUTH},
    'er-094': {'name': 'CAS Analytical Methods Trial', 'facts': CAS_AUTH},
    'er-095': {'name': 'CAS Formulus Trial', 'facts': CAS_AUTH},
    'er-096': {'name': 'CAS BioFinder Trial', 'facts': CAS_AUTH},
}

BOOK_RETURN = {
    'id': 'book-return',
    'name': '책 반납하기',
    'question': '다 읽은 책을 반납하고 싶어',
    'category': 'books',
    'description': '자동반납기·대출대·무인반납함에서 반납할 수 있어요. 늦으면 늦은 날수만큼 대출이 정지돼요.',
    'audience': 'all',
    'channel': '자동반납기 · 대출대 · 무인반납함',
    'login': '현장 반납',
    'cost': '연체료 금액은 공식 안내에서 확인하지 못함',
    'caution': '딸림자료가 있거나 예약된 책은 대출대에 반납해야 합니다. 연체하면 연체일수만큼 대출이 정지되고 증명서 발급도 제한됩니다. '
               '무인반납함에 넣은 책이 언제 반납 처리되는지, 자동반납기가 어디 있는지, 다른 분관 책을 어디서 반납하는지는 '
               '공식 안내에서 확인하지 못했습니다.',
    'steps': ['자동반납기에서 직접 반납 처리하고 확인증 받기',
              '딸림자료·예약된 책은 대출대에 반납하고 처리 상황 확인',
              '업무시간이 끝나면 중앙도서관 1층 로비 또는 중앙디지털도서관 정문 앞 무인반납함에 넣기'],
    'source': SRC + '#/service/circulation/return',
    'keywords': '반납 책 반납 반납함 무인반납 자동반납기 연체 늦게 돌려주기',
    'checkedAt': DAY,
    'recordKind': 'guide',
    'facts': [
        fact('무인반납함: 중앙도서관 1층 로비, 중앙디지털도서관 정문 앞(업무시간 종료 이후)', '#/service/circulation/return', 'location'),
        fact('연체하면 연체일수만큼 대출이 정지되고, 도서 대출과 제증명 발급이 제한됨', '#/service/circulation/return'),
    ],
}


def load(name):
    return json.loads((DATA / name).read_text(encoding='utf-8'))


def save(name, obj):
    (DATA / name).write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')


def patch(records, changes):
    by_id = {r['id']: r for r in records}
    for rid, fields in changes.items():
        for key, value in fields.items():
            if value is None:
                by_id[rid].pop(key, None)
            else:
                by_id[rid][key] = value


services = load('services.json')
patch(services, SERVICES)
if not any(s['id'] == 'book-return' for s in services):
    services.insert(next(i for i, s in enumerate(services) if s['id'] == 'loan') + 1, BOOK_RETURN)
save('services.json', services)
resources = load('resources.json')
patch(resources, RESOURCES)
save('resources.json', resources)
related = load('related.json')
related['loan'] = ['book-return', 'night', 'wish']
related['book-return'] = ['loan', 'my-library']
save('related.json', related)
meta = load('meta.json')
meta['metadata']['guideCount'] = 48
save('meta.json', meta)
print('콘텐츠 수정 완료: 가이드', len(services), '· 자료', len(resources))
```

Run: `python .tmp/apply_content.py`
Expected: `콘텐츠 수정 완료: 가이드 48 · 자료 98`

이 스크립트는 2026-10-13 계획 단계에서 v2 데이터 사본에 미리 적용해 확인했다: 콘텐츠 테스트·데이터 검사 규칙 통과, 대표 검색 수치(q04) 그대로, Task 6 전에도 "책 반납"의 2위가 book-return. 그룹스터디룸·메이커스튜디오의 운영시간·예약 사실은 4차 평가 뒤 시설 페이지 원문에서 확인했다(official_facts 8장).

- [ ] **Step 3: check_data에 facts·주장 단어 검사 추가** — `run_checks`의 `for r in recs:` 반복 안에 추가

```python
        for f in r.get('facts') or []:
            if not f.get('text') or not https(f.get('source')) or not re.match(r'^\d{4}-\d{2}-\d{2}$', f.get('checkedAt', '')):
                errs.append(f'{rid}: facts 형식(text·https source·YYYY-MM-DD checkedAt)')
            if f.get('kind') not in (None, 'location', 'auth', 'hours'):
                errs.append(f'{rid}: facts.kind {f.get("kind")}(location·auth·hours만, D16)')
        if (r.get('eligibilityNote') or r.get('costNote')) and not r.get('facts'):
            errs.append(f'{rid}: eligibilityNote·costNote의 근거 facts 없음(P1-05)')
        for field in ('name', 'question', 'description', 'keywords'):
            if re.search('무료|무제한', str(r.get(field) or '')):
                errs.append(f'{rid}: 주장 필드 {field}에 무료·무제한(PRD K10)')
```

- [ ] **Step 4: 생성·검사·테스트**

Run: `python tools/build_data.py && python tests/check_data.py --stage 1 && python tests/smoke.py --stage 1 --browsers chromium,webkit --modes file,http`
Expected: `문제 0건`, 실패 0(마지막 줄의 두 숫자가 같음)

- [ ] **Step 5: 커밋**

```bash
git add data/ data.js tests/
git commit -m "v3①: 공식 사실로 콘텐츠 수정·반납 안내 추가 (P1-05, P1-13)" -m "시험기간 개방 규칙과 적용 공간, 인쇄 위치 두 곳과 시간, 대상·위치·인증 사실(사실마다 출처), 시설 카드의 공식 링크를 개별 페이지로, 성격이 다른 자료의 주의 문구, 주장 필드의 무료·무제한 제거, CAS 공식 표기, 반납 안내 추가. 확인일 2026-10-13" -m "Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
```

---

### Task 6: 검색 기본 정비 (P1-08)

**Files:**
- Create: `data/normalize-cases.json`, `tools/normalize.py`, `tools/perf.py`, `tests/test_search.py`
- Modify: `js/lib.js`, `js/app.js`, `data/services.json`(overseas 키워드), `tests/check_data.py`, `tests/test_regression.py`, `tools/build_data.py`(normalize-cases는 data.js에 넣지 않음 — 변경 없음 확인)

**Interfaces:**
- Consumes: `window.LIBRARY_GUIDE.commonText`
- Produces:
  - `LG.normalize(v) -> string`, `LG.tokenize(q) -> string[]`, `LG.FREE_WORDS = ['무료','무제한']`
  - `LG.SEARCH_FIELDS = {guide: [...], resource: [...], menu: [...]}`(PRD 6장 ① 표, K9)
  - `state.query`는 입력창 원문(공백 포함)이다. 공백·기호만 있으면 안내 화면, 비어 있으면 처음 목록(S3)
  - `LG.buildIndex(records, commonText) -> Map<id, {nameNorm, fields:string[], generated:string[]}>`
  - `LG.matches(entry, tokens) -> boolean`, `LG.rankTier(entry, tokens) -> 0|1|2`, `LG.search(records, index, tokens) -> records`
  - `tools/normalize.normalize(s) -> str`
  - 성능 표시(PRD 7장, R21): `performance.mark('first-render')`(첫 `render()` 직후), `performance.mark('search-rendered')`(검색어 input 처리 직후). `python tools/perf.py` → 5회 중앙값 출력, 기준(1000ms·50ms)을 넘으면 종료 코드 1

- [ ] **Step 1: 정규화 벡터** — `data/normalize-cases.json`

```json
[
  ["“통계”", "통계"],
  ["영어 논문", "영어논문"],
  ["  JSTOR  ", "jstor"],
  ["ＪＳＴＯＲ", "jstor"],
  ["!!!", ""],
  ["???", ""],
  ["팀플~할&곳+", "팀플할곳"],
  ["「책」 반납", "책반납"],
  ["Web of Science", "webofscience"],
  ["O’Reilly", "oreilly"]
]
```

- [ ] **Step 2: 실패하는 검색 테스트** — `tests/test_search.py`

```python
"""검색 기본 정비(P1-08)."""
import json
import pathlib

from harness import check, test

CASES = json.loads((pathlib.Path(__file__).resolve().parents[1] / 'data' / 'normalize-cases.json').read_text(encoding='utf-8'))


@test()
def t_js_normalize_vectors(site):
    site.open()
    got = site.page.evaluate('cases => cases.map(([i]) => window.LG.normalize(i))', CASES)
    bad = [(i, e, g) for (i, e), g in zip(CASES, got) if e != g]
    check(not bad, f'JS 정규화 불일치 {bad}')


@test()
def t_symbol_only_query(site):
    site.open()
    for q in ('!!!', '???', '“”', '   '):
        site.search(q)
        check(site.page.locator('#empty').is_visible(), f'{q}: 안내 화면 없음')
        check('검색어를 입력하세요' in site.page.inner_text('#empty'), f'{q}: 안내 문구 없음')
        check(site.card_count() == 0, f'{q}: 카드가 보임')


@test()
def t_free_word_zero(site):
    site.open()
    for q in ('무료', '무제한'):
        site.search(q)
        check(site.count() == 0, f'{q}: {site.count()}건(①에서는 0건)')


@test()
def t_remote_noise_removed(site):
    site.open()
    site.search('교외접속')
    ids = site.result_ids()
    check(ids and ids[0] == 'remote', f'교외접속 1위 {ids[:3]}')
    check(site.count() < 10, f'교외접속 {site.count()}건(공통 문장 잡음)')


@test()
def t_quote_and_joined_words(site):
    site.open()
    site.search('“통계”')
    check('stats' in site.result_ids()[:3], f'“통계” 상위 3개 {site.result_ids()[:3]}')
    for q in ('영어논문', '영어 논문'):
        site.search(q)
        check('overseas' in site.result_ids()[:3], f'{q} 상위 3개 {site.result_ids()[:3]}')


@test()
def t_no_cross_field_match(site):
    site.open()
    site.search('앱휴대폰')
    check('mobile' not in site.result_ids(), '필드 경계를 넘어 일치함')


@test(clock=False)  # 가짜 시계는 performance.mark를 기록하지 않는다
def t_perf_marks(site):
    site.open()
    check(site.page.evaluate("performance.getEntriesByName('first-render').length") == 1, 'first-render 표시 없음')
    site.search('통계')
    check(site.page.evaluate("performance.getEntriesByName('search-rendered').length") >= 1, 'search-rendered 표시 없음')


@test()
def t_cleared_query_shows_all(site):
    site.open()
    d = site.data()
    site.search('통계')
    site.search('')
    check(site.count() == sum(len(d[k]) for k in ('services', 'resources', 'directory')), '입력을 지웠는데 처음 목록이 아님')


# 메뉴는 단계 문장을 검색하지 않고, 가이드는 검색한다(PRD 6장 ① 표, S2)
STEP_FIXTURE = r"""(() => { let v; Object.defineProperty(window, 'LIBRARY_GUIDE', { configurable: true, get() { return v; },
  set(x) { x.directory.push(Object.assign({}, x.directory[0], { id: 'menu-fixture', steps: ['zzmenustepzz'] }));
           x.services.push(Object.assign({}, x.services[0], { id: 'guide-fixture', steps: ['zzguidestepzz'] })); v = x; } }); })();"""


@test()
def t_search_fields_by_kind(site):
    site.page.add_init_script(STEP_FIXTURE)
    site.open()
    site.search('zzmenustepzz')
    check(site.count() == 0, '메뉴의 단계 문장이 검색됨')
    site.search('zzguidestepzz')
    check('guide-fixture' in site.result_ids(), '가이드의 단계 문장은 검색돼야 함')
```

`tests/test_regression.py`에서 `d01`·`d03`·`d04` 세 함수를 **삭제**한다(위 테스트로 대체. `d02`는 Task 5에서 이미 지웠다).

Run: `python tests/smoke.py --stage 1 -k test_search`
Expected: 여러 `FAIL`(LG.normalize 없음 등)

- [ ] **Step 3: lib.js에 검색 함수 추가** — `js/lib.js`의 `LG.safeUrl` 아래에 추가

```js
  // 정규화: NFKC → 소문자 → 공백·문장부호·기호 제거(PRD 6장 2번)
  LG.normalize = value => String(value ?? '').normalize('NFKC').toLocaleLowerCase().replace(/[\s\p{P}\p{S}]/gu, '');
  // 단어 나누기 → 단어마다 정규화 → 빈 단어 버림(6장 1~3번)
  LG.tokenize = query => String(query ?? '').trim().split(/\s+/).map(LG.normalize).filter(Boolean);
  // 이 단어는 근거가 확인된 생성 키워드로만 일치(K10). ①에는 생성 키워드가 없다.
  LG.FREE_WORDS = ['무료', '무제한'];

  // ① 검색 필드: 종류마다 다르다(PRD 6장 ① 표, K9). 메뉴는 질문·단계를 검색하지 않는다.
  LG.SEARCH_FIELDS = {
    guide: ['name', 'question', 'description', 'keywords', 'caution', 'steps'],
    resource: ['name', 'description', 'officialDescription', 'keywords', 'subject', 'sourceType', 'caution', 'steps'],
    menu: ['name', 'description', 'keywords', 'menuGroup', 'menuSubgroup', 'caution']
  };

  // ① 검색 색인. 공통 문장(화면 상수 목록과 똑같은 문장·배열 원소)은 색인에서만 뺀다.
  LG.buildIndex = (records, commonText = {}) => {
    const common = new Set([...(commonText.caution || []), ...(commonText.steps || []), ...(commonText.question || [])]);
    const suffix = commonText.keywordSuffix || '';
    const index = new Map();
    for (const r of records) {
      const raw = [];
      for (const field of LG.SEARCH_FIELDS[r.recordKind] || LG.SEARCH_FIELDS.guide) {
        let value = r[field];
        if (field === 'keywords' && r.recordKind === 'menu' && suffix && String(value || '').endsWith(suffix)) {
          value = String(value).slice(0, -suffix.length);
        }
        for (const v of Array.isArray(value) ? value : [value]) if (v && !common.has(v)) raw.push(v);
      }
      index.set(r.id, { nameNorm: LG.normalize(r.name), fields: raw.map(LG.normalize).filter(Boolean), generated: [] });
    }
    return index;
  };

  LG.matches = (entry, tokens) => tokens.every(t => (LG.FREE_WORDS.includes(t)
    ? entry.generated.includes(t)
    : entry.fields.some(f => f.includes(t))));

  // ① 최소 정렬: 이름에 모든 단어 → 일부 단어 → 나머지(같은 단계 안에서는 기존 순서)
  LG.rankTier = (entry, tokens) => {
    const hits = tokens.filter(t => entry.nameNorm.includes(t)).length;
    return hits === tokens.length ? 0 : hits > 0 ? 1 : 2;
  };

  LG.search = (records, index, tokens) => {
    if (!tokens.length) return records.slice();
    return records
      .map((r, i) => ({ r, i, e: index.get(r.id) }))
      .filter(x => x.e && LG.matches(x.e, tokens))
      .map(x => ({ ...x, tier: LG.rankTier(x.e, tokens) }))
      .sort((a, b) => a.tier - b.tier || a.i - b.i)
      .map(x => x.r);
  };
```

- [ ] **Step 4: app.js 검색을 lib.js로 교체**

1. `const normalized = …` 줄을 삭제하고, `const kindName = …` 줄 **아래**에 추가한다. 아래 줄은 `$()`를 부르므로 `const $` 선언보다 뒤여야 한다(앞에 두면 선언 전 접근 오류로 화면 코드 전체가 멈춘다, S1).

```js
  const searchIndex = window.LG.buildIndex(records, window.LIBRARY_GUIDE.commonText);
  const emptyHeading = $('#empty h3').textContent;
  const emptyText = $('#empty p').innerHTML;
```

2. `render()`의 첫 두 문장(terms·currentMatches)을 아래로 바꾼다.

```js
    const tokens = window.LG.tokenize(state.query);
    const invalidQuery = state.query !== '' && tokens.length === 0;  // 공백·기호만 입력(S3)
    currentMatches = invalidQuery ? [] : window.LG.search(records.filter(matchesFilters), searchIndex, tokens);
```

3. `$('#empty').hidden = …` 줄 아래에 추가:

```js
    $('#empty h3').textContent = invalidQuery ? '검색어를 입력하세요' : emptyHeading;
    $('#empty p').innerHTML = invalidQuery ? '글자나 숫자로 된 검색어를 넣어 주세요. 기호만으로는 찾을 수 없어요.' : emptyText;
```

4. 성능 표시(PRD 7장). 파일 끝의 첫 `render();`를 아래로 바꾼다.

```js
  render();
  performance.mark('first-render');
```

검색어 input 처리기를 아래로 바꾼다.

```js
  $('#search-input').addEventListener('input', e => {
    state.query = e.target.value;  // 원문 그대로(공백만 입력도 구분, S3)
    state.limit = 12;
    render();
    performance.mark('search-rendered');
  });
```

5. submit 처리기의 `state.query = $('#search-input').value.trim();`에서 `.trim()`을 뺀다. `render()`의 결과 수 문구 `(state.query ? ' · “' + state.query + '”' : '')`는 `(state.query.trim() ? ' · “' + state.query.trim() + '”' : '')`로 바꾼다.

- [ ] **Step 5: 붙여 쓰는 말 키워드 보강** — `data/services.json`의 `overseas.keywords` 앞에 `"영어 논문 "`을 붙인다.

- [ ] **Step 6: Python 정규화와 벡터 검사** — `tools/normalize.py`

```python
"""JS LG.normalize와 같은 규칙의 Python 구현(검사용)."""
import unicodedata


def normalize(value):
    s = unicodedata.normalize('NFKC', str(value or '')).lower()
    return ''.join(ch for ch in s if not (ch.isspace() or unicodedata.category(ch)[0] in 'PS'))
```

`tests/check_data.py`의 `run_checks` 끝(`return errs` 앞)에 추가하고, 파일 위쪽 import에 `import normalize as norm`을 추가한다(`sys.path`에 tools가 이미 있음).

```python
    cases = json.loads((ROOT / 'data' / 'normalize-cases.json').read_text(encoding='utf-8'))
    for given, expected in cases:
        if norm.normalize(given) != expected:
            errs.append(f'정규화 벡터 불일치(Python): {given!r} → {norm.normalize(given)!r}, 기대 {expected!r}')
    for field in ('caution', 'steps', 'question'):
        for s in (d.get('commonText') or {}).get(field, []):
            if not any(s == r.get(field) or s in (r.get(field) or []) for r in recs):
                errs.append(f'commonText.{field}: 데이터에 없는 문장')
```

성능 측정 도구 `tools/perf.py`(기록용. 게이트에는 넣지 않는다, R21):

```python
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
```

- [ ] **Step 7: 생성·검사·전체 테스트**

Run: `python tools/build_data.py && python tests/check_data.py --stage 1 && python tests/smoke.py --stage 1 --browsers chromium,webkit --modes file,http`
Expected: `문제 0건`, 실패 0(마지막 줄의 두 숫자가 같음) (q04의 대표 검색 수치 그대로 유지). 이어서 `python tools/perf.py`를 한 번 돌려 본다(기준 안이면 종료 코드 0. 넘으면 원인을 Task 14의 QA 기록에 남긴다).

- [ ] **Step 8: 커밋**

```bash
git add js/lib.js js/app.js data/ data.js tools/normalize.py tools/perf.py tests/
git commit -m "v3①: 검색 기본 정비 (P1-08)" -m "단어별 정규화·빈 단어 처리, 필드별 비교, 공통 문장 색인 제외, 무료·무제한 규칙, 최소 정렬, JS·Python 정규화 벡터 공유, 성능 표시와 측정 도구" -m "Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
```

---

### Task 7: 최소 공지 기능 (P1-06)

**Files:**
- Create: `tests/test_notice.py`
- Modify: `data/notices.json`, `js/lib.js`, `js/app.js`, `index.html`, `styles.css`, `tests/check_data.py`, `tests/helpers.py`

**Interfaces:**
- Produces:
  - `LG.todayLocal(date = new Date()) -> 'YYYY-MM-DD'`, `LG.isActiveOn(item, today) -> boolean`, `LG.activeNotices(notices, today, taskId?) -> notice[]`
  - `notices.json` 항목: `{id, text, link, source, checkedAt, startsOn, endsOn, taskIds}`
  - DOM: `#notices`(홈 공지 영역), 상세의 `.detail-notices`
  - `app.js`: `todayNow()`(그릴 때마다 오늘 날짜를 다시 계산, S14), `noticeHtml(n)`, `renderNotices()`(`render()` 맨 앞에서 호출)
  - `tests/helpers.py`: `TEST_NOTICE`(테스트용 공지 하나), `notices_fixture(items) -> str`(notices만 바꾸는 초기화 스크립트). Task 10도 쓴다

- [ ] **Step 1: 실패하는 공지 테스트** — `tests/test_notice.py`

```python
"""공지: 기간 안에만 보이고, 첫날·마지막 날 포함, 다음 날 숨김. 테스트용 공지(픽스처)를 주입한다(K2)."""
from harness import check, test
from helpers import TEST_NOTICE, notices_fixture

FIXTURE = notices_fixture([TEST_NOTICE])


def at(site, day):
    site.page.clock.set_fixed_time(f'{day}T10:00:00+09:00')
    site.page.add_init_script(FIXTURE)
    site.open()
    return site.page.locator('#notices').is_visible()


@test()
def t_notice_boundaries(site):
    for day, visible in (('2026-10-07', True), ('2026-10-15', True), ('2026-10-26', True)):
        check(at(site, day) == visible, f'{day}: 보임={visible} 이어야 함')


@test()
def t_notice_hidden_after(site):
    check(not at(site, '2026-10-27'), '종료 다음 날에도 보임')


@test()
def t_notice_on_card(site):
    at(site, '2026-10-15')
    site.open_any('hours')
    check('테스트 공지' in site.page.inner_text('#detail-content .detail-notices'), '상세에 공지 없음')


@test()
def t_today_local_midnight(site):
    site.page.clock.set_fixed_time('2026-10-27T00:30:00+09:00')
    site.open()
    check(site.page.evaluate('window.LG.todayLocal()') == '2026-10-27', '한국 시간 자정 직후 날짜가 전날로 계산됨')


@test()
def t_notice_rechecked_after_midnight(site):
    site.page.clock.set_fixed_time('2026-10-26T23:59:00+09:00')
    site.page.add_init_script(FIXTURE)
    site.open()
    check(site.page.locator('#notices').is_visible(), '종료일 밤에는 보여야 함')
    site.page.clock.set_fixed_time('2026-10-27T00:01:00+09:00')
    site.search('통계')  # 다시 그리기
    check(not site.page.locator('#notices').is_visible(), '자정을 넘긴 뒤 다시 그렸는데 공지가 남음(S14)')
```

`tests/helpers.py` 맨 위 import에 `import json`을 더하고, 파일 끝에 공지 픽스처 도우미를 추가한다(Task 10도 쓴다).

```python
TEST_NOTICE = {'id': 'fixture-exam', 'text': '테스트 공지: 열람실 24시간 개방',
               'link': 'https://lib.jejunu.ac.kr/#/bbs/notice/6789', 'source': 'https://lib.jejunu.ac.kr/#/bbs/notice/6789',
               'checkedAt': '2026-10-13', 'startsOn': '2026-10-07', 'endsOn': '2026-10-26', 'taskIds': ['hours']}


def notices_fixture(items):
    """window.LIBRARY_GUIDE 대입을 가로채 notices만 바꾸는 초기화 스크립트(file://에서도 동작)."""
    return ("(() => { let v; Object.defineProperty(window, 'LIBRARY_GUIDE', { configurable: true, get() { return v; },"
            " set(x) { x.notices = " + json.dumps(items, ensure_ascii=False) + "; v = x; } }); })();")
```

Run: `python tests/smoke.py --stage 1 -k test_notice`
Expected: `FAIL`(#notices 없음)

- [ ] **Step 2: lib.js에 날짜·공지 함수 추가**

```js
  // 기기 로컬 날짜 'YYYY-MM-DD'. toISOString은 UTC라 쓰지 않는다(PRD 5장 날짜 규칙).
  LG.todayLocal = (d = new Date()) => d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-'
    + String(d.getDate()).padStart(2, '0');
  // 시작·종료일 당일 포함. 'YYYY-MM-DD' 문자열 비교.
  LG.isActiveOn = (item, today) => (!item.startsOn || item.startsOn <= today) && (!item.endsOn || today <= item.endsOn);
  LG.activeNotices = (notices, today, taskId) => (notices || [])
    .filter(n => LG.isActiveOn(n, today) && (!taskId || (n.taskIds || []).includes(taskId)));
```

- [ ] **Step 3: 화면** — `index.html`의 `<main id="top">` 바로 다음에 추가

```html
<section id="notices" class="notices" aria-label="지금 이 시기 공지" hidden></section>
```

`js/app.js`의 `$('#checked-at').textContent = …` 아래에 추가:

```js
  // 오늘 날짜는 그릴 때마다 다시 계산한다(열어 둔 채 자정을 넘겨도 다음 조작 때 맞게, S14)
  const todayNow = () => window.LG.todayLocal();
  const noticeHtml = n => '<li><strong>' + escape(n.text) + '</strong> <span class="notice-period">'
    + escape(n.startsOn.replaceAll('-', '.')) + ' ~ ' + escape(n.endsOn.replaceAll('-', '.')) + '</span>'
    + (safeUrl(n.link) ? ' <a href="' + escape(safeUrl(n.link)) + '" target="_blank" rel="noopener noreferrer">공지 보기 ↗</a>' : '')
    + '<span class="notice-source">확인일 ' + escape(n.checkedAt.replaceAll('-', '.')) + '</span></li>';

  function renderNotices() {
    const items = window.LG.activeNotices(window.LIBRARY_GUIDE.notices, todayNow());
    $('#notices').innerHTML = items.length
      ? '<h2 class="sr-only">지금 이 시기 공지</h2><ul>' + items.map(noticeHtml).join('') + '</ul>' : '';
    $('#notices').hidden = items.length === 0;
  }
```

`render()`의 맨 앞에 `renderNotices();`를 넣는다.

`openDetail()`의 `$('#detail-content').innerHTML = …` 문자열에서 `<p class="detail-summary">` 바로 앞에 끼운다:

```js
      + (() => { const ns = window.LG.activeNotices(window.LIBRARY_GUIDE.notices, todayNow(), id);
        return ns.length ? '<div class="detail-notices"><h3>지금 이 시기</h3><ul>' + ns.map(noticeHtml).join('') + '</ul></div>' : ''; })()
```

`styles.css` 끝에 추가:

```css
.notices {
  margin: 16px auto 0;
  max-width: 1180px;
  padding: 12px 18px;
  border: 1px solid var(--green);
  border-radius: var(--radius);
  background: var(--soft);
}
.notices ul,
.detail-notices ul {
  margin: 0;
  padding-left: 18px;
}
.notice-period,
.notice-source {
  color: var(--muted);
  font-size: 0.9em;
  margin-left: 6px;
}
```

- [ ] **Step 4: 실제 공지 데이터** — `data/notices.json`

```json
[
  {
    "id": "exam-2026-2-midterm",
    "text": "중간시험 대비 중앙도서관 열람실 24시간 개방(중앙디지털도서관·제주자료실은 기존 시간)",
    "link": "https://lib.jejunu.ac.kr/#/bbs/notice/6789",
    "source": "https://lib.jejunu.ac.kr/#/bbs/notice/6789",
    "checkedAt": "2026-10-13",
    "startsOn": "2026-10-07",
    "endsOn": "2026-10-26",
    "taskIds": ["hours"]
  }
]
```

이 공지는 2026-10-26에 끝난다. 데이터 검사는 실제 날짜로 돌기 때문에 10/27부터는 게이트가 실패한다. 그때는 이 항목을 지우거나 다음 공지로 바꾼 뒤 다시 생성·커밋한다. `--today`로 우회하지 않는다(R15). 기능 테스트는 픽스처 공지를 쓰므로 영향이 없다.

- [ ] **Step 5: check_data에 공지 검사** — `run_checks`의 `return errs` 앞에 추가

```python
    date_re = re.compile(r'^\d{4}-\d{2}-\d{2}$')
    for n in d.get('notices') or []:
        nid = n.get('id', '?')
        for f in ('id', 'text', 'checkedAt', 'startsOn', 'endsOn'):
            if not n.get(f):
                errs.append(f'notice {nid}: {f} 없음')
        if not (https(n.get('link')) and https(n.get('source'))):
            errs.append(f'notice {nid}: link·source가 https 아님')
        if not all(date_re.match(n.get(f, '')) for f in ('checkedAt', 'startsOn', 'endsOn')):
            errs.append(f'notice {nid}: 날짜 형식 YYYY-MM-DD')
        elif n['startsOn'] > n['endsOn']:
            errs.append(f'notice {nid}: 시작일 > 종료일')
        elif n['endsOn'] < today:
            errs.append(f'notice {nid}: 기간이 지났습니다({n["endsOn"]}). 공지를 지우거나 갱신하세요(K18)')
        for t in n.get('taskIds') or []:
            if t not in have:
                errs.append(f'notice {nid}: 없는 taskId {t}')
```

- [ ] **Step 6: 생성·검사·테스트**

Run: `python tools/build_data.py && python tests/check_data.py --stage 1 && python tests/check_data.py --stage 1 --today 2026-10-27; python tests/smoke.py --stage 1 --browsers chromium,webkit --modes file,http`
Expected: 첫 검사 `문제 0건`, 두 번째(10/27) `ERROR notice … 기간이 지났습니다`, 스모크 실패 0(마지막 줄의 두 숫자가 같음)

- [ ] **Step 7: 커밋**

```bash
git add js/lib.js js/app.js index.html styles.css data/notices.json data.js tests/
git commit -m "v3①: 최소 공지 기능 (P1-06)" -m "기기 로컬 날짜·당일 포함 공지 표시, 카드 상세 공지, 기간 지난 공지 검사, 날짜 고정·픽스처 테스트" -m "Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
```

---

### Task 8: 상세의 마지막 한 걸음과 조건 표시 (P1-07 화면, P1-11)

**Files:**
- Create: `tests/test_detail.py`
- Modify: `js/app.js`(`card`, `openDetail`), `styles.css`, `data/services.json`(목록형 가이드 `findHint`), `tests/test_regression.py`, `tests/check_data.py`

**Interfaces:**
- Consumes: `facts`, `eligibilityNote`, `costNote`, `findHint`(이 작업에서 추가), `LG.activeNotices`, `todayNow()`·`noticeHtml()`(Task 7)
- Produces: 상세 DOM 계약. 위에서 아래 순서로(PRD P1-07·K21: 요약 바로 아래에 나머지 예외, 접지 않음):
  1. `h2#detail-title`, `.detail-question`
  2. `.detail-top`: `a.primary[data-official]`(공식 버튼), `.find-hint`(목록형일 때)
  3. `dl.detail-conditions`(대상·비용·인증·로그인), `.detail-channel`(이용 경로 한 줄, S6)
  4. `.detail-notices`(지금 이 시기, 있을 때)
  5. `.detail-exceptions`: "이용 전 확인할 점" = caution + 위치가 아닌 사실 전부(인증·시간 포함, 사실마다 확인일·출처 링크) `ul.detail-facts-list`
  6. `.detail-location`(위치 사실, 있을 때)
  7. `.detail-summary`, (자료) `.official-excerpt`, `ol.detail-steps`
  8. `.material-list`, `.related`
  9. `.detail-disclaimer`(1개)
- 대상 칸의 기본값은 "공식 안내에서 확인"이다. 학부/대학원 분류(`audience`)를 이용 자격처럼 쓰지 않는다(R10, S6).

- [ ] **Step 1: 실패하는 상세 테스트** — `tests/test_detail.py`

```python
"""상세: 공식 버튼과 조건이 대화상자의 보이는 첫 화면 안, 예외는 요약 바로 아래, 찾는 방법, 위치, 면책 1회."""
from harness import check, test

# 요소가 화면 높이와 대화상자의 보이는 영역 양쪽 안에 있는지(대화상자는 높이 제한 + 자체 스크롤이 있다, S7)
VISIBLE = """sel => { const el = document.querySelector(sel); const dlg = document.querySelector('#detail-dialog');
  if (!el || !dlg) return false; const r = el.getBoundingClientRect(); const d = dlg.getBoundingClientRect();
  return r.height > 0 && r.top >= Math.max(0, d.top) && r.bottom <= Math.min(window.innerHeight, d.bottom); }"""

ORDER = """() => { const els = ['.detail-top', '.detail-conditions', '.detail-exceptions', '.detail-steps']
    .map(s => document.querySelector('#detail-content ' + s));
  if (els.some(e => !e)) return 'missing ' + els.map(e => !!e).join(',');
  for (let i = 1; i < els.length; i++) {
    if (!(els[i - 1].compareDocumentPosition(els[i]) & Node.DOCUMENT_POSITION_FOLLOWING)) return 'order ' + i;
  }
  return 'ok'; }"""


def visible_in_dialog(site, selector):
    return site.page.evaluate(VISIBLE, selector)


@test()
def t_official_button_above_fold_desktop(site):
    site.open()
    for rid in ('stats', 'group', 'er-044', 'remote'):
        site.open_any(rid)
        check(visible_in_dialog(site, '#detail-content a.primary[data-official]'), f'{rid}: 공식 버튼이 첫 화면 밖')
        site.close_detail()


@test(viewport='mobile')
def t_detail_above_fold_mobile(site):
    site.open()
    for rid, must in (('group', '재학생·교직원'), ('maker', '재학생·교직원'), ('locker', '재학생'), ('delivery', '장애인'),
                      ('er-057', '초대링크'), ('er-085', '학내 IP')):
        site.open_any(rid)
        for sel in ('#detail-content a.primary[data-official]', '.detail-conditions'):
            check(visible_in_dialog(site, sel), f'{rid} {sel}: 390×844 첫 화면 밖')
        check(must in site.page.inner_text('.detail-conditions'), f'{rid}: 조건 요약에 "{must}" 없음')
        site.close_detail()
    for rid in ('stats', 'er-044'):
        site.open_any(rid)
        check(visible_in_dialog(site, '.find-hint'), f'{rid}: 찾는 방법이 첫 화면 밖')
        site.close_detail()


@test()
def t_detail_order_exceptions_below_summary(site):
    site.open()
    site.open_any('group')
    order = site.page.evaluate(ORDER)
    check(order == 'ok', f'상세 순서(공식 버튼 → 조건 → 확인할 점 → 이용 방법)가 아님: {order}')
    check(site.page.locator('#detail-content details').count() == 0, '예외를 접어 두면 안 됨(K21)')
    text = site.page.inner_text('.detail-exceptions')
    check('30분' in text and '자동 취소' in text, f'예약 규칙이 확인할 점에 없음: {text[:80]}')


@test()
def t_find_hint_for_list_links(site):
    site.open()
    site.open_any('er-044')
    hint = site.page.inner_text('.find-hint')
    check('JSTOR Collection' in hint and '검색 칸' in hint, f'자료 찾는 방법: {hint}')
    site.close_detail()
    site.open_any('stats')
    check('Statista' in site.page.inner_text('.find-hint'), '가이드 찾는 방법 없음')


@test()
def t_location_channel_and_disclaimer_once(site):
    site.open()
    site.open_any('print')
    loc = site.page.inner_text('.detail-location')
    check('3층 3열람실' in loc and '미디어라운지' in loc, f'위치 {loc}')
    check(site.page.locator('#detail-content .detail-disclaimer').count() == 1, '면책 문구 1개가 아님')
    check(site.page.locator('#detail-content .kind-note, #detail-content .material-note').count() == 0, '중복 면책 남음')
    site.close_detail()
    site.open_any('group')
    check('키오스크' in site.page.inner_text('.detail-channel'), '이용 경로(앱·키오스크)가 상세에 없음')


@test()
def t_auth_fact_with_source(site):
    site.open()
    site.open_any('er-085')
    check('학내 IP' in site.page.inner_text('.detail-conditions'), 'WSJ 인증 예외가 조건 요약에 없음')
    item = site.page.locator('.detail-exceptions li', has_text='학내 IP')
    check(item.count() == 1 and item.locator('a').count() == 1, '인증 사실의 출처 링크가 확인할 점에 없음')


@test()
def t_eligibility_default_and_unknown(site):
    site.open()
    site.open_any('thesis-submit')  # 대학원 대상 가이드지만 eligibilityNote가 없다
    check('공식 안내에서 확인' in site.page.inner_text('.detail-conditions'), '대상 기본값이 "공식 안내에서 확인"이 아님')
    site.close_detail()
    site.open_any('seat')
    check('미확인' in site.page.inner_text('.detail-conditions'), '일반열람실 대상 미확인 표시 없음')


@test()
def t_card_condition_badges(site):
    site.open()
    site.search('그룹스터디룸')
    check(site.page.locator('.service-card .badge', has_text='재학생·교직원').count() >= 1, '카드 대상 배지 없음')
    check(site.page.locator('.badge', has_text='세부 조건 확인').count() == 0, "'세부 조건 확인' 배지 남음")
```

`tests/test_regression.py`에서 `d07_official_button_at_end`와 `d10_vague_badge`를 **삭제**한다(위 테스트로 대체).

Run: `python tests/smoke.py --stage 1 -k test_detail`
Expected: `FAIL`

- [ ] **Step 2: 목록형 가이드의 찾는 방법** — `data/services.json`에 `findHint` 추가

| id | findHint |
|---|---|
| `stats` | `"전자정보원 목록의 검색 칸에 Statista 또는 KSDC를 입력하세요."` |
| `overseas` | `"전자정보원 목록의 검색 칸에 ScienceDirect, JSTOR Collection, ProQuest Central Premium 같은 이름을 입력하세요."` |
| `domestic` | `"전자정보원 목록의 검색 칸에 DBPIA, KISS, 스콜라 같은 이름을 입력하세요."` |
| `business` | `"전자정보원 목록의 검색 칸에 NICE bizLINE 또는 Value-Search를 입력하세요."` |
| `discipline` | `"전자정보원 목록의 검색 칸에 IEL(IEEE/IET), CINAHL Complete, Westlaw 같은 전공 서비스 이름을 입력하세요."` |
| `culture` | `"전자정보원 목록의 검색 칸에 Naxos Music Library, The New York Times in Education 같은 이름을 입력하세요."` |
| `ebook` | `"전자책 목록에서 제주대학교 전자책(알라딘·교보문고·북레일·북큐브)이나 예스24 크레마클럽을 고르세요."` |
| `oreilly` | `"전자책 목록의 검색 칸에 O'Reilly for Higher Education을 입력하세요."` |

근거: 공식 전자정보원 목록과 전자책 목록 위쪽에 "전자정보원을 검색하세요." 입력칸이 있다(official_facts 7장). 예시 이름은 데이터에 실제로 있는 이름만 쓴다(R12. RISS와 약칭 "NYT"는 데이터에 없다). O'Reilly는 전자책 목록 원본(`docs/ebooks-raw.json`)에 있다. 넣은 뒤 이름이 모두 있는지 확인한다.
Run: `python -c "import json;n=' '.join(r['name'] for r in json.load(open('data/resources.json',encoding='utf-8')));print([k for k in ('Statista','KSDC','ScienceDirect','JSTOR Collection','ProQuest Central Premium','DBPIA','KISS','스콜라','NICE bizLINE','Value-Search','IEL','CINAHL Complete','Westlaw','Naxos Music Library','The New York Times in Education','제주대학교 전자책','크레마클럽') if k not in n])"`
Expected: `[]`

`tests/check_data.py`의 `for r in recs:` 반복 안에 목록형 가이드 검사를 추가한다(P1-11. ②의 `official.kind=list` 검사를 ① 필드로 미리 한다).

```python
        if r.get('recordKind') == 'guide' and re.search(r'#/search/er(-ebook)?$', r.get('source', '')) and not r.get('findHint'):
            errs.append(f'{rid}: 목록형 링크인데 findHint 없음(P1-11)')
```

- [ ] **Step 3: card() 배지 교체** — `js/app.js`의 `card()`에서 가이드·메뉴 배지 식을 아래로 바꾼다

```js
      : (s.channel ? '<span class="badge">' + escape(s.channel) + '</span>' : '')
        + (s.eligibilityNote ? '<span class="badge target">' + escape(s.eligibilityNote) + '</span>' : '')
        + (s.costNote ? '<span class="badge">' + escape(s.costNote) + '</span>' : '');
```

- [ ] **Step 4: openDetail() 재구성** — `openDetail` 함수 전체를 아래로 바꾼다

```js
  const isListUrl = url => /#\/search\/er(-ebook)?$/.test(url || '');

  function findHint(s) {
    if (s.findHint) return s.findHint;
    if (s.recordKind === 'resource' && isListUrl(s.source)) return "공식 목록 위쪽의 검색 칸에 '" + s.name + "'을(를) 입력하세요.";
    return '';
  }

  function factHtml(f) {
    return '<li>' + escape(f.text) + ' <span class="fact-source">(' + escape(String(f.checkedAt).replaceAll('-', '.'))
      + (safeUrl(f.source) ? ', <a href="' + escape(safeUrl(f.source)) + '" target="_blank" rel="noopener noreferrer">출처</a>' : '')
      + ')</span></li>';
  }

  function openDetail(id) {
    const s = byId(id);
    if (!s) return;
    const resource = s.recordKind === 'resource';
    const menu = s.recordKind === 'menu';
    $('#detail-category').textContent = kindName(s.recordKind) + ' · ' + (resource ? s.subject : menu ? s.menuGroup : categoryName(s.category));
    const sourceLabel = resource
      ? (s.source.endsWith('er-ebook') ? '공식 전자책 목록 열기' : '공식 전자정보원 목록 열기')
      : menu ? '공식 메뉴로 이동하기' : '공식 안내 열기';
    const url = safeUrl(s.source);
    const hint = findHint(s);
    const facts = s.facts || [];
    const auth = facts.filter(f => f.kind === 'auth').map(f => f.text);
    const locations = facts.filter(f => f.kind === 'location');
    const exceptions = facts.filter(f => f.kind !== 'location');
    const notices = window.LG.activeNotices(window.LIBRARY_GUIDE.notices, todayNow(), id);
    const materials = (s.materials || []).filter(m => safeUrl(m.url));
    const related = (relatedMap[id] || []).filter(byId);

    $('#detail-content').innerHTML = '<h2 id="detail-title">' + escape(s.name) + '</h2>'
      + '<p class="detail-question">' + escape(resource ? s.subject + ' · ' + s.sourceType : menu ? s.description : s.question) + '</p>'
      + '<div class="detail-top">'
      + (url ? '<a class="primary" data-official href="' + escape(url) + '" target="_blank" rel="noopener noreferrer">' + sourceLabel + ' ↗</a>'
        : '<p>공식 링크를 확인할 수 없어요.</p>')
      + (hint ? '<p class="find-hint">' + escape(hint) + '</p>' : '')
      + '</div>'
      + '<dl class="detail-conditions">'
      + '<div><dt>대상</dt><dd>' + escape(s.eligibilityNote || '공식 안내에서 확인') + '</dd></div>'
      + '<div><dt>비용</dt><dd>' + escape(s.costNote || s.cost) + '</dd></div>'
      + '<div><dt>인증·로그인</dt><dd>' + escape([s.login, ...auth].filter(Boolean).join(' · ')) + '</dd></div>'
      + '</dl>'
      + (s.channel ? '<p class="detail-channel">이용 경로: ' + escape(s.channel) + '</p>' : '')
      + (notices.length ? '<div class="detail-notices"><h3>지금 이 시기</h3><ul>' + notices.map(noticeHtml).join('') + '</ul></div>' : '')
      + '<div class="detail-exceptions"><h3>이용 전 확인할 점</h3><p class="detail-warning">' + escape(s.caution)
      + (s.duplicateCount > 1 ? '<br>원목록의 같은 이름 ' + s.duplicateCount + '개 항목을 합쳤습니다.' : '') + '</p>'
      + (exceptions.length ? '<ul class="detail-facts-list">' + exceptions.map(factHtml).join('') + '</ul>' : '') + '</div>'
      + (locations.length ? '<div class="detail-location"><h3>위치</h3><ul>' + locations.map(factHtml).join('') + '</ul></div>' : '')
      + '<p class="detail-summary">' + escape(s.description) + '</p>'
      + (resource ? '<h3>공식 목록의 설명</h3><div class="official-excerpt">' + escape(s.officialDescription) + '</div>' : '')
      + '<h3>' + (menu ? '이 메뉴를 찾으려면' : '이렇게 이용해요') + '</h3><ol class="detail-steps">'
      + s.steps.map(step => '<li>' + escape(step) + '</li>').join('') + '</ol>'
      + (materials.length ? '<h3>공식 제공 매뉴얼·관련 링크</h3><div class="material-list">' + materials.map(m => '<a href="'
        + escape(safeUrl(m.url)) + '" target="_blank" rel="noopener noreferrer">' + escape(m.label) + ' ↗</a>').join('') + '</div>' : '')
      + (related.length ? '<h3>함께 보면 좋은 안내</h3><div class="related">' + related.map(key => '<button type="button" data-open="'
        + escape(key) + '">' + escape(byId(key).name) + '</button>').join('') + '</div>' : '')
      + '<p class="detail-disclaimer">공개 안내 확인일 ' + escape(s.checkedAt) + ' · 비공식 학생용 가이드. 학교 계정·개인정보를 수집하지 않아요. '
      + '원문 표기에 오류·과거 정보가 있을 수 있으니 이용 직전 공식 안내를 확인하세요.</p>';
    if (!dialog.open) dialog.showModal();
    dialog.scrollTop = 0;
    $('#close-dialog').focus();
  }
```

Task 7에서 `openDetail`에 넣었던 공지 조각은 이 교체로 사라진다(공지는 같은 자리의 `.detail-notices`로 들어감).

- [ ] **Step 5: 스타일** — `styles.css` 끝에 추가

```css
.detail-top {
  display: grid;
  gap: 6px;
  margin: 10px 0 12px;
}
.detail-top .primary {
  justify-self: start;
}
.find-hint {
  margin: 0;
  color: var(--muted);
  font-size: 0.92em;
}
.detail-conditions {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
  margin: 0 0 8px;
}
.detail-conditions div {
  background: var(--soft);
  border-radius: 10px;
  padding: 8px 10px;
}
.detail-conditions dt {
  font-size: 0.82em;
  color: var(--muted);
}
.detail-conditions dd {
  margin: 2px 0 0;
  font-weight: 600;
}
.detail-channel {
  margin: 0 0 12px;
  color: var(--muted);
  font-size: 0.9em;
}
.detail-facts-list {
  margin: 8px 0 0;
  padding-left: 18px;
}
.fact-source,
.detail-disclaimer {
  color: var(--muted);
  font-size: 0.85em;
}
@media (max-width: 560px) {
  .detail-conditions {
    grid-template-columns: 1fr;
  }
}
```

- [ ] **Step 6: 생성·테스트**

Run: `python tools/build_data.py && python tests/check_data.py --stage 1 && python tests/smoke.py --stage 1 --browsers chromium,webkit --modes file,http`
Expected: `문제 0건`, 실패 0(마지막 줄의 두 숫자가 같음). `t_detail_above_fold_mobile`이 실패하면 `.detail-question`·`.detail-top`·조건 칸의 여백을 줄여 첫 화면에 맞춘다. 조건 요약과 예외는 접지 않는다(K21).

- [ ] **Step 7: 커밋**

```bash
git add js/app.js styles.css data/ data.js tests/
git commit -m "v3①: 상세의 마지막 한 걸음과 조건 표시 (P1-07, P1-11)" -m "공식 버튼·찾는 방법(공식 목록 검색 칸 기준)·대상/비용/인증 요약을 위로, 이용 경로 한 줄, 예외(주의·출처 있는 사실)는 요약 바로 아래, 위치 표시, 면책 1회, 카드 조건 배지, 목록형 가이드 findHint 검사, 대화상자 보이는 영역 기준 검사" -m "Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
```

---

### Task 9: 필터·검색어 유지 (P1-09)

**Files:**
- Create: `tests/test_filters.py`
- Modify: `js/app.js`, `index.html`, `styles.css`, `tests/test_regression.py`

**Interfaces:**
- Produces: DOM `#active-filters`(필터 칩 `button[data-clear]`), `#empty-clear-filters`(`data-widen="true|false"`). `app.js` 내부 `activeFilters() -> [{key, label}]`, `clearFilter(key)`, `recoveryCounts() -> {sameScope, allScopes}`
- 0건 복구 안내(S4): 같은 범위에서 필터만 풀었을 때 결과가 있으면 "필터를 풀면 N건"(범위 유지). 그래도 없고 다른 범위에 있으면 "다른 범위까지 보면 N건"(버튼이 범위도 '전체'로). 안내한 N은 버튼을 누른 뒤의 결과 수와 같아야 한다.

- [ ] **Step 1: 실패하는 필터 테스트** — `tests/test_filters.py`

```python
"""필터·검색어 유지(P1-09)."""
import re

from harness import check, test


def recovery_n(site):
    text = site.page.inner_text('#empty')
    m = re.search(r'(\d+)건', text)
    return text, int(m.group(1)) if m else None


@test()
def t_category_tab_keeps_query(site):
    site.open()
    site.search('통계')
    site.category_tab('assignment')
    check(site.query_value() == '통계', '상황 탭이 검색어를 지움')
    check('stats' in site.result_ids(), '검색어+상황 결과에 통계 없음')


@test()
def t_active_filter_chips(site):
    site.open()
    site.category_tab('space')
    site.select('audience', 'undergrad')
    chips = site.page.eval_on_selector_all('#active-filters [data-clear]', 'els => els.map(e => e.dataset.clear)')
    check(set(chips) >= {'category', 'audience'}, f'칩 {chips}')
    site.page.click('#active-filters [data-clear="category"]')
    site.page.wait_for_timeout(80)
    check(site.page.get_attribute('#category-tabs [data-category="all"]', 'aria-pressed') == 'true', '칩으로 상황 해제 안 됨')


@test()
def t_hidden_filter_zero_result_explains(site):
    site.open()
    site.category_tab('space')
    site.search('교외접속')
    check(site.count() == 0, '전제: 공부 공간 안에서 0건')
    text, n = recovery_n(site)
    check('필터를 풀면' in text and n, f'0건 이유 안내 없음: {text}')
    site.page.click('#empty-clear-filters')
    site.page.wait_for_timeout(100)
    check(site.count() == n and 'remote' in site.result_ids(), f'안내한 {n}건과 해제 뒤 {site.count()}건이 다름')


@test()
def t_zero_result_other_scope(site):
    site.open()
    site.category_card('books')   # 상황 카드는 범위를 '이용 가이드'로 바꾼다
    site.search('CAS BioFinder')  # 자료에만 있는 말
    check(site.count() == 0, '전제: 가이드 범위에서 0건')
    text, n = recovery_n(site)
    check('다른 범위까지 보면' in text and n, f'다른 범위 안내 없음: {text}')
    site.page.click('#empty-clear-filters')
    site.page.wait_for_timeout(100)
    check(site.count() == n and 'er-096' in site.result_ids(), f'안내한 {n}건과 해제 뒤 {site.count()}건이 다름')


@test()
def t_zero_result_keeps_chosen_scope(site):
    site.open()
    site.scope('resource')
    site.select('resource-subject', '통계·기업')
    site.search('JSTOR')
    check(site.count() == 0, '전제: 통계·기업 분야에서 JSTOR 0건')
    text, n = recovery_n(site)
    check('필터를 풀면' in text and n == 1, f'같은 범위 안내가 아님: {text}')
    site.page.click('#empty-clear-filters')
    site.page.wait_for_timeout(100)
    check(site.result_ids() == ['er-044'], f'자료 범위를 유지한 채 JSTOR가 나와야 함: {site.result_ids()}')
    check(site.page.get_attribute('#scope-tabs [data-scope="resource"]', 'aria-pressed') == 'true', '고른 범위가 바뀜')


@test()
def t_scope_change_resets_hidden_filters(site):
    site.open()
    site.scope('resource')
    site.select('resource-subject', '통계·기업')
    site.scope('all')
    site.scope('resource')
    check(site.count() == 98, f'숨은 분야 필터가 남음: {site.count()}')
```

`tests/test_regression.py`에서 `d06_category_tab_clears_query`를 **삭제**한다.

Run: `python tests/smoke.py --stage 1 -k test_filters`
Expected: `FAIL`

- [ ] **Step 2: 화면 골격** — `index.html`의 `<div class="result-heading">` 바로 앞에 추가

```html
<div id="active-filters" class="active-filters" aria-label="적용 중인 필터" hidden></div>
```

`#empty`의 `<button class="primary" id="empty-reset">…</button>` 앞에 추가:

```html
<button type="button" class="secondary" id="empty-clear-filters" hidden>필터 모두 해제</button>
```

- [ ] **Step 3: app.js 로직**

1. 클릭 위임의 `[data-category]` 처리에서 `state.query = '';`와 `$('#search-input').value = '';` 두 줄을 **상황 카드일 때만** 실행하도록 `if (cat.classList.contains('category-card')) { … }` 블록 안으로 옮긴다.
2. `changeScope`를 아래로 바꾼다(숨은 필터 초기화).

```js
  function changeScope(scope) {
    if (scope !== state.scope) {
      Object.assign(state, { subject: 'all', sourceType: 'all', access: 'all', menuGroup: 'all' });
      ['resource-subject', 'resource-type', 'resource-access', 'menu-group'].forEach(sid => { $('#' + sid).value = 'all'; });
    }
    state.scope = scope;
    state.category = 'all';
    state.limit = 12;
    render();
  }
```

3. `render()` 위에 추가:

```js
  const FILTER_LABELS = { audience: { undergrad: '학부생' } };

  function activeFilters() {
    const list = [];
    if (state.category !== 'all' && state.scope !== 'resource' && state.scope !== 'menu') {
      list.push({ key: 'category', label: categoryName(state.category) });
    }
    if (state.audience !== 'all') list.push({ key: 'audience', label: FILTER_LABELS.audience[state.audience] || state.audience });
    if (state.scope === 'resource') {
      for (const key of ['subject', 'sourceType', 'access']) if (state[key] !== 'all') list.push({ key, label: state[key] });
    }
    if (state.scope === 'menu' && state.menuGroup !== 'all') list.push({ key: 'menuGroup', label: state.menuGroup });
    return list;
  }

  const SELECT_OF = { audience: 'audience', subject: 'resource-subject', sourceType: 'resource-type', access: 'resource-access', menuGroup: 'menu-group' };

  function clearFilter(key) {
    state[key] = 'all';
    if (SELECT_OF[key]) $('#' + SELECT_OF[key]).value = 'all';
  }

  // 0건일 때 복구 안내용 수: 같은 범위에서 필터만 풀었을 때, 범위까지 풀었을 때(S4)
  function recoveryCounts() {
    const tokens = window.LG.tokenize(state.query);
    const count = list => (tokens.length ? window.LG.search(list, searchIndex, tokens).length : list.length);
    return {
      sameScope: count(records.filter(r => state.scope === 'all' || r.recordKind === state.scope)),
      allScopes: count(records)
    };
  }
```

4. `render()` 끝(마지막 `querySelectorAll(...)` 두 줄 뒤)에 추가:

```js
    const filters = activeFilters();
    $('#active-filters').innerHTML = filters.map(f => '<button type="button" data-clear="' + escape(f.key) + '">'
      + escape(f.label) + ' <span aria-hidden="true">×</span><span class="sr-only"> 필터 해제</span></button>').join('')
      + (filters.length > 1 ? '<button type="button" data-clear="all">모두 해제</button>' : '');
    $('#active-filters').hidden = filters.length === 0;
    let recovery = null;
    if (currentMatches.length === 0 && !invalidQuery) {
      const c = recoveryCounts();
      if (filters.length && c.sameScope > 0) recovery = { n: c.sameScope, widen: false };
      else if (c.allScopes > 0 && (filters.length || state.scope !== 'all')) recovery = { n: c.allScopes, widen: true };
    }
    $('#empty-clear-filters').hidden = !recovery;
    if (recovery) {
      $('#empty p').textContent = recovery.widen
        ? '지금 범위와 필터에서는 결과가 없어요. 다른 범위까지 보면 ' + recovery.n + '건이 있어요.'
        : '적용 중인 필터 때문에 결과가 없어요. 필터를 풀면 ' + recovery.n + '건이 있어요.';
      $('#empty-clear-filters').textContent = recovery.widen ? '전체 범위에서 보기' : '필터 모두 해제';
      $('#empty-clear-filters').dataset.widen = String(recovery.widen);
    }
```

5. 클릭 위임 맨 앞(`const open = …` 위)에 추가:

```js
    const clear = e.target.closest('[data-clear]');
    if (clear) {
      if (clear.dataset.clear === 'all') activeFilters().forEach(f => clearFilter(f.key));
      else clearFilter(clear.dataset.clear);
      state.limit = 12;
      render();
      return;
    }
```

6. 이벤트 등록부에 추가:

```js
  $('#empty-clear-filters').addEventListener('click', () => {
    const widen = $('#empty-clear-filters').dataset.widen === 'true';
    activeFilters().forEach(f => clearFilter(f.key));
    state.limit = 12;
    if (widen) changeScope('all');
    else render();
  });
```

- [ ] **Step 4: 스타일** — `styles.css` 끝에 추가(칩도 누르는 영역 44px, PRD 7장)

```css
.active-filters {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin: 8px 0;
}
.active-filters button {
  min-height: 44px;
  padding: 4px 14px;
  border: 1px solid var(--green);
  border-radius: 999px;
  background: var(--white);
  color: var(--green);
}
```

- [ ] **Step 5: 테스트**

Run: `python tests/smoke.py --stage 1 --browsers chromium,webkit --modes file,http`
Expected: 실패 0(마지막 줄의 두 숫자가 같음)

- [ ] **Step 6: 커밋**

```bash
git add js/app.js index.html styles.css tests/
git commit -m "v3①: 필터·검색어 유지 (P1-09)" -m "상황 탭이 검색어를 지우지 않음, 적용 중 필터 칩과 개별 해제, 0건일 때 같은 범위→다른 범위 순서의 복구 안내(안내 수 = 해제 뒤 결과 수), 범위 이동 시 숨은 필터 초기화" -m "Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
```

---

### Task 10: 상단 검색 (P1-10)

**Files:**
- Create: `tests/test_mobile.py`
- Modify: `index.html`, `js/app.js`, `styles.css`, `tests/test_regression.py`

**Interfaces:**
- Consumes: `notices_fixture`·`TEST_NOTICE`(Task 7의 `tests/helpers.py`)
- Produces: DOM `.top-search`(hero 맨 위. `#search-form`이 이곳으로 이동), `button.header-search`(모든 폭), 모든 폭에서 sticky인 `.site-header`, `#services-title[tabindex="-1"]`. `app.js`의 `scrollBehavior()`, `setScrollPadding()`(헤더 높이 + 12px를 `html`의 scroll-padding-top으로)
- 이유(S12): 검색창을 맨 위로 옮기면 결과와 멀어진다. 헤더를 붙여 두고 헤더 검색 버튼을 모든 폭에 두어, 결과를 본 뒤에도 한 번에 검색창으로 돌아오게 한다. 붙은 헤더가 검색창·결과 제목을 가리지 않게 스크롤 여백을 헤더 높이에 맞춘다.

- [ ] **Step 1: 실패하는 테스트** — `tests/test_mobile.py`

```python
"""상단 검색(P1-10). 모바일 390×844와 데스크톱 1440×900. 위치는 '가려지지 않았는지'(elementFromPoint)로 검사한다."""
from harness import check, test
from helpers import TEST_NOTICE, notices_fixture

HIT = """sel => { const el = document.querySelector(sel); const r = el.getBoundingClientRect();
  const x = r.left + r.width / 2, y = r.top + r.height / 2;
  if (y < 0 || y > window.innerHeight) return 'off-screen ' + Math.round(y);
  const hit = document.elementFromPoint(x, y);
  return hit && (hit === el || el.contains(hit)) ? 'ok' : 'covered by ' + (hit ? (hit.className || hit.tagName) : 'none'); }"""


def not_covered(site, selector):
    return site.page.evaluate(HIT, selector)


def back_to_search(site):
    site.page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
    btn = site.page.locator('.header-search')
    check(btn.is_visible(), '스크롤 뒤 헤더 검색 버튼이 안 보임')
    btn.click()
    site.page.wait_for_function("document.activeElement && document.activeElement.id === 'search-input'")
    state = not_covered(site, '#search-input')
    check(state == 'ok', f'검색창이 보이지 않거나 가려짐: {state}')


@test(viewport='mobile')
def t_search_first_screen_no_notice(site):
    site.page.add_init_script(notices_fixture([]))
    site.open()
    state = not_covered(site, '#search-input')
    check(state == 'ok', f'첫 화면 검색창(공지 없음): {state}')


@test(viewport='mobile')
def t_search_first_screen_with_notice(site):
    site.page.add_init_script(notices_fixture([TEST_NOTICE]))
    site.open()
    check(site.page.locator('#notices').is_visible(), '전제: 공지가 보임')
    state = not_covered(site, '#search-input')
    check(state == 'ok', f'첫 화면 검색창(공지 있음): {state}')


@test(viewport='mobile')
def t_search_one_action_after_scroll_mobile(site):
    site.open()
    back_to_search(site)


@test()
def t_search_one_action_after_scroll_desktop(site):
    site.open()
    back_to_search(site)


@test(viewport='mobile')
def t_mobile_nav_links(site):
    site.open()
    visible = site.page.eval_on_selector_all('nav a', 'els => els.filter(e => e.offsetParent !== null).map(e => e.textContent.trim())')
    check(len(visible) >= 4, f'모바일 주요 메뉴(상황별·전체 검색·자료·공식 도서관): {visible}')


@test()
def t_submit_moves_to_results_not_covered(site):
    site.open()
    site.search('통계')
    state = not_covered(site, '#result-count')
    check(state == 'ok', f'검색 뒤 결과 머리: {state}')


@test()
def t_search_form_keeps_style(site):
    site.open()
    border = site.page.evaluate("getComputedStyle(document.querySelector('#search-form')).borderTopWidth")
    bg = site.page.evaluate("getComputedStyle(document.querySelector('#search-form button')).backgroundColor")
    check(border not in ('0px', ''), f'검색 폼 테두리 스타일이 빠짐: {border}')
    check(bg not in ('rgba(0, 0, 0, 0)', 'transparent'), f'검색 버튼 배경 스타일이 빠짐: {bg}')


@test(viewport='mobile', motion='no-preference')
def t_default_motion_uses_smooth_scroll(site):
    site.page.add_init_script("""window.__scrolls = []; const o = Element.prototype.scrollIntoView;
      Element.prototype.scrollIntoView = function (a) { window.__scrolls.push(a && a.behavior); return o.call(this, a); };""")
    site.open()
    site.search('통계')
    check('smooth' in site.page.evaluate('window.__scrolls'), '기본 설정에서 부드러운 스크롤을 쓰지 않음')
```

`tests/test_regression.py`에서 `d09_mobile_search_far`를 **삭제**한다.

Run: `python tests/smoke.py --stage 1 -k test_mobile`
Expected: `FAIL`

- [ ] **Step 2: index.html 구조 변경**

1. `#search-form` 요소(`<form id="search-form" …>…</form>`) 전체를 잘라 내어, hero 섹션 첫 `<div>` 안 맨 앞(`<p class="eyebrow">책만 빌리는…` 앞)에 아래 감싸개와 함께 붙인다.

```html
<div class="top-search">
  <!-- 여기에 잘라 낸 <form id="search-form" role="search">…</form> -->
</div>
```

2. 헤더 `<nav>` 바로 앞에 추가:

```html
<button type="button" class="header-search" aria-label="검색창으로 이동">검색</button>
```

3. `<h2 id="services-title">`에 `tabindex="-1"`을 추가한다.

- [ ] **Step 3: app.js** — 이벤트 등록부에 추가하고, submit 처리기를 바꾼다

```js
  const scrollBehavior = () => (window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth');

  // 헤더가 화면 위에 붙어 있으므로 스크롤이 헤더 아래에서 멈추게 한다(S12)
  const setScrollPadding = () => {
    document.documentElement.style.scrollPaddingTop = Math.ceil($('.site-header').getBoundingClientRect().height + 12) + 'px';
  };
  setScrollPadding();
  window.addEventListener('resize', setScrollPadding);

  $('.header-search').addEventListener('click', () => {
    $('.top-search').scrollIntoView({ behavior: scrollBehavior(), block: 'start' });
    $('#search-input').focus({ preventScroll: true });
  });
```

```js
  $('#search-form').addEventListener('submit', e => {
    e.preventDefault();
    state.query = $('#search-input').value;
    state.limit = 12;
    render();
    $('#services').scrollIntoView({ behavior: scrollBehavior(), block: 'start' });
  });
```

기존의 두 `scrollIntoView({ behavior: 'smooth' })`도 `scrollIntoView({ behavior: scrollBehavior() })`로 바꾼다.

- [ ] **Step 4: 스타일** — `styles.css`

1. 검색창 스타일이 폼 위치에 묶이지 않게 선택자를 바꾼다(기본 규칙과 560px 미디어쿼리 모두): `.search-row form` → `#search-form`, `.search-row input` → `#search-form input`, `.search-row form button` → `#search-form button`.
2. 모바일에서 메뉴를 숨기던 두 규칙을 지운다: L1의 `@media (max-width: 560px)` 안 `nav>a:not(.official) { display: none; }`, L3의 `.site-header nav>a[data-scope] { display: none; }`(포맷 후 각각 여러 줄).
3. 끝에 추가:

```css
.top-search {
  margin: 0 0 20px;
}
.top-search input {
  min-height: 48px;
}
.site-header {
  position: sticky;
  top: 0;
  z-index: 10;
  background: var(--paper);
  /* 가운데 정렬된 헤더의 바탕을 화면 양옆까지 칠한다 */
  box-shadow: 0 0 0 100vmax var(--paper);
  clip-path: inset(0 -100vmax);
}
.header-search {
  display: inline-flex;
  align-items: center;
  min-height: 44px;
  padding: 0 14px;
  border: 1px solid var(--green);
  border-radius: 999px;
  background: var(--white);
  color: var(--green);
}
@media (max-width: 560px) {
  nav {
    display: flex;
    overflow-x: auto;
    gap: 4px;
  }
  nav > a {
    display: inline-flex;
    align-items: center;
    min-height: 44px;
    white-space: nowrap;
  }
}
/* 데스크톱: 검색 버튼을 메뉴 바로 왼쪽에 붙인다 */
.header-search {
  margin-left: auto;
}
@media (max-width: 560px) {
  /* 모바일: 첫 줄 = 이름 + 검색 버튼, 둘째 줄 = 메뉴(가로 스크롤) */
  .site-header {
    flex-wrap: wrap;
    align-items: center;
    row-gap: 4px;
    padding: 10px 16px 6px;
  }
  .site-header nav {
    order: 3;
    width: 100%;
  }
}
```

- [ ] **Step 5: 테스트**

Run: `python tests/smoke.py --stage 1 --browsers chromium,webkit --modes file,http`
Expected: 실패 0(마지막 줄의 두 숫자가 같음). q11의 `scrollWidth ≤ 390`도 통과해야 한다(nav는 가로 스크롤 영역 안에서만 넘침). 가림 검사가 실패하면 `setScrollPadding()`의 여유(12px)를 늘리거나 헤더 세로 여백을 줄인다.

- [ ] **Step 6: 커밋**

```bash
git add index.html js/app.js styles.css tests/
git commit -m "v3①: 상단 검색 (P1-10)" -m "검색창을 첫 화면 맨 위로, 붙은 헤더와 헤더 검색 버튼(모든 폭), 헤더 높이에 맞춘 스크롤 여백, 검색창 스타일 유지, 모바일 주요 메뉴 표시, 검색 시 결과로 이동(동작 줄이기 존중), 가림 검사" -m "Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
```

---

### Task 11: 접근성 결함 수정 (P1-12)

**Files:**
- Create: `tests/test_a11y.py`
- Modify: `js/app.js`, `index.html`, `styles.css`, `tests/test_regression.py`

**Interfaces:**
- Produces: 상황 카드 질문 `span.category-question`, `#scope-tabs[role=group]`, `#category-tabs[role=group]`

- [ ] **Step 1: 실패하는 접근성 테스트** — `tests/test_a11y.py`

```python
"""접근성(P1-12): 포커스, 구조, 대비, 누르는 영역, 동작 줄이기."""
from harness import check, test

CONTRAST = """([fgSel, bgSel]) => {
  const rgb = s => s.match(/\\d+(\\.\\d+)?/g).slice(0, 3).map(Number);
  const lum = c => { const [r, g, b] = c.map(v => { v /= 255; return v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4; });
    return 0.2126 * r + 0.7152 * g + 0.0722 * b; };
  const fg = rgb(getComputedStyle(document.querySelector(fgSel)).color);
  const bg = rgb(getComputedStyle(document.querySelector(bgSel)).backgroundColor);
  const [a, b] = [lum(fg), lum(bg)].sort((x, y) => y - x); return (a + 0.05) / (b + 0.05); }"""


@test()
def t_structure_roles(site):
    site.open()
    check(site.page.locator('#category-grid button h3').count() == 0, 'button 안 h3 남음')
    for sel in ('#scope-tabs', '#category-tabs'):
        check(site.page.get_attribute(sel, 'role') == 'group', f'{sel} role=group 없음')
    check(site.page.locator('#category-grid [aria-pressed]').count() == 0, '상황 카드에 aria-pressed')
    check(site.page.get_attribute('[data-book="loan"]', 'aria-pressed') == 'false', '책 상황 버튼 초기 aria-pressed')


@test()
def t_focus_after_load_more(site):
    site.open()
    site.page.focus('#load-more')
    site.page.keyboard.press('Enter')
    site.page.wait_for_timeout(120)
    active = site.page.evaluate('document.activeElement.closest(".service-card") !== null')
    check(active, '더 보기 뒤 포커스가 새 카드로 가지 않음')


@test()
def t_focus_after_category_card(site):
    site.open()
    site.category_card('space')
    check(site.page.evaluate('document.activeElement.id') == 'services-title', '상황 카드 뒤 포커스 이동 안 됨')


@test()
def t_contrast(site):
    site.open()
    # 결함 재현(v2 미달): .book-guide p:not(.eyebrow) on #e9eee4 4.31, .resource-filters>div on soft 4.48
    # 회귀 확인(v2 통과): .coverage on paper 4.86, 상세 조건 칸 dt on soft (S11)
    site.scope('resource')
    pairs = [('.book-guide p:not(.eyebrow)', '.book-guide'), ('.resource-filters > div', '.resource-filters'), ('.coverage', 'body')]
    site.open_any('group')
    pairs.append(('.detail-conditions dt', '.detail-conditions div'))
    for fg, bg in pairs:
        ratio = site.page.evaluate(CONTRAST, [fg, bg])
        check(ratio >= 4.5, f'{fg} on {bg} 대비 {ratio:.2f}')
    # 포커스 링: file://에서는 스타일시트 규칙(cssRules)을 읽을 수 없으므로, 실제로 포커스를 준 요소의 계산된 색을 본다
    site.close_detail()
    site.page.focus('#search-input')  # 입력창은 어떻게 포커스해도 :focus-visible이 적용된다
    ring, green = site.page.evaluate("""() => { const t = document.createElement('div'); t.style.color = 'var(--green)';
      document.body.append(t); const g = getComputedStyle(t).color; t.remove();
      return [getComputedStyle(document.activeElement).outlineColor, g]; }""")
    check(ring == green, f'포커스 링 색 {ring}(var(--green) = {green} 기대)')


SMALL = """sels => Array.from(document.querySelectorAll(sels)).filter(e => e.offsetParent !== null || e.closest('dialog[open]'))
  .map(e => [e.textContent.trim().slice(0, 12), Math.round(e.getBoundingClientRect().height)]).filter(([, h]) => h < 44)"""


@test(viewport='mobile')
def t_target_sizes_mobile(site):
    site.open()
    small = site.page.evaluate(SMALL, '#scope-tabs button, #category-tabs button, #search-form button, .book-options button, '
                               '.service-card button, #load-more, nav a, .header-search')
    site.category_tab('space')
    site.search('교외접속')  # 필터 칩과 0건 해제 버튼이 보이는 상태(S11)
    small += site.page.evaluate(SMALL, '.active-filters button, #empty-clear-filters')
    site.open_any('group')
    small += site.page.evaluate(SMALL, '#close-dialog, #detail-content a.primary, .related button, .material-list a')
    check(not small, f'44px 미만: {small[:6]}')


@test()
def t_reduced_motion(site):
    site.page.emulate_media(reduced_motion='reduce')
    site.page.add_init_script("""window.__scrolls = []; const o = Element.prototype.scrollIntoView;
      Element.prototype.scrollIntoView = function (a) { window.__scrolls.push(a && a.behavior); return o.call(this, a); };""")
    site.open()
    site.category_card('space')
    check(site.page.evaluate('window.__scrolls').count('smooth') == 0, '동작 줄이기인데 smooth 스크롤')
```

`tests/test_regression.py`에서 `d08_a11y_structure`를 **삭제**한다.

Run: `python tests/smoke.py --stage 1 -k test_a11y`
Expected: `FAIL`

- [ ] **Step 2: 마크업·ARIA**

- `index.html`: `<div id="scope-tabs" …>`와 `<div id="category-tabs" …>`에 `role="group"` 추가. `[data-book]` 버튼 6개에 `aria-pressed="false"` 추가.
- `js/app.js` 상황 카드 렌더: `'<h3>' + escape(c.question) + '</h3>'` → `'<span class="category-question">' + escape(c.question) + '</span>'`
- `render()`의 `document.querySelectorAll('button[data-category]')` → `document.querySelectorAll('#category-tabs button[data-category]')`

- [ ] **Step 3: 포커스 이동** — `js/app.js`

```js
  $('#load-more').addEventListener('click', () => {
    const before = state.limit;
    state.limit += 12;
    render();
    const next = document.querySelectorAll('#service-grid .service-card button')[before];
    if (next) next.focus();
  });
```

클릭 위임의 상황 카드 분기(`if (cat.classList.contains('category-card')) { … }`) 끝, `render()` 호출 **뒤**에 다음을 실행하도록 바꾼다.

```js
      render();
      if (cat.classList.contains('category-card')) $('#services-title').focus({ preventScroll: true });
      return;
```

- [ ] **Step 4: 대비·포커스 링·누르는 영역** — `styles.css`

1. `:root`의 `--muted: #66716a` → `--muted: #535e57`
2. 포커스 규칙의 `outline: 3px solid #73a98e` → `outline: 3px solid var(--green)`
3. `.category-card h3` 선택자를 `.category-card .category-question`으로 바꾸고 `display: block`을 추가한다.
4. 끝에 추가:

```css
.tabs button,
.scope-tabs button,
#reset,
#search-form button,
.book-options button,
.service-card button,
#load-more,
.related button,
.material-list a,
.active-filters button,
#empty-clear-filters,
.dialog-top button,
#detail-content a.primary,
.header-search,
nav a {
  min-height: 44px;
}
```

- [ ] **Step 5: 테스트**

Run: `python tests/smoke.py --stage 1 --browsers chromium,webkit --modes file,http`
Expected: 실패 0(마지막 줄의 두 숫자가 같음). 대비가 4.5 미만이면 `--muted`를 한 단계 더 어둡게(`#4b5650`) 하고 다시 실행한다.

- [ ] **Step 6: 커밋**

```bash
git add js/app.js index.html styles.css tests/
git commit -m "v3①: 접근성 결함 수정 (P1-12)" -m "더 보기·상황 카드 포커스, 동작 줄이기, 대비 AA, button 안 h3 제거, 탭 묶음 role, 누르는 영역 44px" -m "Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
```

---

### Task 12: 화면 용어 정리 (P1-15)

**Files:**
- Create: `tests/test_terms.py`
- Modify: `js/app.js`, `index.html`, `docs/RESEARCH.md`(v1 문서의 "33개"), `README.md`

**Interfaces:**
- Produces: `kindName` 표시값 — guide `이용 가이드`, resource `논문·자료 사이트`, menu `공식 사이트 메뉴`. `SOURCE_TYPE_LABEL = {'국외DB': '해외 자료'}`

- [ ] **Step 1: 실패하는 용어 테스트** — `tests/test_terms.py`

```python
"""화면 용어(PRD 부록 D, P1-15)."""
from harness import check, test


@test()
def t_terms(site):
    site.open()
    site.scope('resource')  # 숨어 있던 자료 필터를 연 상태에서 본다(S11)
    body = site.page.inner_text('body')
    for old in ('공식 메뉴 위치', '제공 표시', '원목록 97개'):
        check(old not in body, f'옛 용어 남음: {old}')
    check('논문·자료 사이트(전자정보원)' in site.page.inner_text('#scope-tabs'), '범위 탭에 공식 용어 괄호가 없음(부록 D, S19)')
    check('논문·자료 사이트' in site.page.inner_text('#result-count'), '자료 범위 이름')
    cards = site.page.inner_text('#service-grid')
    check('국외DB' not in cards, '국외DB 표시 남음')
    check('이용 범위 확인' not in cards, "'이용 범위 확인' 배지 남음(M5)")


@test()
def t_audience_options(site):
    site.open()
    values = site.page.eval_on_selector_all('#audience option', 'els => els.map(e => e.value)')
    check(values == ['all', 'undergrad'], f'이용 대상 선택지 {values}')


@test()
def t_audience_filter_only_when_it_matters(site):
    site.open()
    visible = lambda: site.page.locator('.audience-control').is_visible()  # noqa: E731
    check(visible(), '전체 범위에는 대학원 대상이 있어 학부생 필터가 보여야 함')
    site.scope('resource')
    check(not visible(), '자료 범위에는 대학원 대상이 없어 숨겨야 함(P1-15)')
    site.scope('guide')
    site.category_tab('books')
    check(not visible(), '책·자료 상황에는 대학원 대상이 없어 숨겨야 함')
    site.category_tab('space')
    check(visible(), '공부 공간에는 캐럴(대학원 대상)이 있어 보여야 함')
```

Run: `python tests/smoke.py --stage 1 -k test_terms`
Expected: `FAIL`

- [ ] **Step 2: app.js 용어**

```js
  const kindName = kind => ({ guide: '이용 가이드', resource: '논문·자료 사이트(전자정보원)', menu: '공식 사이트 메뉴' }[kind] || '이용 가이드');
  const SOURCE_TYPE_LABEL = { '국외DB': '해외 자료', '국내DB': '국내 자료' };
  const sourceTypeLabel = v => SOURCE_TYPE_LABEL[v] || v;
  const ACCESS_BADGE = { '공개자료 안내': ['open', '공개 자료'], '시범서비스': ['trial', '시범 서비스'] };
```

- `card()`의 자료 배지 식을 바꾼다: `'<span class="badge">' + escape(s.subject) + '</span>' + (ACCESS_BADGE[s.accessType] ? '<span class="badge ' + ACCESS_BADGE[s.accessType][0] + '">' + ACCESS_BADGE[s.accessType][1] + '</span>' : '')`
- `card()`의 `escape(resource ? s.sourceType : …)` → `escape(resource ? sourceTypeLabel(s.sourceType) : …)`, 버튼 문구 `'공식 메뉴 위치 보기'` → `'공식 사이트에서 찾는 곳 보기'`
- `openDetail()`의 `s.subject + ' · ' + s.sourceType` → `s.subject + ' · ' + sourceTypeLabel(s.sourceType)`
- 범위 탭 이름: `'전자정보원'` → `'논문·자료 사이트(전자정보원)'`(부록 D 후보. 공식 사이트·상세 버튼이 쓰는 말과 이어지게 괄호를 남긴다, S19), `'공식 메뉴'` → `'공식 사이트 메뉴'`
- 학부생 필터는 결과가 달라질 때만 보이게 한다(P1-15, S5). `render()` 위에 아래 함수를 두고, `render()` 끝에 `$('.audience-control').hidden = !audienceMatters();`를 넣는다. Task 9의 `activeFilters()`에서 대상 칩 조건을 `if (state.audience !== 'all' && audienceMatters())`로 바꾼다(숨은 필터의 칩은 보이지 않게).

```js
  // 학부생 필터는 지금 범위·상황에 대학원 대상이 있을 때만 의미가 있다. 입력 중에 깜빡이지 않게 검색어는 보지 않는다
  function audienceMatters() {
    return records.some(r => r.audience === 'grad' && (state.scope === 'all' || r.recordKind === state.scope)
      && (state.category === 'all' || r.category === state.category));
  }
```
- `notes`를 바꾼다:

```js
  const notes = {
    all: '이용 가이드, 논문·자료 사이트, 공식 사이트 메뉴를 함께 찾아요. 같은 서비스가 여러 곳에 보일 수 있어요.',
    guide: '학생 질문으로 풀어 쓴 이용 안내예요. 대상·비용·인증은 공식 안내를 다시 확인해 주세요.',
    resource: '도서관 전자자료 목록 98개예요. 공개 자료·시범 서비스·그 밖의 자료는 이용 조건이 달라요.',
    menu: '공식 사이트의 메뉴 89개를 어디서 찾는지 알려 줘요. 로그인 뒤 기능까지 확인한 것은 아니에요.'
  };
```

- `resource-type` select 옵션 생성에서 표시 문구만 `sourceTypeLabel(v)`로(값은 그대로): `'<option value="' + escape(v) + '">' + escape(sourceTypeLabel(v)) + '</option>'`
- `#coverage` 문구: `services.length + '개 이용 안내 · 논문·자료 사이트 ' + resources.length + '개 · 공식 사이트 메뉴 ' + directory.length + '개를 찾을 수 있어요'`

- [ ] **Step 3: index.html 용어**

- `<label for="resource-access">제공 표시</label>` → `이용 상태`
- `#resource-access`의 옵션 문구: `공개자료로 안내` → `공개 자료`, `시범서비스로 표시` → `시범 서비스`, `이용 범위 확인 필요` → `학교 이용 범위 확인 필요`(value는 그대로)
- `#audience`의 `<option value="grad">…</option>` 삭제
- 헤더 nav의 `전자정보원` 링크 문구 → `논문·자료 사이트`
- about 문단의 "전자정보원 목록" → "논문·자료 사이트 목록"

- [ ] **Step 4: 문서 수치 정리**

- `docs/RESEARCH.md`(v1 조사 기록) 3번째 줄의 "세부 서비스 33개는" → "v1 당시 세부 서비스 33개(현재 48개)는"
- `README.md` "현재 범위"의 가이드 47개 → 48개, 검색 대상 234개 → 235개, 기능 목록에 "공지(시험기간 등)", "적용 중 필터 표시" 추가

- [ ] **Step 5: 테스트**

Run: `python tests/smoke.py --stage 1 --browsers chromium,webkit --modes file,http`
Expected: 실패 0(마지막 줄의 두 숫자가 같음)

- [ ] **Step 6: 커밋**

```bash
git add js/app.js index.html docs/RESEARCH.md README.md tests/
git commit -m "v3①: 화면 용어 정리 (P1-15)" -m "전자정보원→논문·자료 사이트, 공식 메뉴 위치→공식 사이트 메뉴, 제공 표시→이용 상태, 정보 없는 배지 제거, 대학원생(전체) 선택지 제거, 문서 수치 갱신" -m "Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
```

---

### Task 13: 배포 준비와 push 게이트 (P1-14)

**Files:**
- Create: `js/config.js`, `favicon.svg`, `tools/gate.py`, `tools/deploy_check.py`, `tests/test_deploy.py`, `tests/check_links.py`
- Modify: `index.html`, `js/lib.js`, `js/app.js`, `docs/DEV.md`

**Interfaces:**
- Produces:
  - `window.LG_CONFIG = {siteUrl, feedbackFormUrl, feedbackFields: {query, card}}`
  - `LG.feedbackUrl(config, {query, card}) -> string` (폼 주소가 없으면 `''`)
  - `python tools/gate.py` (실패 시 종료 코드 1), `python tools/deploy_check.py <배포 주소>`
  - `python tests/check_links.py [--only 문자열] [--limit N] [--out 경로]` → `.tmp/links-report.md`(정상·경고·실패 기록. 종료 코드는 늘 0, S9)

- [ ] **Step 1: 실패하는 배포 테스트** — `tests/test_deploy.py`

```python
"""배포 준비(P1-14)."""
from harness import check, test

FORM = """(() => { let v; Object.defineProperty(window, 'LG_CONFIG', { configurable: true, get() { return v; },
  set(x) { x.feedbackFormUrl = 'https://docs.google.com/forms/d/e/TEST/viewform';
           x.feedbackFields = { query: 'entry.1', card: 'entry.2' }; v = x; } }); })();"""


@test()
def t_head_meta(site):
    site.open()
    check(site.page.get_attribute('meta[name="robots"]', 'content') == 'noindex', 'noindex 없음(M4)')
    check(site.page.get_attribute('meta[property="og:title"]', 'content'), 'og:title 없음')
    check(site.page.get_attribute('link[rel="icon"]', 'href') == 'favicon.svg', '파비콘 없음')
    check('비공식' in site.page.inner_text('.site-header'), '헤더에 비공식 표시 없음')


# 실제 config.js 값과 상관없이 돌도록 "폼 없음"도 명시적으로 주입한다(S16)
NO_FORM = """(() => { let v; Object.defineProperty(window, 'LG_CONFIG', { configurable: true, get() { return v; },
  set(x) { x.feedbackFormUrl = ''; v = x; } }); })();"""


@test()
def t_feedback_hidden_without_form(site):
    site.page.add_init_script(NO_FORM)
    site.open()
    site.search('zzqq없는말')
    check(site.page.locator('#feedback-link').is_hidden(), '폼 주소가 없는데 제보 링크가 보임')
    site.open_any('group')
    check(site.page.locator('#detail-content .feedback-link').count() == 0, '폼 주소가 없는데 상세에 제보 링크가 있음')


@test()
def t_feedback_prefilled(site):
    site.page.add_init_script(FORM)
    site.open()
    site.search('zzqq없는말')
    href = site.page.get_attribute('#feedback-link', 'href')
    check(href and href.startswith('https://docs.google.com/forms/') and 'entry.1=' in href, f'제보 링크 {href}')
    check('zzqq' in href, '검색어가 미리 채워지지 않음')


@test()
def t_feedback_card_prefill(site):
    site.page.add_init_script(FORM)
    site.open()
    site.open_any('group')
    href = site.page.get_attribute('#detail-content .feedback-link', 'href')
    check(href and 'entry.2=group' in href, f'상세 제보 링크에 카드 id가 없음: {href}')
```

Run: `python tests/smoke.py --stage 1 -k test_deploy`
Expected: `FAIL`

- [ ] **Step 2: 설정 파일** — `js/config.js`

```js
// 사이트 설정. 배포 주소와 제보 폼은 사용자가 정한 뒤 채운다(PRD D9, P1-14).
window.LG_CONFIG = {
  siteUrl: '',
  feedbackFormUrl: '',
  feedbackFields: { query: '', card: '' }
};
```

- [ ] **Step 3: lib.js 제보 주소**

```js
  // 구글 폼 미리 채우기 주소. 폼이 없으면 '' (링크를 숨긴다).
  LG.feedbackUrl = (config, values = {}) => {
    const base = LG.safeUrl(config && config.feedbackFormUrl);
    if (!base) return '';
    const fields = (config && config.feedbackFields) || {};
    const params = ['usp=pp_url'];
    for (const key of ['query', 'card']) {
      if (fields[key] && values[key]) params.push(encodeURIComponent(fields[key]) + '=' + encodeURIComponent(values[key]));
    }
    return base + (base.includes('?') ? '&' : '?') + params.join('&');
  };
```

- [ ] **Step 4: index.html**

`<head>`의 `<title>` 아래에 추가:

```html
<meta name="robots" content="noindex">
<meta property="og:title" content="도서관의 쓸모 | 제주대 도서관 활용 가이드(비공식)">
<meta property="og:description" content="학생의 질문에서 시작하는 제주대학교 도서관 비공식 활용 가이드">
<meta property="og:type" content="website">
<meta property="og:locale" content="ko_KR">
<meta name="theme-color" content="#245b43">
<link rel="icon" href="favicon.svg" type="image/svg+xml">
```

스크립트 순서를 `data.js` → `js/config.js` → `js/lib.js` → `js/app.js`로 한다(`config.js` 태그 추가, `js/app.js` 맨 위 주석도 같이).
헤더 `<span>제주대 학생을 위한 활용 가이드</span>` → `<span>제주대 학생을 위한 비공식 활용 가이드</span>`.
`#empty` 안 `<button class="primary" id="empty-reset">` 앞에 추가:

```html
<a id="feedback-link" class="feedback-link" target="_blank" rel="noopener noreferrer" hidden>찾는 게 없거나 정보가 틀렸나요? 알려 주세요 ↗</a>
```

- [ ] **Step 5: app.js 제보 링크** — `render()` 끝에 추가

```js
    const fb = window.LG.feedbackUrl(window.LG_CONFIG, { query: state.query });
    $('#feedback-link').hidden = !fb || currentMatches.length !== 0;
    if (fb) $('#feedback-link').href = fb;
```

`openDetail()`의 `.detail-disclaimer` 문단 뒤에 추가:

```js
      + (() => { const u = window.LG.feedbackUrl(window.LG_CONFIG, { card: id });
        return u ? '<p><a class="feedback-link" href="' + escape(u) + '" target="_blank" rel="noopener noreferrer">이 안내가 틀렸나요? 알려 주세요 ↗</a></p>' : ''; })()
```

- [ ] **Step 6: 파비콘** — `favicon.svg` (Tabler Icons "book", MIT)

```svg
<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#245b43" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 19a9 9 0 0 1 9 0a9 9 0 0 1 9 0"/><path d="M3 6a9 9 0 0 1 9 0a9 9 0 0 1 9 0"/><path d="M3 6l0 13"/><path d="M12 6l0 13"/><path d="M21 6l0 13"/></svg>
```

- [ ] **Step 7: push 게이트** — `tools/gate.py`

```python
"""push 전 검사(PRD 2장 9번, K17, D16). 사용: python tools/gate.py"""
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
PY = sys.executable
STEPS = [
    ('데이터 생성', [PY, 'tools/build_data.py']),
    ('생성물이 커밋된 상태와 같은지', ['git', 'diff', '--exit-code', '--', 'data.js']),
    ('데이터 검사', [PY, 'tests/check_data.py', '--stage', '1']),
    ('Playwright', [PY, 'tests/smoke.py', '--stage', '1', '--browsers', 'chromium,webkit', '--modes', 'file,http']),
]


def clean_tree():
    out = subprocess.run(['git', 'status', '--porcelain'], cwd=ROOT, capture_output=True, check=True).stdout.decode('utf-8')
    return out.strip() == ''


def private_ok():
    # 경로를 직접 지정해 묻는다. 출력 문자열 검색은 한글 경로가 8진수로 바뀌면 놓친다(S17)
    tracked = subprocess.run(['git', 'ls-files', '-z', '--', '_비공개'], cwd=ROOT, capture_output=True, check=True).stdout
    ignored = subprocess.run(['git', 'check-ignore', '-q', '_비공개/x'], cwd=ROOT).returncode == 0
    return tracked == b'' and ignored


def main():
    print('== 작업 트리 확인', flush=True)
    if not clean_tree():
        print('게이트 실패: 커밋하지 않은 변경이 있습니다. 커밋한 뒤 다시 실행하세요(테스트한 파일 = push할 커밋, D16).')
        sys.exit(1)
    for name, cmd in STEPS:
        print(f'== {name}', flush=True)
        if subprocess.run(cmd, cwd=ROOT).returncode != 0:
            print(f'게이트 실패: {name}. push하지 마세요.')
            sys.exit(1)
    print('== _비공개/ 제외 확인')
    if not private_ok():
        print('게이트 실패: _비공개/가 추적되거나 제외되지 않았습니다.')
        sys.exit(1)
    print('게이트 통과: push해도 됩니다.')


if __name__ == '__main__':
    main()
```

- [ ] **Step 8: 배포본 확인** — `tools/deploy_check.py`

```python
"""배포본이 HEAD와 같은지 확인한 뒤 배포 주소에서 테스트한다. 사용: python tools/deploy_check.py https://<배포 주소>/"""
import hashlib
import pathlib
import subprocess
import sys
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
FILES = ['index.html', 'styles.css', 'data.js', 'js/config.js', 'js/lib.js', 'js/app.js', 'favicon.svg']


def main():
    base = sys.argv[1].rstrip('/') + '/'
    stale = []
    for f in FILES:
        local = subprocess.run(['git', 'show', f'HEAD:{f}'], cwd=ROOT, capture_output=True, check=True).stdout
        with urllib.request.urlopen(base + f + '?nocache=1') as r:
            remote = r.read()
        if hashlib.sha256(local).digest() != hashlib.sha256(remote).digest():
            stale.append(f)
    if stale:
        print('배포본이 아직 HEAD와 다릅니다:', stale, '— 잠시 뒤 다시 실행하세요.')
        sys.exit(1)
    print('배포본 = HEAD 확인')
    sys.exit(subprocess.run([sys.executable, 'tests/smoke.py', '--stage', '1', '--browsers', 'chromium,webkit', '--base', base], cwd=ROOT).returncode)


if __name__ == '__main__':
    main()
```

- [ ] **Step 9: 링크 도착 점검 도구** — `tests/check_links.py`(PRD 8장·부록 A 분류표·부록 B, S9. 게이트에는 넣지 않는다)

```python
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
    return '정상', ''


def check_page(context, url):
    page = context.new_page()  # 주소마다 새 문서로 연다(같은 문서 안 해시 이동은 제목·상태가 남는다)
    try:
        page.goto(url, timeout=20000)
        page.wait_for_timeout(2500)
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
```

Run: `python tests/check_links.py --only facility`
Expected: 시설 주소들이 `정상`으로 나오고 마지막 줄에 `정상 N · 경고 0 · 실패 0 → .tmp/links-report.md`

- [ ] **Step 10: DEV.md 갱신** — 로딩 순서를 `data.js → js/config.js → js/lib.js → js/app.js`로 고치고, 끝에 추가

```markdown
## push와 배포
1. 모든 변경을 커밋한 뒤 `python tools/gate.py` — 통과해야 push한다(커밋하지 않은 변경이 있으면 실패).
2. 처음 한 번(사용자): GitHub 저장소 Settings → Pages → Source를 "Deploy from a branch", Branch를 `main` / `/ (root)`로 저장.
3. push 뒤: `python tools/deploy_check.py https://lumos0107.github.io/jejunu-library-guide/`
4. 배포 주소가 정해지면 `js/config.js`의 `siteUrl`을 채운다. 구글 폼을 만들면 `feedbackFormUrl`과 미리 채우기 entry 이름을 채운다.
5. ① 동안은 `<meta name="robots" content="noindex">`를 유지하고, ② 커뮤니티 공개 때 뺀다.
6. 링크 도착 점검: `python tests/check_links.py` → `.tmp/links-report.md`. 공식 사이트에 부담을 주지 않게 하나씩 천천히 연다. 첫 push 전과 월 1회(D14).
```

- [ ] **Step 11: 테스트와 상태 확인**

Run: `python tests/smoke.py --stage 1 --browsers chromium,webkit --modes file,http`
Expected: 실패 0(마지막 줄의 두 숫자가 같음)

```bash
git status --short
```

Expected: 이 작업에서 만든·고친 파일만 보이고 `_비공개`·`.tmp`·`__pycache__` 줄이 없음(전체 스테이징은 하지 않는다, S17)

- [ ] **Step 12: 커밋**

```bash
git add index.html favicon.svg js/ tools/gate.py tools/deploy_check.py tests/ docs/DEV.md
git commit -m "v3①: 배포 준비와 push 게이트 (P1-14)" -m "noindex·og·파비콘·비공식 표시, 설정 파일과 미리 채운 제보 링크(폼 주소 없으면 숨김), gate.py·deploy_check.py" -m "Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
```

---

### Task 14: 최종 검증·코드 교차 리뷰·문서·push

**Files:**
- Create: `docs/v3/QA-1.md`
- Modify: (리뷰 지적 반영 파일)

- [ ] **Step 1: 공지 기간 확인과 게이트 실행**

오늘이 2026-10-26보다 뒤면 `data/notices.json`의 `exam-2026-2-midterm`을 지우거나 다음 공지로 바꾸고, 생성·커밋한 뒤 게이트를 돌린다(R15. `--today`로 우회하지 않는다).

Run: `python tools/gate.py`
Expected: 마지막 줄 `게이트 통과: push해도 됩니다.`

- [ ] **Step 2: 성능 확인(필수, S18)**

Run: `python tools/perf.py`
Expected: 종료 코드 0(첫 화면 1000ms 이하, 검색 50ms 이하). 넘으면 원인을 고치고 다시 잰다. 고쳐도 넘으면 **push하지 말고 사용자에게 결과를 보여 주고 결정을 받는다.** data.js 크기는 예산(313,537B)을 넘어도 이유와 실제 시간을 기록하면 된다(PRD 7장).

- [ ] **Step 3: 링크 도착 점검(기록, S9)**

Run: `python tests/check_links.py`
Expected: `.tmp/links-report.md` 생성. `실패` 줄은 하나씩 본다. 우리 데이터의 주소가 틀렸으면 고치고(Task 5 방식으로 출처·확인일과 함께), 공식 사이트 쪽 장애면 QA 기록에 경고로 남긴다(PRD 부록 A 분류표).

- [ ] **Step 4: 코드 교차 리뷰(사용자 지시)** — GPT 2명·Claude 2명(관점 A: 학생 사용·콘텐츠 정확성, B: 코드 품질·보안·테스트)이 ① 작업 전체(`git diff $(git log --format=%H --grep='회귀 테스트 기반 추가 (P1-01)' -1)^..HEAD`)와 PRD ①을 평가하고 2라운드 교차 평가한다. 방법은 `docs/v3/REVIEW-2026-10-13.md` 1장과 같다. 합의 지적은 고치고, 각 수정마다 해당 테스트를 먼저 추가한다.

- [ ] **Step 5: 크로스 체크(보조)** — Playwright MCP와 Aside MCP로 로컬 서버(`python -m http.server 8765 --bind 127.0.0.1`)를 열어 S1 대표 과업 A1~A6을 손으로 따라가 보고, 자동 테스트와 다른 결과가 있으면 기록한다.

- [ ] **Step 6: QA 기록** — `docs/v3/QA-1.md`에 남긴다: 실행 환경(브라우저·모드), 게이트 결과, 테스트 수, `python tools/perf.py` 결과(첫 화면·검색 시간, data.js 크기와 313KB 예산 대비. 예산을 넘으면 이유, R19·R21), 링크 점검 요약(정상·경고·실패 수와 실패·경고 목록), 교차 리뷰 요약, 크로스 체크 결과, 남은 사용자 작업(Pages 켜기·구글 폼·학생 테스트), 확인하지 못한 것.

QA-1.md 끝에 **실제 기기 체크리스트**(R22)를 둔다. 배포 주소가 생기면 사용자가 iOS Safari와 삼성 인터넷에서 확인한다.

| # | 확인 | iOS Safari | 삼성 인터넷 |
|---|---|---|---|
| 1 | 첫 화면에서 스크롤 없이 검색창이 보인다 | | |
| 2 | '통계' 검색 → '통계·설문조사'가 상위 3개 안에 있다 | | |
| 3 | 그룹스터디룸 상세: 스크롤 전에 공식 버튼과 대상·비용·인증 요약이 보인다 | | |
| 4 | 공식 버튼이 새 탭에서 공식 페이지를 연다 | | |
| 5 | 상세를 닫기 버튼으로 닫으면 목록으로 돌아온다 | | |
| 6 | 스크롤한 뒤 헤더 '검색' 버튼을 누르면 검색창으로 가고 키보드가 뜬다(검색창이 헤더에 가리지 않음) | | |
| 7 | 글자 크기를 크게 해도 가로로 넘치지 않는다 | | |
| 8 | 상세가 열린 상태에서 뒤로가기를 누르면 어떻게 되는지 기록(①은 보장하지 않음, D15) | | |

- [ ] **Step 7: 커밋과 push**

```bash
git add docs/v3/QA-1.md
git commit -m "v3①: 최종 검증 기록" -m "Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
python tools/gate.py && git push -u origin main
```

Expected: 게이트 통과 뒤 push 성공

- [ ] **Step 8: 사용자에게 넘길 일**

1. GitHub Pages 켜기(DEV.md 절차) → 끝나면 `python tools/deploy_check.py <주소>`
2. 구글 폼 만들기(로그인 없이 제출·익명·연락처 미수집) → 주소와 entry 이름을 `js/config.js`에
3. ② 학생 사용성 테스트 참가자 모집(D8·D13)
4. 배포 주소에서 QA-1.md의 실제 기기 체크리스트 확인(iOS Safari·삼성 인터넷)

---

## 부록. 구현 뒤 바뀐 점 (5차 코드 리뷰)

Task 1~13을 구현한 뒤 5차 교차 평가(코드 리뷰)에서 합의한 수정이다. 이유와 출처는 [REVIEW-2026-10-13-5.md](REVIEW-2026-10-13-5.md), 커밋은 9259a08. 위 Task의 코드 블록은 구현 당시 기준으로 두고, 바뀐 점만 여기에 모은다.

- **콘텐츠(일회성 스크립트 `.tmp/apply_review5.py`):** 이용시간·열람실 좌석에 열람실 페이지의 "일부열람실" 표현, 교외접속 요약 "일부 자료는 별도 가입·등록 필요", 반납 비용 "연체료 유무는 공식 안내에서 확인하지 못함"과 2018년 FAQ 반납함 처리 시점, 에디티지 웹메일 신청 필수(인증 사실), 학위논문 대상 요약, 인쇄 "공식 안내에 인증 언급 없음"·3열람실·방학 중 시간, 시험기간 공지의 연결 카드에 `seat`
- **app.js:** 카드의 대상·비용 배지를 종류 공통으로, 카드 버튼 이름 = 카드 이름 + 보이는 글, 공식 버튼 `aria-describedby="detail-find-hint"`, 필터 칩은 선택 상자에 보이는 글(`selectedLabel`), `clearAllFilters()`(숨은 학부생 필터까지), 칩 해제·0건 복구·검색 제출 뒤 `#services-title`로 포커스, 공지 출처 링크, `Object.hasOwn` 조회
- **index.html·styles.css:** 탭 제목·푸터 '비공식', '전체 검색'에 `data-scope="all"`, `#active-filters`에 `role="group"`, 선택 상자·공지 링크·제보 링크·푸터 링크 44px(문장 안 '출처' 링크는 WCAG 2.5.8 예외), `.skip` z-index 20
- **테스트:** `t_condition_summaries_exact`(조건 요약 13개 정확 일치), `t_all_details_open`(235개), `t_card_button_names_include_visible_text`, `t_resource_card_note_badges`, `t_category_card_starts_fresh`(카드는 검색어를 지움, GPT와 합의), `t_filter_chip_labels_use_display_terms`, `t_hidden_audience_recovery_matches`, `t_focus_after_clearing_filters`, `t_nav_all_search_resets_scope`, `t_skip_link_not_covered`, `t_notice_shows_source_when_different`, q10 책 상황 6개, 악성 데이터 확대, `tests/test_check_data.py`(데이터 검사 음성 테스트). 기본값 테스트는 픽스처 레코드로
- **도구:** check_data(단계 배열, 달력 날짜, recordKind, 예약 키·id, 책 상황 키 대조, 요약에는 위치가 아닌 근거), smoke(실행할 테스트가 없으면 실패), check_links(본문 대기 40초·제목 판정), deploy_check(브라우저와 같은 주소, 배포 전 안내), gate(`.nojekyll` 확인), `.nojekyll` 추가
