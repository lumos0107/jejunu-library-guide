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
