# 개발 안내

## 로딩 순서와 전역
index.html이 아래 순서로 읽는다(모두 `defer`라 문서 순서대로 실행).
1. `data.js` → `window.LIBRARY_GUIDE` (생성물, 직접 고치지 않음)
2. `js/config.js` → `window.LG_CONFIG` (배포 주소·제보 폼 설정)
3. `js/lib.js` → `window.LG` (순수 함수: 이스케이프·https 링크 검사·검색·날짜·제보 주소. DOM을 만지지 않음)
4. `js/app.js` → 전역을 만들지 않는 IIFE

새 스크립트는 이 목록에 추가하고, 전역은 `window.LG`(순수 함수)·`window.LG_CONFIG`(설정) 외에는 만들지 않는다.

## 명령
- 테스트: `python tests/smoke.py --stage 1 --browsers chromium,webkit --modes file,http`
- 데이터 검사: `python tests/check_data.py --stage 1` (검사기 자체는 `tests/test_check_data.py`가 잘못된 데이터로 확인한다)

## 데이터
- 편집 원본은 `data/*.json`이다. 고친 뒤 `python tools/build_data.py`로 data.js를 다시 만든다.
- `python tools/build_data.py --check`: data.js가 원본과 같은지 확인(쓰지 않음).
- `data/common-text.json`: 검색 색인에서 뺄 공통 문장(10회 이상 반복되는 caution·steps·메뉴 question). 화면 표시는 그대로다.

## push와 배포
1. 모든 변경을 커밋한 뒤 `python tools/gate.py` — 통과해야 push한다(커밋하지 않은 변경이 있으면 실패).
2. 처음 한 번(사용자): GitHub 저장소 Settings → Pages → Source를 "Deploy from a branch", Branch를 `main` / `/ (root)`로 저장.
3. push 뒤: `python tools/deploy_check.py https://lumos0107.github.io/jejunu-library-guide/`
4. 배포 주소가 정해지면 `js/config.js`의 `siteUrl`을 채운다. 구글 폼을 만들면 `feedbackFormUrl`과 미리 채우기 entry 이름을 채운다.
5. ① 동안은 `<meta name="robots" content="noindex">`를 유지하고, ② 커뮤니티 공개 때 뺀다.
5-1. 본문 글꼴 다시 만들기: `pip install fonttools brotli` 후 `python tools/build_font.py`(원본 주소·해시 고정, fonts/README.md). 화면 글자가 글꼴에 없으면 데이터 검사가 알려 준다. 디자인 규칙(색은 :root 토큰만, 글자 크기 토큰, 굵기 400·600·700, 0.3초 이상 전환·그라데이션 금지)도 데이터 검사가 본다(D21).
6. 링크 도착 점검: `python tests/check_links.py` → `.tmp/links-report.md`. 공식 사이트에 부담을 주지 않게 하나씩 천천히 연다. 첫 push 전과 월 1회(D14).
   전자정보원 찾는 방법 점검: `python tests/check_er_find.py` → `.tmp/er-find-report.md`. 공식 목록을 한 번씩만 열어 카드마다 버튼·검색어로 그 자료가 찾아지는지 본다. 링크 점검과 같이 월 1회(D18).
7. 저장소 루트의 `.nojekyll`은 지우지 않는다. 없으면 GitHub Pages가 docs/*.md를 noindex 없는 웹페이지로 만든다(게이트가 확인).
