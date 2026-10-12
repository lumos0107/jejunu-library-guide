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
