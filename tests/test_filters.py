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


@test()
def t_category_card_starts_fresh(site):
    # 홈 상황 카드는 검색 없이 시작하는 탐색 입구라 검색어를 지운다(5차 평가에서 GPT와 합의). 탭은 유지(t_category_tab_keeps_query)
    site.open()
    site.search('조별과제')
    site.category_card('space')
    check(site.query_value() == '', '상황 카드가 실패한 검색어를 남김')
    check('group' in site.result_ids(), '공부 공간 탐색 결과에 그룹스터디룸이 없음')


@test()
def t_filter_chip_labels_use_display_terms(site):
    site.open()
    site.scope('resource')
    site.select('resource-type', '국외DB')
    site.select('resource-access', '이용 범위 확인')
    chips = site.page.inner_text('#active-filters')
    check('해외 자료' in chips and '학교 이용 범위 확인 필요' in chips, f'칩 용어: {chips}')
    check('국외DB' not in chips, f'칩에 옛 용어: {chips}')


@test()
def t_hidden_audience_recovery_matches(site):
    site.open()
    site.select('audience', 'undergrad')
    site.category_card('books')           # 책·자료 상황에는 대학원 대상이 없어 학부생 필터가 숨는다
    site.search('학위논문')
    check(site.count() == 0, f'전제: 0건이어야 함 {site.count()}')
    text, n = recovery_n(site)
    check(n, f'복구 안내 없음: {text}')
    site.page.click('#empty-clear-filters')
    site.page.wait_for_timeout(100)
    check(site.count() == n and 'thesis-submit' in site.result_ids(), f'안내 {n}건 != 해제 뒤 {site.count()}건 {site.result_ids()}')


@test()
def t_focus_after_clearing_filters(site):
    site.open()
    check(site.page.get_attribute('#active-filters', 'role') == 'group', '#active-filters에 role=group 없음')
    site.category_tab('space')
    site.page.click('#active-filters [data-clear="category"]')
    site.page.wait_for_timeout(80)
    check(site.page.evaluate('document.activeElement.id') == 'services-title', '칩으로 필터를 푼 뒤 포커스가 사라짐')


@test()
def t_nav_all_search_resets_scope(site):
    site.open()
    site.scope('resource')
    site.page.click('nav a[href="#services"]:not([data-scope="resource"])')
    site.page.wait_for_timeout(100)
    check(site.page.get_attribute('#scope-tabs [data-scope="all"]', 'aria-pressed') == 'true', "'전체 검색' 메뉴가 범위를 바꾸지 않음")
