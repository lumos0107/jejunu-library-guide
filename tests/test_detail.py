"""상세: 공식 버튼과 조건이 대화상자의 보이는 첫 화면 안, 예외는 요약 바로 아래, 찾는 방법, 위치, 면책 1회."""
from harness import check, test

# 요소가 화면 높이와 대화상자의 보이는 영역 양쪽 안에 있는지(대화상자는 높이 제한 + 자체 스크롤이 있다, S7)
VISIBLE = """sel => { const el = document.querySelector(sel); const dlg = document.querySelector('#detail-dialog');
  if (!el || !dlg) return false; const r = el.getBoundingClientRect(); const d = dlg.getBoundingClientRect();
  return r.height > 0 && r.top >= Math.max(0, d.top) && r.bottom <= Math.min(window.innerHeight, d.bottom); }"""

ORDER = """() => { const els = ['.detail-top', '.detail-conditions', '.detail-exceptions', '.detail-steps']
    .map(s => document.querySelector('#detail-content ' + s));
  if (els.some(e => !e)) return 'missing ' + els.map(e => !!e).join(',');
  for (let i = 1; i < els.length; i++) {
    if (!(els[i - 1].compareDocumentPosition(els[i]) & Node.DOCUMENT_POSITION_FOLLOWING)) return 'order ' + i;
  }
  return 'ok'; }"""


def visible_in_dialog(site, selector):
    return site.page.evaluate(VISIBLE, selector)


@test()
def t_official_button_above_fold_desktop(site):
    site.open()
    for rid in ('stats', 'group', 'er-044', 'remote'):
        site.open_any(rid)
        check(visible_in_dialog(site, '#detail-content a.primary[data-official]'), f'{rid}: 공식 버튼이 첫 화면 밖')
        site.close_detail()


@test(viewport='mobile')
def t_detail_above_fold_mobile(site):
    site.open()
    for rid, must in (('group', '재학생·교직원'), ('maker', '재학생·교직원'), ('locker', '재학생'), ('delivery', '장애인'),
                      ('er-057', '초대링크'), ('er-085', '학내 IP')):
        site.open_any(rid)
        for sel in ('#detail-content a.primary[data-official]', '.detail-conditions'):
            check(visible_in_dialog(site, sel), f'{rid} {sel}: 390×844 첫 화면 밖')
        check(must in site.page.inner_text('.detail-conditions'), f'{rid}: 조건 요약에 "{must}" 없음')
        site.close_detail()
    for rid in ('stats', 'er-044'):
        site.open_any(rid)
        check(visible_in_dialog(site, '.find-hint'), f'{rid}: 찾는 방법이 첫 화면 밖')
        site.close_detail()


@test()
def t_detail_order_exceptions_below_summary(site):
    site.open()
    site.open_any('group')
    order = site.page.evaluate(ORDER)
    check(order == 'ok', f'상세 순서(공식 버튼 → 조건 → 확인할 점 → 이용 방법)가 아님: {order}')
    check(site.page.locator('#detail-content details').count() == 0, '예외를 접어 두면 안 됨(K21)')
    text = site.page.inner_text('.detail-exceptions')
    check('30분' in text and '자동 취소' in text, f'예약 규칙이 확인할 점에 없음: {text[:80]}')


@test()
def t_find_hint_for_list_links(site):
    site.open()
    site.open_any('er-044')
    hint = site.page.inner_text('.find-hint')
    check('JSTOR Collection' in hint and '검색 칸' in hint, f'자료 찾는 방법: {hint}')
    site.close_detail()
    site.open_any('stats')
    check('Statista' in site.page.inner_text('.find-hint'), '가이드 찾는 방법 없음')


