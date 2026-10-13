"""① 회귀 테스트. q* = 유지할 약속, d* = v2 동작 고정값(표시된 작업에서 기대값을 바꾼다)."""
import json
import pathlib

from harness import check, test

FIX = pathlib.Path(__file__).resolve().parent / 'fixtures'
KINDS = ('services', 'resources', 'directory')


def total(d):
    return sum(len(d[k]) for k in KINDS)


@test()
def q01_ids_preserved(site):
    site.open()
    d = site.data()
    ids = [r['id'] for k in KINDS for r in d[k]]
    check(len(ids) == len(set(ids)), 'id 중복')
    fixture = json.loads((FIX / 'v2-ids.json').read_text(encoding='utf-8'))
    have = set(ids)
    missing = [i for k in fixture for i in fixture[k] if i not in have]
    check(not missing, f'v2 id 누락: {missing[:5]}')


@test()
def q02_required_fields_https_console(site):
    site.open()
    d = site.data()
    for k in KINDS:
        for r in d[k]:
            for f in ('id', 'name', 'description', 'source', 'recordKind'):
                check(r.get(f), f'{r.get("id")}: {f} 없음')
            check(r['steps'], f'{r["id"]}: steps 없음')
            check(r['source'].startswith('https://'), f'{r["id"]}: source가 https 아님')
    check(not site.console_errors(), f'콘솔 오류: {site.console_errors()[:3]}')


@test()
def q03_initial_list_and_load_more(site):
    site.open()
    d = site.data()
    check(site.count() == total(d), f'첫 화면 {site.count()} != {total(d)}')
    check(site.card_count() == 12, '처음 카드 12개')
    site.load_more()
    check(site.card_count() == 24, '더 보기 뒤 24개')
    check(site.page.inner_text('#checked-at').strip() != '', '확인일 표시 없음')
    check(site.category_card_count() == len(d['categories']), f'상황 카드 {site.category_card_count()}')


@test()
def q04_representative_searches(site):
    site.open()
    cases = [('무선인터넷', 2, {'wifi', 'menu-046'}), ('SDI', 3, {'sdi'}), ('외국어 교정', 4, {'editage', 'enago'}),
             ('Naxos', 2, {'culture', 'er-055'}), ('CAS BioFinder', 1, {'er-096'}), ('크레마클럽', 2, {'ebook', 'er-098'})]
    for q, n, must in cases:
        site.search(q)
        ids = set(site.result_ids())
        check(site.count() == n, f'{q}: {site.count()}건(기대 {n})')
        check(must <= ids, f'{q}: {must - ids} 없음')


@test()
def q05_resource_and_menu_filters(site):
    site.open()
    site.scope('resource')
    check(site.count() == 98, f'전자정보원 {site.count()}')
    check(site.resource_filters_visible(), '전자정보원 필터 영역이 안 보임')
    site.select('resource-access', '공개자료 안내')
    check(site.count() == 6, f'공개자료 {site.count()}')
    site.select('resource-access', '시범서비스')
    check(site.count() == 4, f'시범서비스 {site.count()}')
    site.select('resource-access', 'all')
    site.select('resource-subject', '통계·기업')
    check(site.count() == 5, f'통계·기업 {site.count()}')
    site.select('resource-subject', 'all')
    site.scope('menu')
    check(site.count() == 94, f'메뉴 {site.count()}(공식 메뉴 89 + 홈 하단 배너 5, D19)')
    site.select('menu-group', 'My Library')
    check(site.count() == 17, f'My Library {site.count()}')


@test()
def q06_statista_detail(site):
    site.open()
    site.scope('resource')
    site.search('Statista')
    ids = site.result_ids()
    check(ids, 'Statista 결과 없음')
    site.open_detail(ids[0])
    check('Statista' in site.detail_text(), '상세에 Statista 없음')
    check(len(site.material_links()) >= 1, '매뉴얼 링크 없음')
    check(site.official_href() == 'https://lib.jejunu.ac.kr/#/search/er', f'공식 링크 {site.official_href()}')
    site.close_detail()
    check(not site.dialog_open(), 'Escape로 닫히지 않음')


