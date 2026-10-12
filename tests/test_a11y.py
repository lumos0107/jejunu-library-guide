"""접근성(P1-12): 포커스, 구조, 대비, 누르는 영역, 동작 줄이기."""
from harness import check, test

CONTRAST = """([fgSel, bgSel]) => {
  const rgb = s => s.match(/\\d+(\\.\\d+)?/g).slice(0, 3).map(Number);
  const lum = c => { const [r, g, b] = c.map(v => { v /= 255; return v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4; });
    return 0.2126 * r + 0.7152 * g + 0.0722 * b; };
  const fg = rgb(getComputedStyle(document.querySelector(fgSel)).color);
  const bg = rgb(getComputedStyle(document.querySelector(bgSel)).backgroundColor);
  const [a, b] = [lum(fg), lum(bg)].sort((x, y) => y - x); return (a + 0.05) / (b + 0.05); }"""


@test()
def t_structure_roles(site):
    site.open()
    check(site.page.locator('#category-grid button h3').count() == 0, 'button 안 h3 남음')
    for sel in ('#scope-tabs', '#category-tabs'):
        check(site.page.get_attribute(sel, 'role') == 'group', f'{sel} role=group 없음')
    check(site.page.locator('#category-grid [aria-pressed]').count() == 0, '상황 카드에 aria-pressed')
    check(site.page.get_attribute('[data-book="loan"]', 'aria-pressed') == 'false', '책 상황 버튼 초기 aria-pressed')


@test()
def t_focus_after_load_more(site):
    site.open()
    site.page.focus('#load-more')
    site.page.keyboard.press('Enter')
    site.page.wait_for_timeout(120)
    active = site.page.evaluate('document.activeElement.closest(".service-card") !== null')
    check(active, '더 보기 뒤 포커스가 새 카드로 가지 않음')


@test()
def t_focus_after_category_card(site):
    site.open()
    site.category_card('space')
    check(site.page.evaluate('document.activeElement.id') == 'services-title', '상황 카드 뒤 포커스 이동 안 됨')


@test()
def t_contrast(site):
    site.open()
    # 결함 재현(v2 미달): .book-guide p:not(.eyebrow) on #e9eee4 4.31, .resource-filters>div on soft 4.48
    # 회귀 확인(v2 통과): .coverage on paper 4.86, 상세 조건 칸 dt on soft (S11)
    site.scope('resource')
    pairs = [('.book-guide p:not(.eyebrow)', '.book-guide'), ('.resource-filters > div', '.resource-filters'), ('.coverage', 'body')]
    site.open_any('group')
    pairs.append(('.detail-conditions dt', '.detail-conditions div'))
    for fg, bg in pairs:
        ratio = site.page.evaluate(CONTRAST, [fg, bg])
        check(ratio >= 4.5, f'{fg} on {bg} 대비 {ratio:.2f}')
    # 포커스 링: file://에서는 스타일시트 규칙을 읽을 수 없으므로, 실제로 포커스를 준 요소의 계산된 색을 본다
    site.close_detail()
    site.page.focus('#search-input')  # 입력창은 어떻게 포커스해도 :focus-visible이 적용된다
    ring, green = site.page.evaluate("""() => { const t = document.createElement('div'); t.style.color = 'var(--green)';
      document.body.append(t); const g = getComputedStyle(t).color; t.remove();
      return [getComputedStyle(document.activeElement).outlineColor, g]; }""")
    check(ring == green, f'포커스 링 색 {ring}(var(--green) = {green} 기대)')


SMALL = """sels => Array.from(document.querySelectorAll(sels)).filter(e => e.offsetParent !== null || e.closest('dialog[open]'))
  .map(e => [e.textContent.trim().slice(0, 12), Math.round(e.getBoundingClientRect().height)]).filter(([, h]) => h < 44)"""


@test(viewport='mobile')
def t_target_sizes_mobile(site):
    site.open()
    small = site.page.evaluate(SMALL, '#scope-tabs button, #category-tabs button, #search-form button, .book-options button, '
                               '.service-card button, #load-more, nav a, .header-search')
    site.category_tab('space')
    site.search('교외접속')  # 필터 칩과 0건 해제 버튼이 보이는 상태(S11)
    small += site.page.evaluate(SMALL, '.active-filters button, #empty-clear-filters')
    site.open_any('group')
    small += site.page.evaluate(SMALL, '#close-dialog, #detail-content a.primary, .related button, .material-list a')
    check(not small, f'44px 미만: {small[:6]}')


@test()
def t_reduced_motion(site):
    site.page.emulate_media(reduced_motion='reduce')
    site.page.add_init_script("""window.__scrolls = []; const o = Element.prototype.scrollIntoView;
      Element.prototype.scrollIntoView = function (a) { window.__scrolls.push(a && a.behavior); return o.call(this, a); };""")
    site.open()
    site.category_card('space')
    check(site.page.evaluate('window.__scrolls').count('smooth') == 0, '동작 줄이기인데 smooth 스크롤')
