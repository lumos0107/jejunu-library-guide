"""화면 안전: 데이터의 악성 문자열이 실행되거나 링크로 열리지 않는다."""
from harness import check, test

# facts·찾는 방법·대상·공지 경로도 미리 넣어 둔다. 뒤 Task가 이 필드를 화면에 그리기 시작하면 이 테스트가 자동으로 그 경로까지 검사한다(S11)
EVIL = r"""(() => { let v; Object.defineProperty(window, 'LIBRARY_GUIDE', { configurable: true,
  get() { return v; },
  set(x) { x.services.unshift({ id: 'x"onmouseover="window.__xss=2', name: '<img src=x onerror="window.__xss=1">',
    question: 'q', category: 'start', description: '<b>d</b>', audience: 'all', channel: 'c', login: 'l', cost: 'c',
    caution: '<img src=x onerror="window.__xss=4">', steps: ['s'], source: 'javascript:window.__xss=3', keywords: 'evil',
    checkedAt: '2026-10-13', recordKind: 'guide', materials: [{ label: 'm', url: 'http://insecure.example' }],
    findHint: '<img src=x onerror="window.__xss=5">', eligibilityNote: '<img src=x onerror="window.__xss=6">',
    facts: [{ text: '<img src=x onerror="window.__xss=7">', source: 'javascript:window.__xss=8', checkedAt: '2026-10-13' }] });
    x.notices = [{ id: 'evil-notice', text: '<img src=x onerror="window.__xss=9">', link: 'javascript:window.__xss=10',
      source: 'javascript:window.__xss=11', checkedAt: '2026-10-13', startsOn: '2026-10-01', endsOn: '2026-12-31',
      taskIds: ['x"onmouseover="window.__xss=2'] }];
    const r = x.resources[0]; r.name = '<img src=x onerror="window.__xss=12">evil-res'; r.subject = '<img src=x onerror="window.__xss=13">';
    r.officialDescription = '<img src=x onerror="window.__xss=14">';
    const m = x.directory[0]; m.name = '<img src=x onerror="window.__xss=15">evil-menu'; m.menuGroup = '<img src=x onerror="window.__xss=16">';
    x.categories[0].name = '<img src=x onerror="window.__xss=17">'; x.categories[0].question = '<img src=x onerror="window.__xss=18">';
    x.bookCases.loan.text = '<img src=x onerror="window.__xss=19">';
    v = x; } }); })();"""


@test()
def t_malicious_data_is_inert(site):
    site.page.add_init_script(EVIL)
    site.open()
    site.search('evil')
    site.page.locator('#service-grid .service-card').first.hover()
    site.page.locator('#service-grid button').first.click()
    site.page.wait_for_selector('#detail-dialog[open]')  # 상세가 실제로 열린 상태에서 검사한다(S11)
    site.page.wait_for_timeout(200)
    site.close_detail()
    for scope in ('resource', 'menu'):  # 자료·메뉴 카드와 선택 상자, 상세까지 그린다
        site.scope(scope)
        site.search('evil')
        site.page.locator('#service-grid button').first.click()
        site.page.wait_for_selector('#detail-dialog[open]')
        site.close_detail()
    site.book_case('loan')
    site.page.wait_for_timeout(200)
    check(site.page.evaluate('document.querySelectorAll("img, [onerror], [onmouseover]").length') == 0, '악성 요소가 문서에 들어감')
    check(site.page.evaluate('window.__xss') is None, f'스크립트가 실행됨: {site.page.evaluate("window.__xss")}')
    hrefs = site.page.eval_on_selector_all('a[href]', 'els => els.map(e => e.getAttribute("href"))')
    bad = [h for h in hrefs if h.lower().startswith(('javascript:', 'http:'))]
    check(not bad, f'안전하지 않은 링크: {bad}')
