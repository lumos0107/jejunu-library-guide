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
