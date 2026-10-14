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
def t_search_first_screen_two_notices(site):
    """시험기간처럼 공지가 세 건(24시간 개방·야간버스·독서주간)이어도 첫 화면에서 검색창이 보인다."""
    second = dict(TEST_NOTICE, id='fixture-bus', text='테스트 공지: 시험 기간 도서관 야간버스 운행(중앙도서관 정문 앞 탑승). 날짜별 출발 시각·노선은 공지의 표 확인')
    third = dict(TEST_NOTICE, id='fixture-week', text='테스트 공지: 독서주간 한정, 연체도서를 반납하고 안내데스크에 요청하면 대출 정지 즉시 해제(챌린지·응모도 진행, 기념품은 소진 시 종료)')
    site.page.add_init_script(notices_fixture([TEST_NOTICE, second, third]))
    site.open()
    check(site.page.locator('#notices li').count() == 3, '전제: 공지 세 건')
    state = not_covered(site, '#search-input')
    check(state == 'ok', f'첫 화면 검색창(공지 세 건): {state}')


@test(viewport='mobile')
def t_notices_collapsed_one_line(site):
    """공지는 1건부터 한 줄로 접힌다(D21). 요약 44px, 펼치면 링크 44px, 검색해도 펼친 상태 유지."""
    second = dict(TEST_NOTICE, id='fixture-bus', text='테스트 공지 둘')
    site.page.add_init_script(notices_fixture([TEST_NOTICE, second]))
    site.open()
    summary = site.page.locator('#notices summary')
    check(site.page.locator('#notices details:not([open])').count() == 1, '공지가 접혀 있지 않음')
    check('2건' in summary.inner_text() and summary.bounding_box()['height'] >= 44, f'요약 줄: {summary.inner_text()}')
    summary.click()
    links = site.page.locator('#notices a')
    check(links.first.is_visible() and links.first.bounding_box()['height'] >= 44, '펼친 공지의 링크가 안 보이거나 44px 미만')
    site.page.fill('#search-input', '열람실')
    site.page.wait_for_timeout(120)
    check(site.page.locator('#notices details[open]').count() == 1, '검색했더니 펼친 공지가 닫힘')


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
def t_default_motion_scrolls_instantly(site):
    """동작 줄이기를 켜지 않아도 즉시 이동한다(부드러운 스크롤은 0.8~1초라 0.3초 규칙에 어긋남, D21 사용자 결정)."""
    site.page.add_init_script("""window.__scrolls = []; const o = Element.prototype.scrollIntoView;
      Element.prototype.scrollIntoView = function (a) { window.__scrolls.push(a && a.behavior); return o.call(this, a); };""")
    site.open()
    site.search('통계')
    site.category_card('space')
    scrolls = site.page.evaluate('window.__scrolls')
    check(scrolls and 'smooth' not in scrolls, f'부드러운 스크롤을 씀: {scrolls}')
    check(site.page.evaluate("getComputedStyle(document.documentElement).scrollBehavior") == 'auto', 'CSS scroll-behavior가 auto가 아님')
