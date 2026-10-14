// 제주대 도서관 사용 가이드(비공식) — 순수 함수 모음(window.LG). DOM을 만지지 않는다.
(() => {
  'use strict';
  const LG = (window.LG = window.LG || {});

  LG.escapeHtml = value => String(value ?? '').replace(/[&<>"']/g, c => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  }[c]));

  // https 링크만 허용한다. 그 밖에는 빈 문자열.
  LG.safeUrl = url => (/^https:\/\//i.test(String(url ?? '')) ? String(url) : '');

  // 정규화: NFKC → 소문자 → 공백·문장부호·기호 제거(PRD 6장 2번)
  LG.normalize = value => String(value ?? '').normalize('NFKC').toLocaleLowerCase().replace(/[\s\p{P}\p{S}]/gu, '');
  // 단어 나누기 → 단어마다 정규화 → 빈 단어 버림(6장 1~3번)
  LG.tokenize = query => String(query ?? '').trim().split(/\s+/).map(LG.normalize).filter(Boolean);
  // 이 단어는 근거가 확인된 생성 키워드로만 일치(K10). ①에는 생성 키워드가 없다.
  LG.FREE_WORDS = ['무료', '무제한'];

  // ① 검색 필드: 종류마다 다르다(PRD 6장 ① 표, K9). 메뉴는 질문·단계를 검색하지 않는다.
  LG.SEARCH_FIELDS = {
    guide: ['name', 'question', 'description', 'keywords', 'caution', 'steps'],
    resource: ['name', 'description', 'officialDescription', 'keywords', 'subject', 'sourceType', 'caution', 'steps'],
    menu: ['name', 'description', 'keywords', 'menuGroup', 'menuSubgroup', 'caution']
  };

  // ① 검색 색인. 공통 문장(화면 상수 목록과 똑같은 문장·배열 원소)은 색인에서만 뺀다.
  LG.buildIndex = (records, commonText = {}) => {
    const common = new Set([...(commonText.caution || []), ...(commonText.steps || []), ...(commonText.question || [])]);
    const suffix = commonText.keywordSuffix || '';
    const index = new Map();
    for (const r of records) {
      const raw = [];
      for (const field of LG.SEARCH_FIELDS[r.recordKind] || LG.SEARCH_FIELDS.guide) {
        let value = r[field];
        if (field === 'keywords' && r.recordKind === 'menu' && suffix && String(value || '').endsWith(suffix)) {
          value = String(value).slice(0, -suffix.length);
        }
        for (const v of Array.isArray(value) ? value : [value]) if (v && !common.has(v)) raw.push(v);
      }
      index.set(r.id, { nameNorm: LG.normalize(r.name), fields: raw.map(LG.normalize).filter(Boolean), generated: [] });
    }
    return index;
  };

  LG.matches = (entry, tokens) => tokens.every(t => (LG.FREE_WORDS.includes(t)
    ? entry.generated.includes(t)
    : entry.fields.some(f => f.includes(t))));

  // ① 최소 정렬: 이름에 모든 단어 → 일부 단어 → 나머지(같은 단계 안에서는 기존 순서)
  LG.rankTier = (entry, tokens) => {
    const hits = tokens.filter(t => entry.nameNorm.includes(t)).length;
    return hits === tokens.length ? 0 : hits > 0 ? 1 : 2;
  };

  LG.search = (records, index, tokens) => {
    if (!tokens.length) return records.slice();
    return records
      .map((r, i) => ({ r, i, e: index.get(r.id) }))
      .filter(x => x.e && LG.matches(x.e, tokens))
      .map(x => ({ ...x, tier: LG.rankTier(x.e, tokens) }))
      .sort((a, b) => a.tier - b.tier || a.i - b.i)
      .map(x => x.r);
  };

  // 기기 로컬 날짜 'YYYY-MM-DD'. toISOString은 UTC라 쓰지 않는다(PRD 5장 날짜 규칙).
  LG.todayLocal = (d = new Date()) => d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-'
    + String(d.getDate()).padStart(2, '0');
  // 시작·종료일 당일 포함. 'YYYY-MM-DD' 문자열 비교.
  LG.isActiveOn = (item, today) => (!item.startsOn || item.startsOn <= today) && (!item.endsOn || today <= item.endsOn);
  LG.activeNotices = (notices, today, taskId) => (notices || [])
    .filter(n => LG.isActiveOn(n, today) && (!taskId || (n.taskIds || []).includes(taskId)));

  // 공식 전자정보원 목록의 가나다·ABC 줄 버튼 이름. 공식 거르기와 같은 규칙(2026-10-13 공식 스크립트 확인):
  // 한글은 첫 글자의 초성, 영문은 첫 글자, 숫자·기호는 '기타'. 된소리 초성(ㄲ·ㄸ·ㅃ·ㅆ·ㅉ)은 맞는 버튼이 없어 ''.
  const CHOSEONG = 'ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ';
  const INDEX_LABEL = Object.fromEntries([...'ㄱㄴㄷㄹㅁㅂㅅㅇㅈㅊㅋㅌㅍㅎ'].map((c, i) => [c, '가나다라마바사아자차카타파하'[i]]));
  LG.indexButton = name => {
    const c = String(name ?? '').charAt(0);
    const code = c.charCodeAt(0);
    if (code >= 0xAC00 && code <= 0xD7A3) return INDEX_LABEL[CHOSEONG[Math.floor((code - 0xAC00) / 588)]] || '';
    if (/[A-Za-z]/.test(c)) return c.toUpperCase();
    return c ? '기타' : '';
  };
  // 목적격 조사: 한글로 끝나면 받침에 따라 '을'·'를'. 영문 등은 읽는 법을 알 수 없어 '을(를)'.
  LG.objectParticle = word => {
    const code = String(word ?? '').trim().slice(-1).charCodeAt(0);
    return code >= 0xAC00 && code <= 0xD7A3 ? ((code - 0xAC00) % 28 ? '을' : '를') : '을(를)';
  };

  // 구글 폼 미리 채우기 주소. 폼이 없으면 '' (링크를 숨긴다).
  LG.feedbackUrl = (config, values = {}) => {
    const base = LG.safeUrl(config && config.feedbackFormUrl);
    if (!base) return '';
    const fields = (config && config.feedbackFields) || {};
    const params = ['usp=pp_url'];
    for (const key of ['query', 'card']) {
      if (fields[key] && values[key]) params.push(encodeURIComponent(fields[key]) + '=' + encodeURIComponent(values[key]));
    }
    return base + (base.includes('?') ? '&' : '?') + params.join('&');
  };
})();
