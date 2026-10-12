// 도서관의 쓸모 — 순수 함수 모음(window.LG). DOM을 만지지 않는다.
(() => {
  'use strict';
  const LG = (window.LG = window.LG || {});

  LG.escapeHtml = value => String(value ?? '').replace(/[&<>"']/g, c => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  }[c]));

  // https 링크만 허용한다. 그 밖에는 빈 문자열.
  LG.safeUrl = url => (/^https:\/\//i.test(String(url ?? '')) ? String(url) : '');
})();
