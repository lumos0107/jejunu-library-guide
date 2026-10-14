// 도서관의 쓸모 — 화면 코드
// 로딩 순서(index.html, 모두 defer): data.js → js/config.js → js/lib.js → js/app.js
(() => {
  'use strict';

  const { categories, services, resources = [], directory = [], checkedAt } = window.LIBRARY_GUIDE;
  const records = [...services, ...resources, ...directory];

  const $ = selector => document.querySelector(selector);
  const { escapeHtml: escape, safeUrl } = window.LG;
  const byId = id => records.find(s => s.id === id);
  const categoryName = id => categories.find(c => c.id === id)?.name || id;
  const kindName = kind => ({ guide: '이용 가이드', resource: '논문·자료 사이트(전자정보원)', menu: '공식 사이트 메뉴' }[kind] || '이용 가이드');
  const SOURCE_TYPE_LABEL = { '국외DB': '해외 자료', '국내DB': '국내 자료' };
  const sourceTypeLabel = v => SOURCE_TYPE_LABEL[v] || v;
  const ACCESS_BADGE = { '공개자료 안내': '공개 자료', '시범서비스': '시범 서비스' };  // 배지는 한 가지 모양, 뜻은 글자로(D21)
  const searchIndex = window.LG.buildIndex(records, window.LIBRARY_GUIDE.commonText);
  const emptyHeading = $('#empty h3').textContent;
  const emptyText = $('#empty p').innerHTML;

  const DEFAULT_STATE = { scope: 'all', category: 'all', query: '', audience: 'all', subject: 'all',
    sourceType: 'all', access: 'all', menuGroup: 'all', limit: 12 };
  const state = { ...DEFAULT_STATE };
  let currentMatches = [];

  const notes = {
    all: '이용 가이드, 논문·자료 사이트, 공식 사이트 메뉴를 함께 찾아요. 같은 서비스가 여러 곳에 보일 수 있어요.',
    guide: '학생 질문으로 풀어 쓴 이용 안내예요. 대상·비용·인증은 공식 안내를 다시 확인해 주세요.',
    resource: '도서관 전자자료 목록 98개예요. 공개 자료·시범 서비스·그 밖의 자료는 이용 조건이 달라요.',
    menu: '공식 사이트의 메뉴 89개를 어디서 찾는지 알려 줘요. 로그인 뒤 기능까지 확인한 것은 아니에요.'
  };

  function card(s) {
    const resource = s.recordKind === 'resource';
    const menu = s.recordKind === 'menu';
    // 확인된 대상·비용 요약은 종류와 상관없이 배지로 보인다
    const noteBadges = (s.eligibilityNote ? '<span class="badge">' + escape(s.eligibilityNote) + '</span>' : '')
      + (s.costNote ? '<span class="badge">' + escape(s.costNote) + '</span>' : '');
    const badges = resource
      ? '<span class="badge">' + escape(s.subject) + '</span>' + (ACCESS_BADGE[s.accessType]
        ? '<span class="badge">' + ACCESS_BADGE[s.accessType] + '</span>' : '') + noteBadges
      : (s.channel ? '<span class="badge">' + escape(s.channel) + '</span>' : '') + noteBadges;
    const action = resource ? '설명·매뉴얼 보기' : menu ? '공식 사이트에서 찾는 곳 보기' : '이용 방법 보기';
    return '<article class="service-card"><div class="record-kind"><span>' + kindName(s.recordKind) + '</span><span>'
      + escape(resource ? sourceTypeLabel(s.sourceType) : menu ? s.menuGroup : categoryName(s.category)) + '</span></div><h3>'
      + escape(s.name) + '</h3>'
      + (!menu ? '<p class="service-question">' + escape(resource ? s.subject + ' 분야에서 활용하기' : s.question) + '</p>' : '')
      + '<p class="service-description' + (menu ? ' official-path' : '') + '">' + escape(s.description) + '</p>'
      + '<div class="badges">' + badges + '</div><button type="button" data-open="' + escape(s.id) + '" aria-label="'
      + escape(s.name) + ' ' + action + '">'  // 이름에 보이는 글을 넣는다(WCAG 2.5.3)
      + action + '<span aria-hidden="true">↗</span></button></article>';
  }

  function matchesFilters(s) {
    return (state.scope === 'all' || s.recordKind === state.scope)
      && (state.category === 'all' || s.category === state.category)
      && (state.audience !== 'undergrad' || s.audience !== 'grad')
      && (state.scope !== 'resource' || ((state.subject === 'all' || s.subject === state.subject)
        && (state.sourceType === 'all' || s.sourceType === state.sourceType)
        && (state.access === 'all' || s.accessType === state.access)))
      && (state.scope !== 'menu' || state.menuGroup === 'all' || s.menuGroup === state.menuGroup);
  }

  const FILTER_LABELS = { audience: { undergrad: '학부생' } };

  function activeFilters() {
    const list = [];
    if (state.category !== 'all' && state.scope !== 'resource' && state.scope !== 'menu') {
      list.push({ key: 'category', label: categoryName(state.category) });
    }
    if (state.audience !== 'all' && audienceMatters()) list.push({ key: 'audience', label: FILTER_LABELS.audience[state.audience] || state.audience });
    if (state.scope === 'resource') {
      for (const key of ['subject', 'sourceType', 'access']) if (state[key] !== 'all') list.push({ key, label: selectedLabel(key) });
    }
    if (state.scope === 'menu' && state.menuGroup !== 'all') list.push({ key: 'menuGroup', label: state.menuGroup });
    return list;
  }

  const SELECT_OF = { audience: 'audience', subject: 'resource-subject', sourceType: 'resource-type', access: 'resource-access', menuGroup: 'menu-group' };

  function clearFilter(key) {
    state[key] = 'all';
    if (SELECT_OF[key]) $('#' + SELECT_OF[key]).value = 'all';
  }

  // 칩은 선택 상자에 보이는 글과 같은 말을 쓴다(P1-15)
  function selectedLabel(key) {
    const option = $('#' + SELECT_OF[key]).selectedOptions[0];
    return option ? option.textContent : state[key];
  }

  // 화면에 칩이 없는 숨은 학부생 필터까지 푼다. 복구 수(recoveryCounts)도 학부생 필터 없이 센다
  function clearAllFilters() {
    activeFilters().forEach(f => clearFilter(f.key));
    if (state.audience !== 'all') clearFilter('audience');
  }

  // 0건일 때 복구 안내용 수: 같은 범위에서 필터만 풀었을 때, 범위까지 풀었을 때(S4)
  function recoveryCounts() {
    const tokens = window.LG.tokenize(state.query);
    const count = list => (tokens.length ? window.LG.search(list, searchIndex, tokens).length : list.length);
    return {
      sameScope: count(records.filter(r => state.scope === 'all' || r.recordKind === state.scope)),
      allScopes: count(records)
    };
  }

  // 학부생 필터는 지금 범위·상황에 대학원 대상이 있을 때만 의미가 있다. 입력 중에 깜빡이지 않게 검색어는 보지 않는다
  function audienceMatters() {
    return records.some(r => r.audience === 'grad' && (state.scope === 'all' || r.recordKind === state.scope)
      && (state.category === 'all' || r.category === state.category));
  }

  function render() {
    renderNotices();
    const tokens = window.LG.tokenize(state.query);
    const invalidQuery = state.query !== '' && tokens.length === 0;  // 공백·기호만 입력(S3)
    currentMatches = invalidQuery ? [] : window.LG.search(records.filter(matchesFilters), searchIndex, tokens);

    $('#service-grid').innerHTML = currentMatches.slice(0, state.limit).map(card).join('');
    $('#empty').hidden = currentMatches.length !== 0;
    $('#empty h3').textContent = invalidQuery ? '검색어를 입력하세요' : emptyHeading;
    $('#empty p').innerHTML = invalidQuery ? '글자나 숫자로 된 검색어를 넣어 주세요. 기호만으로는 찾을 수 없어요.' : emptyText;
    $('#load-more').hidden = currentMatches.length <= state.limit;
    $('#load-more').textContent = '더 보기 · ' + Math.min(state.limit, currentMatches.length) + ' / ' + currentMatches.length;

    const kinds = { guide: 0, resource: 0, menu: 0 };
    currentMatches.forEach(s => kinds[s.recordKind]++);
    $('#result-count').textContent = (state.scope === 'all' ? '전체 검색' : kindName(state.scope)) + ' · '
      + currentMatches.length + '개 결과' + (state.query.trim() ? ' · “' + state.query.trim() + '”' : '')
      + (state.scope === 'all' ? ' (가이드 ' + kinds.guide + ' · 자료 ' + kinds.resource + ' · 메뉴 ' + kinds.menu + ')' : '');

    $('#scope-note').textContent = notes[state.scope];
    $('#resource-filters').hidden = state.scope !== 'resource';
    $('#menu-filter').hidden = state.scope !== 'menu';
    $('#category-tabs').hidden = state.scope === 'resource' || state.scope === 'menu';
    document.querySelectorAll('#category-tabs button[data-category]').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.category === state.category)));
    document.querySelectorAll('button[data-scope]').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.scope === state.scope)));
    const filters = activeFilters();
    $('#active-filters').innerHTML = filters.map(f => '<button type="button" data-clear="' + escape(f.key) + '">'
      + escape(f.label) + ' <span aria-hidden="true">×</span><span class="sr-only"> 필터 해제</span></button>').join('')
      + (filters.length > 1 ? '<button type="button" data-clear="all">모두 해제</button>' : '');
    $('#active-filters').hidden = filters.length === 0;
    $('.audience-control').hidden = !audienceMatters();
    const fb = window.LG.feedbackUrl(window.LG_CONFIG, { query: state.query });
    $('#feedback-link').hidden = !fb || currentMatches.length !== 0;
    if (fb) $('#feedback-link').href = fb;
    let recovery = null;
    if (currentMatches.length === 0 && !invalidQuery) {
      const c = recoveryCounts();
      if (filters.length && c.sameScope > 0) recovery = { n: c.sameScope, widen: false };
      else if (c.allScopes > 0 && (filters.length || state.scope !== 'all')) recovery = { n: c.allScopes, widen: true };
    }
    $('#empty-clear-filters').hidden = !recovery;
    if (recovery) {
      $('#empty p').textContent = recovery.widen
        ? '지금 범위와 필터에서는 결과가 없어요. 다른 범위까지 보면 ' + recovery.n + '건이 있어요.'
        : '적용 중인 필터 때문에 결과가 없어요. 필터를 풀면 ' + recovery.n + '건이 있어요.';
      $('#empty-clear-filters').textContent = recovery.widen ? '전체 범위에서 보기' : '필터 모두 해제';
      $('#empty-clear-filters').dataset.widen = String(recovery.widen);
    }
  }

  function reset() {
    Object.assign(state, DEFAULT_STATE);
    $('#search-input').value = '';
    ['audience', 'resource-subject', 'resource-type', 'resource-access', 'menu-group'].forEach(id => { $('#' + id).value = 'all'; });
    render();
  }

  function changeScope(scope) {
    if (scope !== state.scope) {
      Object.assign(state, { subject: 'all', sourceType: 'all', access: 'all', menuGroup: 'all' });
      ['resource-subject', 'resource-type', 'resource-access', 'menu-group'].forEach(sid => { $('#' + sid).value = 'all'; });
    }
    state.scope = scope;
    state.category = 'all';
    state.limit = 12;
    render();
  }

  // 첫 그리기
  // 상황 카드 6개는 index.html에 미리 넣어 둔다(데이터를 받은 뒤 끼워 넣으면 첫 화면이 밀린다, D21). 데이터와 같은지는 데이터 검사가 본다
  $('#category-tabs').innerHTML = [{ id: 'all', name: '모든 상황' }, ...categories].map(c => '<button type="button" data-category="'
    + escape(c.id) + '" aria-pressed="' + (c.id === 'all') + '">' + escape(c.name) + '</button>').join('');
  $('#scope-tabs').innerHTML = [['all', '전체 검색', records.length], ['guide', '이용 가이드', services.length],
    ['resource', '논문·자료 사이트(전자정보원)', resources.length], ['menu', '공식 사이트 메뉴', directory.length]]
    .map(([id, label, count]) => '<button type="button" data-scope="' + id + '" aria-pressed="' + (id === 'all') + '">' + label
      + '<span class="scope-count">' + count + '</span></button>').join('');
  for (const [id, values] of [['resource-subject', [...new Set(resources.map(r => r.subject))]],
    ['resource-type', [...new Set(resources.map(r => r.sourceType))]],
    ['menu-group', [...new Set(directory.map(r => r.menuGroup))]]]) {
    const label = id === 'resource-type' ? sourceTypeLabel : v => v;  // 값은 데이터 그대로, 표시만 바꾼다
    $('#' + id).insertAdjacentHTML('beforeend', values.map(v => '<option value="' + escape(v) + '">' + escape(label(v)) + '</option>').join(''));
  }
  $('#coverage').textContent = services.length + '개 이용 안내 · 논문·자료 사이트 ' + resources.length + '개 · 공식 사이트 메뉴 '
    + directory.length + '개를 찾을 수 있어요';
  $('#checked-at').textContent = checkedAt.replaceAll('-', '.');

  // 오늘 날짜는 그릴 때마다 다시 계산한다(열어 둔 채 자정을 넘겨도 다음 조작 때 맞게, S14)
  const todayNow = () => window.LG.todayLocal();
  const noticeHtml = n => '<li><strong>' + escape(n.text) + '</strong> <span class="notice-period">'
    + escape(n.startsOn.replaceAll('-', '.')) + ' ~ ' + escape(n.endsOn.replaceAll('-', '.')) + '</span>'
    + (safeUrl(n.link) ? ' <a href="' + escape(safeUrl(n.link)) + '" target="_blank" rel="noopener noreferrer">공지 보기 ↗</a>' : '')
    + (safeUrl(n.source) && n.source !== n.link ? ' <a href="' + escape(safeUrl(n.source)) + '" target="_blank" rel="noopener noreferrer">출처</a>' : '')
    + '<span class="notice-source">확인일 ' + escape(n.checkedAt.replaceAll('-', '.')) + '</span></li>';

  // 홈의 공지는 한 줄로 접는다(D21). 확인일은 맨 아래 한 번
  const noticeItem = n => '<li><strong>' + escape(n.text) + '</strong><span class="notice-meta"><span class="notice-period">'
    + escape(n.startsOn.replaceAll('-', '.')) + ' ~ ' + escape(n.endsOn.replaceAll('-', '.')) + '</span>'
    + (safeUrl(n.link) ? ' <a href="' + escape(safeUrl(n.link)) + '" target="_blank" rel="noopener noreferrer">공지 보기 ↗</a>' : '')
    + (safeUrl(n.source) && n.source !== n.link ? ' <a href="' + escape(safeUrl(n.source)) + '" target="_blank" rel="noopener noreferrer">출처</a>' : '')
    + '</span></li>';

  function renderNotices() {
    const items = window.LG.activeNotices(window.LIBRARY_GUIDE.notices, todayNow());
    const box = $('#notices');
    const key = items.map(n => n.id).join('|');
    box.hidden = items.length === 0;
    if (box.dataset.key === key) return;  // 같은 공지면 다시 그리지 않는다(검색할 때마다 펼친 상태가 닫히지 않게)
    box.dataset.key = key;
    const checked = [...new Set(items.map(n => n.checkedAt))].map(d => d.replaceAll('-', '.')).join(' · ');
    box.innerHTML = items.length ? '<h2 class="sr-only">지금 이 시기 공지</h2><details><summary><span class="notice-label">지금 이 시기 '
      + items.length + '건</span><span class="notice-first">' + escape(items[0].text) + '</span></summary><ul>'
      + items.map(noticeItem).join('') + '</ul><p class="notice-checked">확인일 ' + escape(checked) + '</p></details>' : '';
  }

  const relatedMap = window.LIBRARY_GUIDE.related || {};

  const dialog = $('#detail-dialog');

  const isListUrl = url => /#\/search\/er(-ebook)?$/.test(url || '');
  const BANNER_GROUP = '공식 홈 하단 배너';  // 공식 홈 맨 아래 기관 로고 배너. 도착지가 외부 사이트다(D19)

  // 공식 목록은 거른 상태를 주소에 담지 않는다(2026-10-13 확인, D18). 가나다·ABC 버튼과 실제로 찾아지는 검색어로 안내한다
  function findHint(s) {
    if (s.findHint) return s.findHint;
    if (s.recordKind !== 'resource' || !isListUrl(s.source)) return '';
    const term = s.findTerm || s.name;  // findTerm: 공식 이름과 띄어쓰기·Trial 표기가 달라 이름으로는 검색되지 않는 자료
    const typing = "목록 위쪽의 검색 칸에 '" + term + "'" + window.LG.objectParticle(term) + ' 입력하세요.';
    const button = /#\/search\/er$/.test(s.source) ? window.LG.indexButton(s.name) : '';  // 전자책 목록에는 가나다 줄이 없다
    return button ? "공식 목록의 가나다·ABC 줄에서 '" + button + "' 버튼을 누르세요. 또는 " + typing : '공식 ' + typing;
  }

  function factHtml(f) {
    return '<li>' + escape(f.text) + ' <span class="fact-source">(' + escape(String(f.checkedAt).replaceAll('-', '.'))
      + (safeUrl(f.source) ? ', <a href="' + escape(safeUrl(f.source)) + '" target="_blank" rel="noopener noreferrer">출처</a>' : '')
      + ')</span></li>';
  }

  function openDetail(id) {
    const s = byId(id);
    if (!s) return;
    const resource = s.recordKind === 'resource';
    const menu = s.recordKind === 'menu';
    $('#detail-category').textContent = kindName(s.recordKind) + ' · ' + (resource ? s.subject : menu ? s.menuGroup : categoryName(s.category));
    const sourceLabel = resource
      ? (s.source.endsWith('er-ebook') ? '공식 전자책 목록 열기' : '공식 전자정보원 목록 열기')
      : menu ? (s.menuGroup === BANNER_GROUP ? '외부 사이트 열기' : '공식 메뉴로 이동하기') : '공식 안내 열기';
    const url = safeUrl(s.source);
    const hint = findHint(s);
    const facts = s.facts || [];
    const auth = facts.filter(f => f.kind === 'auth').map(f => f.text);
    const locations = facts.filter(f => f.kind === 'location');
    const exceptions = facts.filter(f => f.kind !== 'location');
    const notices = window.LG.activeNotices(window.LIBRARY_GUIDE.notices, todayNow(), id);
    const materials = (s.materials || []).filter(m => safeUrl(m.url));
    const related = (Object.hasOwn(relatedMap, id) ? relatedMap[id] : []).filter(byId);

    $('#detail-content').innerHTML = '<h2 id="detail-title">' + escape(s.name) + '</h2>'
      + '<p class="detail-question">' + escape(resource ? s.subject + ' · ' + sourceTypeLabel(s.sourceType) : menu ? s.description : s.question) + '</p>'
      + '<dl class="detail-conditions">'  // 대상·비용·인증을 먼저 보고 공식 사이트로 간다(D21, 둘 다 첫 화면 안)
      + '<div><dt>대상</dt><dd>' + escape(s.eligibilityNote || '공식 안내에서 확인') + '</dd></div>'
      + '<div><dt>비용</dt><dd>' + escape(s.costNote || s.cost) + '</dd></div>'
      + '<div><dt>인증·로그인</dt><dd>' + escape([s.login, ...auth].filter(Boolean).join(' · ')) + '</dd></div>'
      + '</dl>'
      + '<div class="detail-top">'
      + (url ? '<a class="primary" data-official href="' + escape(url) + '"' + (hint ? ' aria-describedby="detail-find-hint"' : '')
        + ' target="_blank" rel="noopener noreferrer">' + sourceLabel + ' ↗</a>' : '<p>공식 링크를 확인할 수 없어요.</p>')
      + (hint ? '<p class="find-hint" id="detail-find-hint">' + escape(hint) + '</p>' : '')
      + '</div>'
      + (s.channel ? '<p class="detail-channel">이용 경로: ' + escape(s.channel) + '</p>' : '')
      + (notices.length ? '<div class="detail-notices"><h3>지금 이 시기</h3><ul>' + notices.map(noticeHtml).join('') + '</ul></div>' : '')
      + '<div class="detail-exceptions"><h3>이용 전 확인할 점</h3><p class="detail-warning">' + escape(s.caution)
      + (s.duplicateCount > 1 ? '<br>원목록의 같은 이름 ' + s.duplicateCount + '개 항목을 합쳤습니다.' : '') + '</p>'
      + (exceptions.length ? '<ul class="detail-facts-list">' + exceptions.map(factHtml).join('') + '</ul>' : '') + '</div>'
      + (locations.length ? '<div class="detail-location"><h3>위치</h3><ul>' + locations.map(factHtml).join('') + '</ul></div>' : '')
      + '<p class="detail-summary">' + escape(s.description) + '</p>'
      + (resource ? '<h3>공식 목록의 설명</h3><div class="official-excerpt">' + escape(s.officialDescription) + '</div>' : '')
      + '<h3>' + (menu ? '이 메뉴를 찾으려면' : '이렇게 이용해요') + '</h3><ol class="detail-steps">'
      + s.steps.map(step => '<li>' + escape(step) + '</li>').join('') + '</ol>'
      + (materials.length ? '<h3>공식 제공 매뉴얼·관련 링크</h3><div class="material-list">' + materials.map(m => '<a href="'
        + escape(safeUrl(m.url)) + '" target="_blank" rel="noopener noreferrer">' + escape(m.label) + ' ↗</a>').join('') + '</div>' : '')
      + (related.length ? '<h3>함께 보면 좋은 안내</h3><div class="related">' + related.map(key => '<button type="button" data-open="'
        + escape(key) + '">' + escape(byId(key).name) + '</button>').join('') + '</div>' : '')
      + '<p class="detail-disclaimer">공개 안내 확인일 ' + escape(s.checkedAt) + ' · 비공식 학생용 가이드. 학교 계정·개인정보를 수집하지 않아요. '
      + '원문 표기에 오류·과거 정보가 있을 수 있으니 이용 직전 공식 안내를 확인하세요.</p>'
      + (() => { const u = window.LG.feedbackUrl(window.LG_CONFIG, { card: id });
        return u ? '<p><a class="feedback-link" href="' + escape(u) + '" target="_blank" rel="noopener noreferrer">이 안내가 틀렸나요? 알려 주세요 ↗</a></p>' : ''; })();
    if (!dialog.open) dialog.showModal();
    dialog.scrollTop = 0;
    $('#close-dialog').focus();
  }

  $('#close-dialog').addEventListener('click', () => dialog.close());
  dialog.addEventListener('click', e => {
    if (e.target !== dialog) return;
    const r = dialog.getBoundingClientRect();
    if (e.clientX < r.left || e.clientX > r.right || e.clientY < r.top || e.clientY > r.bottom) dialog.close();
  });

  const bookCases = window.LIBRARY_GUIDE.bookCases || {};

  document.addEventListener('click', e => {
    const clear = e.target.closest('[data-clear]');
    if (clear) {
      if (clear.dataset.clear === 'all') clearAllFilters();
      else clearFilter(clear.dataset.clear);
      state.limit = 12;
      render();
      $('#services-title').focus({ preventScroll: true });  // 누른 칩이 사라지므로 포커스를 결과 제목으로
      return;
    }
    const open = e.target.closest('[data-open]');
    if (open) { openDetail(open.dataset.open); return; }
    const scope = e.target.closest('[data-scope]');
    if (scope) {
      e.preventDefault();
      changeScope(scope.dataset.scope);
      if (scope.tagName === 'A') $('#services').scrollIntoView();
      return;
    }
    const cat = e.target.closest('[data-category]');
    if (cat) {
      state.category = cat.dataset.category;
      state.limit = 12;
      if (cat.classList.contains('category-card')) {
        state.query = '';
        $('#search-input').value = '';
        state.scope = 'guide';
        $('#services').scrollIntoView();
      }
      render();
      if (cat.classList.contains('category-card')) $('#services-title').focus({ preventScroll: true });
      return;
    }
    const book = e.target.closest('[data-book]');
    if (book) {
      const result = Object.hasOwn(bookCases, book.dataset.book) ? bookCases[book.dataset.book] : null;
      if (!result) return;
      document.querySelectorAll('[data-book]').forEach(b => b.setAttribute('aria-pressed', String(b === book)));
      $('#book-result').hidden = false;
      $('#book-result').innerHTML = '<p>' + escape(result.text) + '</p>' + result.ids.filter(byId).map(id => '<button type="button" data-open="'
        + escape(id) + '">' + escape(byId(id).name) + ' 이용 방법 ↗</button>').join('');
    }
  });

  $('#search-input').addEventListener('input', e => {
    state.query = e.target.value;  // 원문 그대로(공백만 입력도 구분, S3)
    state.limit = 12;
    render();
    performance.mark('search-rendered');
  });
  $('#search-form').addEventListener('submit', e => {
    e.preventDefault();
    state.query = $('#search-input').value;
    state.limit = 12;
    render();
    $('#services').scrollIntoView({ block: 'start' });
    $('#services-title').focus({ preventScroll: true });  // 키보드로 결과부터 이어서 보게 한다
  });
  $('#audience').addEventListener('change', e => { state.audience = e.target.value; state.limit = 12; render(); });
  for (const [id, key] of [['resource-subject', 'subject'], ['resource-type', 'sourceType'], ['resource-access', 'access'], ['menu-group', 'menuGroup']]) {
    $('#' + id).addEventListener('change', e => { state[key] = e.target.value; state.limit = 12; render(); });
  }
  $('#load-more').addEventListener('click', () => {
    const before = state.limit;
    state.limit += 12;
    render();
    const next = document.querySelectorAll('#service-grid .service-card button')[before];
    if (next) next.focus();
  });
  $('#reset').addEventListener('click', reset);
  $('#empty-reset').addEventListener('click', () => { reset(); $('#search-input').focus(); });
  $('#empty-clear-filters').addEventListener('click', () => {
    const widen = $('#empty-clear-filters').dataset.widen === 'true';
    clearAllFilters();
    state.limit = 12;
    if (widen) changeScope('all');
    else render();
    $('#services-title').focus({ preventScroll: true });
  });

  // 헤더가 화면 위에 붙어 있으므로 스크롤이 헤더 아래에서 멈추게 한다(S12)
  const setScrollPadding = () => {
    document.documentElement.style.scrollPaddingTop = Math.ceil($('.site-header').getBoundingClientRect().height + 12) + 'px';
  };
  setScrollPadding();
  window.addEventListener('resize', setScrollPadding);

  $('.header-search').addEventListener('click', () => {
    $('.top-search').scrollIntoView({ block: 'start' });  // 스크롤은 즉시 이동(부드러운 스크롤은 0.8~1초라 0.3초 규칙에 어긋남, D21)
    $('#search-input').focus({ preventScroll: true });
  });

  render();
  performance.mark('first-render');
})();
