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
