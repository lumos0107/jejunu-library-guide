// 도서관의 쓸모 — 화면 코드
// 로딩 순서(index.html, 모두 defer): data.js → js/lib.js → js/app.js
(() => {
  'use strict';

  const { categories, services, resources = [], directory = [], checkedAt } = window.LIBRARY_GUIDE;
  const records = [...services, ...resources, ...directory];

  const $ = selector => document.querySelector(selector);
  const { escapeHtml: escape, safeUrl } = window.LG;
  const byId = id => records.find(s => s.id === id);
  const categoryName = id => categories.find(c => c.id === id)?.name || id;
  const kindName = kind => ({ guide: '이용 가이드', resource: '전자정보원', menu: '공식 메뉴 위치' }[kind] || '이용 가이드');
  const searchIndex = window.LG.buildIndex(records, window.LIBRARY_GUIDE.commonText);
  const emptyHeading = $('#empty h3').textContent;
  const emptyText = $('#empty p').innerHTML;

  const DEFAULT_STATE = { scope: 'all', category: 'all', query: '', audience: 'all', subject: 'all',
    sourceType: 'all', access: 'all', menuGroup: 'all', limit: 12 };
  const state = { ...DEFAULT_STATE };
  let currentMatches = [];

  const notes = {
    all: '이용 가이드 ' + services.length + '개 · 전자정보원 ' + resources.length + '개 · 공식 메뉴 위치 ' + directory.length
      + '개를 함께 검색해요. 같은 서비스가 가이드와 공식 메뉴에 각각 표시될 수 있어요.',
    guide: '공개 상세 안내를 학생의 질문으로 풀어쓴 가이드예요. 실제 서비스의 이용 대상·비용·인증 조건은 공식 안내를 다시 확인해주세요.',
    resource: '전자정보원 원목록 97개에서 중복 1개를 합친 96개 + 전자책 목록의 추가 2개예요. 공개자료·시범서비스·나머지 목록 등재 항목은 이용조건이 다릅니다.',
    menu: '공식 상위 6개 메뉴의 하위 메뉴 89개예요. 메뉴 위치·링크를 확인했지만 모든 하위 본문이나 로그인 후 기능을 검증한 것은 아닙니다.'
  };

  function card(s) {
    const resource = s.recordKind === 'resource';
    const menu = s.recordKind === 'menu';
    const badges = resource
      ? '<span class="badge">' + escape(s.subject) + '</span><span class="badge '
        + (s.accessType === '시범서비스' ? 'trial' : s.accessType === '공개자료 안내' ? 'open' : '') + '">'
        + escape(s.accessType) + '</span>'
      : (s.channel ? '<span class="badge">' + escape(s.channel) + '</span>' : '')
        + (s.eligibilityNote ? '<span class="badge target">' + escape(s.eligibilityNote) + '</span>' : '')
        + (s.costNote ? '<span class="badge">' + escape(s.costNote) + '</span>' : '');
    return '<article class="service-card"><div class="record-kind"><span>' + kindName(s.recordKind) + '</span><span>'
      + escape(resource ? s.sourceType : menu ? s.menuGroup : categoryName(s.category)) + '</span></div><h3>'
      + escape(s.name) + '</h3>'
      + (!menu ? '<p class="service-question">' + escape(resource ? s.subject + ' 분야에서 활용하기' : s.question) + '</p>' : '')
      + '<p class="service-description' + (menu ? ' official-path' : '') + '">' + escape(s.description) + '</p>'
      + '<div class="badges">' + badges + '</div><button type="button" data-open="' + escape(s.id) + '" aria-label="'
      + escape(s.name) + ' ' + kindName(s.recordKind) + ' 보기">'
      + (resource ? '설명·매뉴얼 보기' : menu ? '공식 메뉴 위치 보기' : '이용 방법 보기')
      + '<span aria-hidden="true">↗</span></button></article>';
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
    if (state.audience !== 'all') list.push({ key: 'audience', label: FILTER_LABELS.audience[state.audience] || state.audience });
    if (state.scope === 'resource') {
      for (const key of ['subject', 'sourceType', 'access']) if (state[key] !== 'all') list.push({ key, label: state[key] });
    }
    if (state.scope === 'menu' && state.menuGroup !== 'all') list.push({ key: 'menuGroup', label: state.menuGroup });
    return list;
  }

  const SELECT_OF = { audience: 'audience', subject: 'resource-subject', sourceType: 'resource-type', access: 'resource-access', menuGroup: 'menu-group' };

  function clearFilter(key) {
    state[key] = 'all';
    if (SELECT_OF[key]) $('#' + SELECT_OF[key]).value = 'all';
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
    document.querySelectorAll('button[data-category]').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.category === state.category)));
    document.querySelectorAll('button[data-scope]').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.scope === state.scope)));
    const filters = activeFilters();
    $('#active-filters').innerHTML = filters.map(f => '<button type="button" data-clear="' + escape(f.key) + '">'
      + escape(f.label) + ' <span aria-hidden="true">×</span><span class="sr-only"> 필터 해제</span></button>').join('')
      + (filters.length > 1 ? '<button type="button" data-clear="all">모두 해제</button>' : '');
    $('#active-filters').hidden = filters.length === 0;
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
  $('#category-grid').innerHTML = categories.map((c, i) => '<button type="button" class="category-card" data-category="' + escape(c.id)
    + '"><span class="category-index"><span>0' + (i + 1) + ' / ' + escape(c.name)
    + '</span><span aria-hidden="true">↗</span></span><h3>' + escape(c.question) + '</h3><p>' + escape(c.desc) + '</p></button>').join('');
  $('#category-tabs').innerHTML = [{ id: 'all', name: '모든 상황' }, ...categories].map(c => '<button type="button" data-category="'
    + escape(c.id) + '" aria-pressed="' + (c.id === 'all') + '">' + escape(c.name) + '</button>').join('');
  $('#scope-tabs').innerHTML = [['all', '전체 검색', records.length], ['guide', '이용 가이드', services.length],
    ['resource', '전자정보원', resources.length], ['menu', '공식 메뉴', directory.length]]
    .map(([id, label, count]) => '<button type="button" data-scope="' + id + '" aria-pressed="' + (id === 'all') + '">' + label
      + '<span class="scope-count">' + count + '</span></button>').join('');
  for (const [id, values] of [['resource-subject', [...new Set(resources.map(r => r.subject))]],
    ['resource-type', [...new Set(resources.map(r => r.sourceType))]],
    ['menu-group', [...new Set(directory.map(r => r.menuGroup))]]]) {
    $('#' + id).insertAdjacentHTML('beforeend', values.map(v => '<option value="' + escape(v) + '">' + escape(v) + '</option>').join(''));
  }
  $('#coverage').textContent = services.length + '개 활용 안내 · ' + resources.length + '개 전자정보원 · 공식 메뉴 '
    + directory.length + '개도 검색할 수 있어요';
  $('#checked-at').textContent = checkedAt.replaceAll('-', '.');

  // 오늘 날짜는 그릴 때마다 다시 계산한다(열어 둔 채 자정을 넘겨도 다음 조작 때 맞게, S14)
  const todayNow = () => window.LG.todayLocal();
  const noticeHtml = n => '<li><strong>' + escape(n.text) + '</strong> <span class="notice-period">'
    + escape(n.startsOn.replaceAll('-', '.')) + ' ~ ' + escape(n.endsOn.replaceAll('-', '.')) + '</span>'
    + (safeUrl(n.link) ? ' <a href="' + escape(safeUrl(n.link)) + '" target="_blank" rel="noopener noreferrer">공지 보기 ↗</a>' : '')
    + '<span class="notice-source">확인일 ' + escape(n.checkedAt.replaceAll('-', '.')) + '</span></li>';

  function renderNotices() {
    const items = window.LG.activeNotices(window.LIBRARY_GUIDE.notices, todayNow());
    $('#notices').innerHTML = items.length
      ? '<h2 class="sr-only">지금 이 시기 공지</h2><ul>' + items.map(noticeHtml).join('') + '</ul>' : '';
    $('#notices').hidden = items.length === 0;
  }

  const relatedMap = window.LIBRARY_GUIDE.related || {};

  const dialog = $('#detail-dialog');

  const isListUrl = url => /#\/search\/er(-ebook)?$/.test(url || '');

  function findHint(s) {
    if (s.findHint) return s.findHint;
    if (s.recordKind === 'resource' && isListUrl(s.source)) return "공식 목록 위쪽의 검색 칸에 '" + s.name + "'을(를) 입력하세요.";
    return '';
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
      : menu ? '공식 메뉴로 이동하기' : '공식 안내 열기';
    const url = safeUrl(s.source);
    const hint = findHint(s);
    const facts = s.facts || [];
    const auth = facts.filter(f => f.kind === 'auth').map(f => f.text);
    const locations = facts.filter(f => f.kind === 'location');
    const exceptions = facts.filter(f => f.kind !== 'location');
    const notices = window.LG.activeNotices(window.LIBRARY_GUIDE.notices, todayNow(), id);
    const materials = (s.materials || []).filter(m => safeUrl(m.url));
    const related = (relatedMap[id] || []).filter(byId);

    $('#detail-content').innerHTML = '<h2 id="detail-title">' + escape(s.name) + '</h2>'
      + '<p class="detail-question">' + escape(resource ? s.subject + ' · ' + s.sourceType : menu ? s.description : s.question) + '</p>'
      + '<div class="detail-top">'
      + (url ? '<a class="primary" data-official href="' + escape(url) + '" target="_blank" rel="noopener noreferrer">' + sourceLabel + ' ↗</a>'
        : '<p>공식 링크를 확인할 수 없어요.</p>')
      + (hint ? '<p class="find-hint">' + escape(hint) + '</p>' : '')
      + '</div>'
      + '<dl class="detail-conditions">'
      + '<div><dt>대상</dt><dd>' + escape(s.eligibilityNote || '공식 안내에서 확인') + '</dd></div>'
      + '<div><dt>비용</dt><dd>' + escape(s.costNote || s.cost) + '</dd></div>'
      + '<div><dt>인증·로그인</dt><dd>' + escape([s.login, ...auth].filter(Boolean).join(' · ')) + '</dd></div>'
      + '</dl>'
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
      + '원문 표기에 오류·과거 정보가 있을 수 있으니 이용 직전 공식 안내를 확인하세요.</p>';
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
      if (clear.dataset.clear === 'all') activeFilters().forEach(f => clearFilter(f.key));
      else clearFilter(clear.dataset.clear);
      state.limit = 12;
      render();
      return;
    }
    const open = e.target.closest('[data-open]');
    if (open) { openDetail(open.dataset.open); return; }
    const scope = e.target.closest('[data-scope]');
    if (scope) {
      e.preventDefault();
      changeScope(scope.dataset.scope);
      if (scope.tagName === 'A') $('#services').scrollIntoView({ behavior: 'smooth' });
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
        $('#services').scrollIntoView({ behavior: 'smooth' });
      }
      render();
      return;
    }
    const book = e.target.closest('[data-book]');
    if (book) {
      const result = bookCases[book.dataset.book];
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
  });
  $('#audience').addEventListener('change', e => { state.audience = e.target.value; state.limit = 12; render(); });
  for (const [id, key] of [['resource-subject', 'subject'], ['resource-type', 'sourceType'], ['resource-access', 'access'], ['menu-group', 'menuGroup']]) {
    $('#' + id).addEventListener('change', e => { state[key] = e.target.value; state.limit = 12; render(); });
  }
  $('#load-more').addEventListener('click', () => { state.limit += 12; render(); });
  $('#reset').addEventListener('click', reset);
  $('#empty-reset').addEventListener('click', () => { reset(); $('#search-input').focus(); });
  $('#empty-clear-filters').addEventListener('click', () => {
    const widen = $('#empty-clear-filters').dataset.widen === 'true';
    activeFilters().forEach(f => clearFilter(f.key));
    state.limit = 12;
    if (widen) changeScope('all');
    else render();
  });

  render();
  performance.mark('first-render');
})();
