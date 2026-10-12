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
