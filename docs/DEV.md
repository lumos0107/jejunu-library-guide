# 개발 안내

## 로딩 순서와 전역
index.html이 아래 순서로 읽는다(모두 `defer`라 문서 순서대로 실행).
1. `data.js` → `window.LIBRARY_GUIDE` (생성물, 직접 고치지 않음)
2. `js/lib.js` → `window.LG` (순수 함수: 이스케이프·https 링크 검사 등. DOM을 만지지 않음)
3. `js/app.js` → 전역을 만들지 않는 IIFE

새 스크립트는 이 목록에 추가하고, 전역은 `window.LG`(순수 함수)·`window.LG_CONFIG`(설정) 외에는 만들지 않는다.

## 명령
- 테스트: `python tests/smoke.py --stage 1 --browsers chromium,webkit --modes file,http`
- 데이터 검사: `python tests/check_data.py --stage 1`

## 데이터
- 편집 원본은 `data/*.json`이다. 고친 뒤 `python tools/build_data.py`로 data.js를 다시 만든다.
- `python tools/build_data.py --check`: data.js가 원본과 같은지 확인(쓰지 않음).
- `data/common-text.json`: 검색 색인에서 뺄 공통 문장(10회 이상 반복되는 caution·steps·메뉴 question). 화면 표시는 그대로다.
