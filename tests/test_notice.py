"""공지: 기간 안에만 보이고, 첫날·마지막 날 포함, 다음 날 숨김. 테스트용 공지(픽스처)를 주입한다(K2)."""
from harness import check, test
from helpers import TEST_NOTICE, notices_fixture

FIXTURE = notices_fixture([TEST_NOTICE])


def at(site, day):
    site.page.clock.set_fixed_time(f'{day}T10:00:00+09:00')
    site.page.add_init_script(FIXTURE)
    site.open()
    return site.page.locator('#notices').is_visible()


@test()
def t_notice_boundaries(site):
    for day, visible in (('2026-10-07', True), ('2026-10-15', True), ('2026-10-26', True)):
        check(at(site, day) == visible, f'{day}: 보임={visible} 이어야 함')


@test()
def t_notice_hidden_after(site):
    check(not at(site, '2026-10-27'), '종료 다음 날에도 보임')


@test()
def t_notice_on_card(site):
    at(site, '2026-10-15')
    site.open_any('hours')
    check('테스트 공지' in site.page.inner_text('#detail-content .detail-notices'), '상세에 공지 없음')


@test()
def t_today_local_midnight(site):
    site.page.clock.set_fixed_time('2026-10-27T00:30:00+09:00')
    site.open()
    check(site.page.evaluate('window.LG.todayLocal()') == '2026-10-27', '한국 시간 자정 직후 날짜가 전날로 계산됨')


@test()
def t_notice_rechecked_after_midnight(site):
    site.page.clock.set_fixed_time('2026-10-26T23:59:00+09:00')
    site.page.add_init_script(FIXTURE)
    site.open()
    check(site.page.locator('#notices').is_visible(), '종료일 밤에는 보여야 함')
    site.page.clock.set_fixed_time('2026-10-27T00:01:00+09:00')
    site.search('통계')  # 다시 그리기
    check(not site.page.locator('#notices').is_visible(), '자정을 넘긴 뒤 다시 그렸는데 공지가 남음(S14)')


@test()
def t_notice_shows_source_when_different(site):
    other = dict(TEST_NOTICE, source='https://lib.jejunu.ac.kr/#/guide/hoo/hoo')
    site.page.clock.set_fixed_time('2026-10-15T10:00:00+09:00')
    site.page.add_init_script(notices_fixture([other]))
    site.open()
    hrefs = site.page.eval_on_selector_all('#notices a', 'els => els.map(e => e.getAttribute("href"))')
    check(other['source'] in hrefs and other['link'] in hrefs, f'공지 링크·출처 {hrefs}')
