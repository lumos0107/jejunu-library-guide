"""전자정보원 카드의 이름·매뉴얼 링크를 공식 목록 API와 대조한다(읽기만, 기록용. check_er_find와 함께 월 1회).
2026-10-14 전체 링크 점검에서 공식 목록 이름이 하루 사이에 바뀐 것(RefWorks(New Version) → Endnote Fusion(구. RefWorks))과
공식 쪽에서 끊긴 매뉴얼 링크를 찾았다. 공식 화면이 쓰는 공개 API(pyxis-api/1/er-sources)를 그대로 읽는다.
- 이름: 공식 목록에 같은 이름이 없으면 알린다. 시범서비스(isTrial)는 공식 이름 뒤에 Trial을 붙인 이름도 같은 것으로 본다(D18).
- 매뉴얼: 공식 목록의 링크(설명·주소)와 카드의 링크가 다르면 알린다. 카드에만 있는 도서관 안내 화면(#/…) 링크는 일부러 더한 것이라 뺀다.
- 공식 목록의 링크가 열리지 않는 것(파일 없음)도 알린다.
사용: python tests/check_er_api.py
종료 코드: 0 모두 같음, 1 다른 곳 있음, 2 네트워크 오류·API 구조 변경(카드 문제로 단정하지 않는다)"""
import json
import pathlib
import re
import sys
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
API = 'https://lib.jejunu.ac.kr/pyxis-api/1/er-sources?erSourceTypeId=7'  # 홈페이지용 전자자료(#/search/er 목록)


def norm(s):
    return re.sub(r'\s+', '', s or '').lower()


def get(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0', 'Range': 'bytes=0-0'})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.status, r.headers.get('Content-Type') or '', r.read(400)


def main():
    try:
        data = json.loads(urllib.request.urlopen(API, timeout=30).read().decode('utf-8'))
        official = data['data']['list'] if isinstance(data['data'], dict) else data['data']
        assert official and 'name' in official[0]
    except Exception as e:
        print('공식 목록 API를 읽지 못함:', e)
        return 2
    ours = [r for r in json.loads((ROOT / 'data' / 'resources.json').read_text(encoding='utf-8')) if r['source'].endswith('#/search/er')]
    by = {}
    for x in official:
        by[norm(x['name'])] = x
        if str(x.get('isTrial')).lower() == 'true':
            by[norm(x['name'] + ' Trial')] = x
    problems, notes = [], []
    for r in ours:
        x = by.get(norm(r['name']))
        if not x:
            problems.append(f"{r['id']} {r['name']}: 공식 목록에 같은 이름이 없음(이름이 바뀌었거나 빠졌는지 확인)")
            continue
        theirs = {(w.get('description') or '').strip(): w['url'].rstrip('/') for w in x.get('webResources') or []}
        mine = {(m.get('label') or '').strip(): m['url'].rstrip('/') for m in r.get('materials') or [] if '/#/' not in m['url']}
        for label, url in list(theirs.items()):
            if '/attachments/' not in url:
                continue
            try:
                status, ctype, head = get(url)
            except Exception as e:
                problems.append(f"{r['id']} {r['name']}: 공식 매뉴얼 '{label}' 열기 실패 {str(e)[:60]}")
                continue
            if 'json' in ctype and b'notFound' in head:  # 공식 쪽에서 끊긴 파일은 카드에서 뺀다(알리기만)
                notes.append(f"{r['id']} {r['name']}: 공식 매뉴얼 '{label}' 파일 없음(공식 쪽에서 끊김{', 카드에도 남아 있음' if label in mine else ''}) {url}")
                if label in mine:
                    problems.append(notes[-1])
                del theirs[label]
        for label in sorted(set(theirs) | set(mine)):
            if theirs.get(label) != mine.get(label):
                problems.append(f"{r['id']} {r['name']}: 매뉴얼 '{label}' 공식 {theirs.get(label) or '없음'} / 카드 {mine.get(label) or '없음'}")
    names = {norm(r['name']) for r in ours}
    for x in official:
        if norm(x['name']) not in names and norm(x['name'] + ' Trial') not in names:
            problems.append(f"공식 목록에만 있음: {x['name']}")
    for n in notes:
        print('참고:', n)
    print('\n'.join(problems) or '공식 목록과 모두 같음')
    return 1 if problems else 0


if __name__ == '__main__':
    sys.exit(main())
