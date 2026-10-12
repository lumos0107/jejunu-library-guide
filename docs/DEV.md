# 개발 안내

## 로딩 순서와 전역
index.html이 아래 순서로 읽는다(모두 `defer`라 문서 순서대로 실행).
1. `data.js` → `window.LIBRARY_GUIDE` (생성물, 직접 고치지 않음)
2. `js/app.js` → 전역을 만들지 않는 IIFE

새 스크립트는 이 목록에 추가하고, 전역은 `window.LG`(순수 함수)·`window.LG_CONFIG`(설정) 외에는 만들지 않는다.

## 명령
- 테스트: `python tests/smoke.py --stage 1 --browsers chromium,webkit --modes file,http`
