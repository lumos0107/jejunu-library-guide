"""전자정보원 카드의 '찾는 방법'이 공식 목록에서 실제로 통하는지 점검한다(읽기만, 기록용. 링크 점검과 함께 월 1회).
공식 목록은 거른 상태를 주소에 담지 않아(2026-10-13 확인, D18) 가나다·ABC 버튼과 검색어로 안내한다.
공식 페이지 자신의 거르기 함수로 카드마다 ① 검색어로 그 자료가 나오는지 ② 안내한 버튼이 화면에 있고 그 자료가 걸리는지 본다.
결과가 1건 이상이라는 것만으로는 통과가 아니다(그 자료가 들어 있어야 한다).
사용: python tests/check_er_find.py [--out .tmp/er-find-report.md]
종료 코드: 0 모두 통과, 1 카드 문제, 2 네트워크 오류·공식 페이지 구조 변경(카드 문제로 단정하지 않는다)"""
import argparse
import datetime
import pathlib
import sys
import time

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[1]
OFFICIAL = 'https://lib.jejunu.ac.kr/#/search/'
BUTTON_VALUE = dict(zip('가나다라마바사아자차카타파하', 'ㄱㄴㄷㄹㅁㅂㅅㅇㅈㅊㅋㅌㅍㅎ'))

# 앱이 실제로 쓰는 재료(검색어·버튼)를 앱의 함수로 뽑는다. 규칙을 여기서 다시 쓰지 않는다.
OURS = r"""() => window.LIBRARY_GUIDE.resources.filter(r => /#\/search\/er(-ebook)?$/.test(r.source) && !r.findHint).map(r => ({
  id: r.id, name: r.name, route: r.source.split('#/search/')[1], term: r.findTerm || r.name,
  button: /#\/search\/er$/.test(r.source) ? window.LG.indexButton(r.name) : '' }))"""

CHECK = r"""cards => {
  let s = null;
  for (const el of document.querySelectorAll('.ng-scope')) {
    let c = window.angular && angular.element(el).scope();
    while (c && !Object.prototype.hasOwnProperty.call(c, 'tmpErResources')) c = c.$parent;
    if (c && c.tmpErResources && typeof c.search === 'function' && typeof c.indexSearch === 'function') { s = c; break; }
  }
  if (!s || !s.tmpErResources.list) return { error: '공식 페이지 구조가 바뀜(거르기 함수·목록을 찾지 못함)' };
  const list = s.tmpErResources.list;
  const squash = x => String(x || '').replace(/\s+/g, ' ').trim();
  const buttons = [...document.querySelectorAll('[ng-click^="indexSearch"]')].map(e => e.innerText.trim());
  const used = new Set();
  const rows = cards.map(c => {
    // 같은 자료: 공백을 하나로 줄여 비교. 공식 이름 옆의 'Trial' 표시는 우리 이름에만 붙어 있다
    const same = list.filter(o => squash(o.name) === squash(c.name) || squash(o.name) + ' Trial' === squash(c.name));
    same.forEach(o => used.add(o));
    if (!same.length) return { id: c.id, name: c.name, status: '공식 목록에서 같은 자료를 못 찾음(이름이 바뀌었나?)' };
    s.indexSearch(null); s.searchKeyword = c.term;
    const bySearch = same.some(o => s.search(o));
    s.searchKeyword = '';
    let status = bySearch ? '통과' : `검색어 '${c.term}'로 나오지 않음`;
    if (c.button) {
      if (!buttons.includes(c.button)) status = `'${c.button}' 버튼이 화면에 없음`;
      else {
        const byButton = same.some(o => { s.indexSearch(c.value); const ok = s.search(o); s.indexSearch(null); return ok; });
        if (!byButton) status = `'${c.button}' 버튼으로 나오지 않음`;
      }
    }
    return { id: c.id, name: c.name, status };
  });
  s.indexSearch(null); s.searchKeyword = '';
  const extra = list.filter(o => !used.has(o)).map(o => o.name);
  return { rows, extra, total: list.length };
}"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default=str(ROOT / '.tmp' / 'er-find-report.md'))
    a = ap.parse_args()
    lines = [f'# 전자정보원 찾는 방법 점검 ({datetime.date.today().isoformat()})', '']
    code = 0
    with sync_playwright() as p:
        b = p.chromium.launch()
        page = b.new_page()
        page.goto((ROOT / 'index.html').as_uri())
        page.wait_for_selector('#service-grid .service-card')
        cards = page.evaluate(OURS)
        for c in cards:
            c['value'] = '#' if c['button'] == '기타' else BUTTON_VALUE.get(c['button'], c['button'])
        for route in ('er', 'er-ebook'):
            mine = [c for c in cards if c['route'] == route]
            try:
                page.goto(OFFICIAL + route, wait_until='domcontentloaded', timeout=40000)
                page.wait_for_function('() => window.angular && document.querySelector(".ng-scope")', timeout=40000)
                time.sleep(5)  # 목록 API 응답 대기(공식 사이트에 부담을 주지 않게 목록당 한 번만 연다)
                res = page.evaluate(CHECK, mine)
            except Exception as e:  # 네트워크·시간 초과
                res = {'error': '네트워크 오류: ' + (str(e).splitlines() or [repr(e)])[0]}
            lines.append(f'## {OFFICIAL}{route}')
            if 'error' in res:
                lines += ['', f'- 점검 불가: {res["error"]}', '']
                code = max(code, 2)
                continue
            bad = [r for r in res['rows'] if r['status'] != '통과']
            lines += ['', f'- 공식 목록 {res["total"]}건, 우리 카드 {len(mine)}개, 통과 {len(mine) - len(bad)}개', '']
            if bad:
                code = max(code, 1)
                lines += ['| 카드 | 이름 | 문제 |', '|---|---|---|'] + [f'| {r["id"]} | {r["name"]} | {r["status"]} |' for r in bad] + ['']
            if res['extra']:
                lines += ['공식 목록에만 있는 자료(우리 카드 없음, 참고): ' + ', '.join(res['extra']), '']
            time.sleep(1.5)
        b.close()
    out = pathlib.Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text('\n'.join(lines) + '\n', encoding='utf-8', newline='\n')
    print('\n'.join(lines))
    print(f'기록: {out}')
    sys.exit(code)


if __name__ == '__main__':
    main()