@test()
def t_find_hint_index_button(site):
    """공식 목록은 거른 상태를 주소에 담지 않는다 → 가나다·ABC 버튼과 실제로 찾아지는 검색어로 안내(D18)."""
    site.open()
    got = site.page.evaluate("""() => [['카피킬러', '까치', 'JSTOR', 'jstor', '3D 자료', '(사)한국', ''].map(window.LG.indexButton),
        ['카피킬러', '학술정보원', 'JSTOR', ''].map(window.LG.objectParticle)]""")
    check(got[0] == ['카', '', 'J', 'J', '기타', '기타', ''], f'가나다·ABC 버튼 {got[0]}')
    check(got[1] == ['를', '을', '을(를)', '을(를)'], f'조사 {got[1]}')
    for rid, must, must_not in (('er-007', ["'카' 버튼", "'카피킬러'를"], []),
                                ('er-087', ["'T' 버튼", '검색 칸'], []),
                                ('er-093', ["'C' 버튼", "'CAS SciFinder'을(를)"], ['SciFinder Trial']),
                                ('er-050', ["'K' 버튼", "'KSDC'을(를)"], [])):
        site.open_any(rid)
        hint = site.page.inner_text('.find-hint')
        check(all(m in hint for m in must) and not any(m in hint for m in must_not), f'{rid} 찾는 방법: {hint}')
        site.close_detail()
    ebook = next(r['id'] for r in site.data()['resources'] if r['source'].endswith('#/search/er-ebook'))
    site.open_any(ebook)
    hint = site.page.inner_text('.find-hint')
    check('버튼' not in hint and '검색 칸' in hint, f'{ebook}: 전자책 목록에는 가나다 줄이 없음: {hint}')


@test()
def t_location_channel_and_disclaimer_once(site):
    site.open()
    site.open_any('print')
    loc = site.page.inner_text('.detail-location')
    check('3층 3열람실' in loc and '미디어라운지' in loc, f'위치 {loc}')
    check(site.page.locator('#detail-content .detail-disclaimer').count() == 1, '면책 문구 1개가 아님')
    check(site.page.locator('#detail-content .kind-note, #detail-content .material-note').count() == 0, '중복 면책 남음')
    site.close_detail()
    site.open_any('group')
    check('키오스크' in site.page.inner_text('.detail-channel'), '이용 경로(앱·키오스크)가 상세에 없음')


@test()
def t_auth_fact_with_source(site):
    site.open()
    site.open_any('er-085')
    check('학내 IP' in site.page.inner_text('.detail-conditions'), 'WSJ 인증 예외가 조건 요약에 없음')
    item = site.page.locator('.detail-exceptions li', has_text='학내 IP')
    check(item.count() == 1 and item.locator('a').count() == 1, '인증 사실의 출처 링크가 확인할 점에 없음')


GRAD_NO_NOTE = r"""(() => { let v; Object.defineProperty(window, 'LIBRARY_GUIDE', { configurable: true, get() { return v; },
  set(x) { const g = x.services.find(s => s.audience === 'grad');
           x.services.push(Object.assign({}, g, { id: 'grad-fixture', eligibilityNote: undefined, facts: [] })); v = x; } }); })();"""


@test()
def t_eligibility_default_and_unknown(site):
    site.page.add_init_script(GRAD_NO_NOTE)
    site.open()
    site.open_any('grad-fixture')  # 대학원 대상이지만 대상 요약(eligibilityNote)이 없는 가이드
    check('공식 안내에서 확인' in site.page.inner_text('.detail-conditions'), '대상 기본값이 "공식 안내에서 확인"이 아님')
    site.close_detail()
    site.open_any('seat')
    check('미확인' in site.page.inner_text('.detail-conditions'), '일반열람실 대상 미확인 표시 없음')


@test()
def t_card_condition_badges(site):
    site.open()
    site.search('그룹스터디룸')
    check(site.page.locator('.service-card .badge', has_text='재학생·교직원').count() >= 1, '카드 대상 배지 없음')
    check(site.page.locator('.badge', has_text='세부 조건 확인').count() == 0, "'세부 조건 확인' 배지 남음")


