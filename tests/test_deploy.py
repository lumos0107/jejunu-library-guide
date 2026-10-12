"""배포 준비(P1-14)."""
from harness import check, test

FORM = """(() => { let v; Object.defineProperty(window, 'LG_CONFIG', { configurable: true, get() { return v; },
  set(x) { x.feedbackFormUrl = 'https://docs.google.com/forms/d/e/TEST/viewform';
           x.feedbackFields = { query: 'entry.1', card: 'entry.2' }; v = x; } }); })();"""


@test()
def t_head_meta(site):
    site.open()
    check(site.page.get_attribute('meta[name="robots"]', 'content') == 'noindex', 'noindex 없음(M4)')
    check(site.page.get_attribute('meta[property="og:title"]', 'content'), 'og:title 없음')
    check(site.page.get_attribute('link[rel="icon"]', 'href') == 'favicon.svg', '파비콘 없음')
    check('비공식' in site.page.inner_text('.site-header'), '헤더에 비공식 표시 없음')


# 실제 config.js 값과 상관없이 돌도록 "폼 없음"도 명시적으로 주입한다(S16)
NO_FORM = """(() => { let v; Object.defineProperty(window, 'LG_CONFIG', { configurable: true, get() { return v; },
  set(x) { x.feedbackFormUrl = ''; v = x; } }); })();"""


@test()
def t_feedback_hidden_without_form(site):
    site.page.add_init_script(NO_FORM)
    site.open()
    site.search('zzqq없는말')
    check(site.page.locator('#feedback-link').is_hidden(), '폼 주소가 없는데 제보 링크가 보임')
    site.open_any('group')
    check(site.page.locator('#detail-content .feedback-link').count() == 0, '폼 주소가 없는데 상세에 제보 링크가 있음')


@test()
def t_feedback_prefilled(site):
    site.page.add_init_script(FORM)
    site.open()
    site.search('zzqq없는말')
    href = site.page.get_attribute('#feedback-link', 'href')
    check(href and href.startswith('https://docs.google.com/forms/') and 'entry.1=' in href, f'제보 링크 {href}')
    check('zzqq' in href, '검색어가 미리 채워지지 않음')


@test()
def t_feedback_card_prefill(site):
    site.page.add_init_script(FORM)
    site.open()
    site.open_any('group')
    href = site.page.get_attribute('#detail-content .feedback-link', 'href')
    check(href and 'entry.2=group' in href, f'상세 제보 링크에 카드 id가 없음: {href}')
