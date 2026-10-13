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
import normalize as norm  # noqa: E402

KINDS = ('services', 'resources', 'directory')
ID_RE = re.compile(r'^[a-z0-9-]+$')


def https(u):
    return isinstance(u, str) and u.startswith('https://')


def real_date(s):
    """'YYYY-MM-DD' 형식이면서 달력에 있는 날짜인지(2026-99-99 같은 값을 막는다)."""
    if not isinstance(s, str) or not re.match(r'^\d{4}-\d{2}-\d{2}$', s):
        return False
    try:
        datetime.date.fromisoformat(s)
        return True
    except ValueError:
        return False


RESERVED = {'__proto__', 'constructor', 'prototype'}  # data.js는 객체 리터럴이라 __proto__ 키가 프로토타입이 된다
KIND_OF = {'services': 'guide', 'resources': 'resource', 'directory': 'menu'}


def reserved_keys(o, path='data'):
    found = []
    if isinstance(o, dict):
        for k, v in o.items():
            if k in RESERVED:
                found.append(f'{path}.{k}')
            found += reserved_keys(v, f'{path}.{k}')
    elif isinstance(o, list):
        for i, v in enumerate(o):
            found += reserved_keys(v, f'{path}[{i}]')
    return found


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
        steps = r.get('steps')
        if not isinstance(steps, list) or not steps or not all(isinstance(x, str) and x for x in steps):
            errs.append(f'{rid}: steps는 비어 있지 않은 문자열 배열이어야 함')
        if rid in RESERVED:
            errs.append(f'{rid}: 예약된 이름은 id로 쓸 수 없음')
        if not https(r.get('source')):
            errs.append(f'{rid}: source가 https 아님')
        for m in r.get('materials') or []:
            if not https(m.get('url')):
                errs.append(f'{rid}: 매뉴얼 링크가 https 아님 {m.get("url")}')
        for f in r.get('facts') or []:
            if not f.get('text') or not https(f.get('source')) or not real_date(f.get('checkedAt')):
                errs.append(f'{rid}: facts 형식(text·https source·YYYY-MM-DD checkedAt)')
            if f.get('kind') not in (None, 'location', 'auth', 'hours'):
                errs.append(f'{rid}: facts.kind {f.get("kind")}(location·auth·hours만, D16)')
        if (r.get('eligibilityNote') or r.get('costNote')) and not any(f.get('kind') != 'location' for f in r.get('facts') or []):
            errs.append(f'{rid}: eligibilityNote·costNote의 근거 facts(위치가 아닌 사실) 없음(P1-05)')
        if r.get('recordKind') == 'guide' and re.search(r'#/search/er(-ebook)?$', r.get('source', '')) and not r.get('findHint'):
            errs.append(f'{rid}: 목록형 링크인데 findHint 없음(P1-11)')
        for field in ('name', 'question', 'description', 'keywords'):
            if re.search('무료|무제한', str(r.get(field) or '')):
                errs.append(f'{rid}: 주장 필드 {field}에 무료·무제한(PRD K10)')
    for kind, want in KIND_OF.items():
        for r in d[kind]:
            if r.get('recordKind') != want:
                errs.append(f'{r.get("id")}: recordKind {r.get("recordKind")}({kind}에는 {want})')
    errs += [f'예약된 키 {p}' for p in reserved_keys(d)]
    page_keys = set(re.findall(r'data-book="([^"]+)"', (ROOT / 'index.html').read_text(encoding='utf-8')))
    if page_keys != set(d.get('bookCases') or {}):
        errs.append(f'책 상황 키가 화면과 다름: 화면 {sorted(page_keys)} / 데이터 {sorted(d.get("bookCases") or {})}')
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
    cases = json.loads((ROOT / 'data' / 'normalize-cases.json').read_text(encoding='utf-8'))
    for given, expected in cases:
        if norm.normalize(given) != expected:
            errs.append(f'정규화 벡터 불일치(Python): {given!r} → {norm.normalize(given)!r}, 기대 {expected!r}')
    for field in ('caution', 'steps', 'question'):
        for s in (d.get('commonText') or {}).get(field, []):
            if not any(s == r.get(field) or s in (r.get(field) or []) for r in recs):
                errs.append(f'commonText.{field}: 데이터에 없는 문장')
    date_re = re.compile(r'^\d{4}-\d{2}-\d{2}$')
    for n in d.get('notices') or []:
        nid = n.get('id', '?')
        for f in ('id', 'text', 'checkedAt', 'startsOn', 'endsOn'):
            if not n.get(f):
                errs.append(f'notice {nid}: {f} 없음')
        if not (https(n.get('link')) and https(n.get('source'))):
            errs.append(f'notice {nid}: link·source가 https 아님')
        if not all(real_date(n.get(f)) for f in ('checkedAt', 'startsOn', 'endsOn')):
            errs.append(f'notice {nid}: 날짜 형식 YYYY-MM-DD')
        elif n['startsOn'] > n['endsOn']:
            errs.append(f'notice {nid}: 시작일 > 종료일')
        elif n['endsOn'] < today:
            errs.append(f'notice {nid}: 기간이 지났습니다({n["endsOn"]}). 공지를 지우거나 갱신하세요(K18)')
        for t in n.get('taskIds') or []:
            if t not in have:
                errs.append(f'notice {nid}: 없는 taskId {t}')
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