# 대표 과업·조건 카드의 대상·비용·인증 요약을 글자 그대로 고정한다(뜻이 뒤집혀도 부분 일치로 통과하지 않게, 5차 평가)
EXPECTED_CONDITIONS = {
    'group': ('재학생·교직원', '공식 안내 확인', '필요'),
    'hours': ('공식 안내에서 확인', '안내 열람', '안내 열람 불필요'),
    'book-return': ('공식 안내에서 확인', '연체료 유무는 공식 안내에서 확인하지 못함', '현장 반납'),
    'print': ('공식 안내에서 확인', '인쇄 100원 · 복사 50원 · 스캔 무료', '공식 안내에 인증 언급 없음'),
    'remote': ('공식 안내에서 확인', '자료별 범위 확인', '필요 · 일부 자료는 별도 가입·등록 필요(WSJ·CAS·NICE bizLINE·Value-Search)'),
    'thesis-submit': ('본교 석·박사 학위취득예정자', '공식 안내 확인', '필요'),
    'editage': ('공식 안내에서 확인', '유료 협약가 · 견적 확인',
                '학교 웹메일 조건 · 학교 웹메일 계정(@jejunu.ac.kr)으로 공동웹페이지를 통해 신청 필수'),
    'maker': ('재학생·교직원', '공식 안내 확인', '필요'),
    'locker': ('재학생(휴학생·연체도서가 있는 경우 신청 불가)', '공식 안내 확인', '필요'),
    'delivery': ('도서관 방문이 어려운 장애인 이용자(담당자 승인 후)', '무료 택배 안내', '필요'),
    'seat': ('대상 미확인', '공식 안내 확인', '필요'),
    'er-085': ('공식 안내에서 확인', '구독·무료 여부 확인', '개별 안내 확인 · 회원가입 후 이용, 학내 IP 대역에서만 등록 가능'),
    'er-057': ('공식 안내에서 확인', '구독·무료 여부 확인',
               '개별 안내 확인 · 개인 ID 등록 때 기관계정 대신 회사직원 초대링크 입력(문의 research@jejunu.ac.kr, 064-754-2229~30)'),
}


@test()
def t_condition_summaries_exact(site):
    site.open()
    for rid, expected in EXPECTED_CONDITIONS.items():
        site.open_any(rid)
        got = tuple(site.page.eval_on_selector_all('.detail-conditions dd', 'els => els.map(e => e.textContent)'))
        check(got == expected, f'{rid} 조건 요약 {got} != {expected}')
        site.close_detail()


@test()
def t_all_details_open(site):
    """모든 레코드(가이드·자료·메뉴)의 상세가 오류 없이 열리고, 제목과 공식 버튼(또는 안내 문구)이 있다."""
    site.open()
    bad = site.page.evaluate("""() => {
      const d = window.LIBRARY_GUIDE, recs = [...d.services, ...d.resources, ...d.directory], bad = [];
      for (const r of recs) {
        const b = document.createElement('button'); b.dataset.open = r.id; b.hidden = true; document.body.append(b); b.click(); b.remove();
        const title = document.querySelector('#detail-title');
        const ok = title && title.textContent === r.name
          && (document.querySelector('#detail-content a[data-official]') || document.querySelector('#detail-content').textContent.includes('공식 링크를 확인할 수 없어요'));
        if (!ok) bad.push(r.id);
        document.querySelector('#detail-dialog').close();
      }
      return { total: recs.length, bad };
    }""")
    check(not bad['bad'], f"상세가 제대로 열리지 않음 {bad['bad'][:5]} / {bad['total']}")


@test()
def t_card_button_names_include_visible_text(site):
    site.open()
    bad = site.page.eval_on_selector_all('#service-grid .service-card button[data-open]', """els => els
      .filter(b => !(b.getAttribute('aria-label') || '').includes(b.textContent.replace('↗', '').trim()))
      .map(b => b.getAttribute('aria-label'))""")
    check(not bad, f'버튼 이름에 보이는 글이 없음(WCAG 2.5.3): {bad[:3]}')
    site.open_any('stats')
    described = site.page.evaluate("""() => { const a = document.querySelector('#detail-content a[data-official]');
      const id = a && a.getAttribute('aria-describedby'); return !!(id && document.getElementById(id)
        && document.getElementById(id).classList.contains('find-hint')); }""")
    check(described, '공식 버튼이 찾는 방법과 연결되지 않음(aria-describedby)')


# 자료 카드에도 확인된 대상·비용 요약이 있으면 배지로 보인다
RESOURCE_NOTE = r"""(() => { let v; Object.defineProperty(window, 'LIBRARY_GUIDE', { configurable: true, get() { return v; },
  set(x) { const r = x.resources.find(r => r.id === 'er-044'); r.eligibilityNote = '테스트 대상'; r.costNote = '테스트 비용'; v = x; } }); })();"""


@test()
def t_resource_card_note_badges(site):
    site.page.add_init_script(RESOURCE_NOTE)
    site.open()
    site.search('JSTOR')
    text = site.page.inner_text('#service-grid')
    check('테스트 대상' in text and '테스트 비용' in text, '자료 카드에 대상·비용 배지가 없음')
