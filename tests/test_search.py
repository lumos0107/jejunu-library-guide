"""검색 기본 정비(P1-08)."""
import json
import pathlib

from harness import check, test

CASES = json.loads((pathlib.Path(__file__).resolve().parents[1] / 'data' / 'normalize-cases.json').read_text(encoding='utf-8'))


@test()
def t_js_normalize_vectors(site):
    site.open()
    got = site.page.evaluate('cases => cases.map(([i]) => window.LG.normalize(i))', CASES)
    bad = [(i, e, g) for (i, e), g in zip(CASES, got) if e != g]
    check(not bad, f'JS 정규화 불일치 {bad}')


@test()
def t_symbol_only_query(site):
    site.open()
    for q in ('!!!', '???', '“”', '   '):
        site.search(q)
        check(site.page.locator('#empty').is_visible(), f'{q}: 안내 화면 없음')
        check('검색어를 입력하세요' in site.page.inner_text('#empty'), f'{q}: 안내 문구 없음')
        check(site.card_count() == 0, f'{q}: 카드가 보임')


@test()
def t_free_word_zero(site):
    site.open()
    for q in ('무료', '무제한'):
        site.search(q)
        check(site.count() == 0, f'{q}: {site.count()}건(①에서는 0건)')


@test()
def t_remote_noise_removed(site):
    site.open()
    site.search('교외접속')
    ids = site.result_ids()
    check(ids and ids[0] == 'remote', f'교외접속 1위 {ids[:3]}')
    check(site.count() < 10, f'교외접속 {site.count()}건(공통 문장 잡음)')


@test()
def t_quote_and_joined_words(site):
    site.open()
    site.search('“통계”')
    check('stats' in site.result_ids()[:3], f'“통계” 상위 3개 {site.result_ids()[:3]}')
    for q in ('영어논문', '영어 논문'):
        site.search(q)
        check('overseas' in site.result_ids()[:3], f'{q} 상위 3개 {site.result_ids()[:3]}')


@test()
def t_no_cross_field_match(site):
    site.open()
    site.search('앱휴대폰')
    check('mobile' not in site.result_ids(), '필드 경계를 넘어 일치함')


@test(clock=False)  # 가짜 시계는 performance.mark를 기록하지 않는다
def t_perf_marks(site):
    site.open()
    check(site.page.evaluate("performance.getEntriesByName('first-render').length") == 1, 'first-render 표시 없음')
    site.search('통계')
    check(site.page.evaluate("performance.getEntriesByName('search-rendered').length") >= 1, 'search-rendered 표시 없음')


@test()
def t_cleared_query_shows_all(site):
    site.open()
    d = site.data()
    site.search('통계')
    site.search('')
    check(site.count() == sum(len(d[k]) for k in ('services', 'resources', 'directory')), '입력을 지웠는데 처음 목록이 아님')


# 메뉴는 단계 문장을 검색하지 않고, 가이드는 검색한다(PRD 6장 ① 표, S2)
STEP_FIXTURE = r"""(() => { let v; Object.defineProperty(window, 'LIBRARY_GUIDE', { configurable: true, get() { return v; },
  set(x) { x.directory.push(Object.assign({}, x.directory[0], { id: 'menu-fixture', steps: ['zzmenustepzz'] }));
           x.services.push(Object.assign({}, x.services[0], { id: 'guide-fixture', steps: ['zzguidestepzz'] })); v = x; } }); })();"""


@test()
def t_search_fields_by_kind(site):
    site.page.add_init_script(STEP_FIXTURE)
    site.open()
    site.search('zzmenustepzz')
    check(site.count() == 0, '메뉴의 단계 문장이 검색됨')
    site.search('zzguidestepzz')
    check('guide-fixture' in site.result_ids(), '가이드의 단계 문장은 검색돼야 함')