@test()
def q07_undergrad_filter(site):
    site.open()
    d = site.data()
    grad = sum(1 for s in d['services'] if s.get('audience') == 'grad')
    grad_all = sum(1 for k in KINDS for r in d[k] if r.get('audience') == 'grad')  # 메뉴에도 대학원 대상이 있다(S20)
    site.scope('guide')
    check(site.count() == len(d['services']), f'가이드 {site.count()}')
    site.select('audience', 'undergrad')
    check(site.count() == len(d['services']) - grad, f'가이드+학부생 {site.count()}')
    site.scope('all')
    check(site.count() == total(d) - grad_all, f'전체+학부생 {site.count()}')


@test()
def q08_space_category(site):
    site.open()
    d = site.data()
    site.category_card('space')
    space = [s['id'] for s in d['services'] if s['category'] == 'space']
    check(site.count() == len(space), f'공부 공간 {site.count()} != {len(space)}')
    site.select('audience', 'undergrad')
    expect = {s['id'] for s in d['services'] if s['category'] == 'space' and s.get('audience') != 'grad'}
    check(set(site.result_ids()) == expect, f'공부 공간+학부생 {site.result_ids()}')


@test()
def q09_empty_and_reset(site):
    site.open()
    d = site.data()
    site.search('zzzz없는검색어qq')
    check(site.page.locator('#empty').is_visible(), '빈 결과 화면 없음')
    site.page.click('#empty-reset')
    site.page.wait_for_timeout(100)
    check(site.count() == total(d), '초기화 뒤 전체로 돌아오지 않음')


@test()
def q10_book_case_not_owned(site):
    site.open()
    site.book_case('not-owned')
    ids = site.page.eval_on_selector_all('#book-result [data-open]', 'els => els.map(e => e.dataset.open)')
    check(ids == ['wish', 'dds'], f'책 상황 결과 {ids}')
    check(site.page.get_attribute('[data-book="not-owned"]', 'aria-pressed') == 'true', 'aria-pressed')
    # 화면의 책 상황 버튼 6개가 모두 데이터와 이어진다(5차 평가)
    cases = site.data()['bookCases']
    keys = site.page.eval_on_selector_all('[data-book]', 'els => els.map(e => e.dataset.book)')
    check(sorted(keys) == sorted(cases), f'화면 키 {keys} != 데이터 키 {sorted(cases)}')
    for key in keys:
        site.book_case(key)
        got = site.page.eval_on_selector_all('#book-result [data-open]', 'els => els.map(e => e.dataset.open)')
        check(got == cases[key]['ids'], f'{key}: {got} != {cases[key]["ids"]}')


@test(viewport='mobile')
def q11_mobile_basics(site):
    site.open()
    sw = site.page.evaluate('document.documentElement.scrollWidth')
    check(sw <= 390, f'가로 넘침 {sw}')
    site.scope('resource')
    site.search('JSTOR')
    check(site.count() == 1, f'JSTOR {site.count()}')
    site.open_detail(site.result_ids()[0])
    box = site.page.locator('#detail-dialog').bounding_box()
    check(box['x'] >= 0 and box['x'] + box['width'] <= 390, f'상세 폭 {box}')
    site.close_detail()
    check(not site.dialog_open(), 'Escape로 닫히지 않음')


@test()
def q12_hero_button_and_close(site):
    site.open()
    site.open_from_hero('maker')
    check('메이커' in site.detail_text(), '히어로 버튼으로 메이커 상세가 열리지 않음')
    site.close_with_button()
    check(not site.dialog_open(), '닫기 버튼으로 닫히지 않음')


# ---- v2 동작 고정값: 표시된 작업에서 기대값을 바꾼다 ----

@test()
def d05_book_return_found(site):  # Task 5에서 전환
    site.open()
    site.search('책 반납')
    check('book-return' in site.result_ids()[:3], f'책 반납 상위 3개 {site.result_ids()[:3]}')
