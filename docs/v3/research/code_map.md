# 도서관 가이드 v2 코드 맵 (① 계획용 조사)

- 조사일 2026-10-13. 사이트 폴더는 읽기만 했다.
- 근거 자료(같은 폴더):
  - `app.pretty.js`: app.js를 풀어쓴 사본. 원본 줄은 `// L n`으로 표기
  - `styles.pretty.css`, `data_profile.txt`
  - `replicate_out.txt`: L15 검색식을 그대로 재현한 결과
  - `ui_out.txt`·`misc_out.txt`: Playwright Chromium file:// 실측
- 아래 `Ln`은 app.js 원본 줄 번호다.

## 1. 파일 개요

| 파일 | 크기·줄 | 내용 |
|---|---|---|
| index.html | 7,756B·12줄 | 정적 골격. `<head>`에 `<script src="data.js" defer>` 다음 `<script src="app.js" defer>`. 둘 다 defer라서 파싱 뒤 문서 순서대로 실행된다 |
| data.js | 313,537B·6,338줄 | `window.LIBRARY_GUIDE = {…};\n`. 본문은 2칸 들여쓴 JSON이다. 접두어 + `json.dumps(obj, ensure_ascii=False, indent=2)` + `;\n`이 원본과 **바이트 단위로 같다**(실측) |
| app.js | 13,716B·40줄 | IIFE `(() => {'use strict'; … })();` 하나. 전역을 만들지 않는다 |
| styles.css | 13,293B·3줄 | L1: 기본 규칙과 미디어쿼리. L2: 주석 "두 번째 버전". L3: v2 추가 규칙 |

- 전역은 `window.LIBRARY_GUIDE` 하나다. `metadata`는 L3에서 구조 분해만 하고 쓰지 않는다.
- `tests/`, `tools/`, `*.py`, `package.json`은 없다.

## 2. app.js 구조

### 2.1 상수·함수

| L | 이름 | 역할 |
|---|---|---|
| 3–9 | 구조 분해, `records`, `$`, `escape`, `byId`, `categoryName`, `kindName` | `records=[...services,...resources,...directory]`(234개)의 순서가 곧 결과 순서다. `escape`는 ``& < > " '``를 바꾼다. `byId`는 못 찾으면 undefined를 낸다. `kindName`: guide '이용 가이드', resource '전자정보원', menu '공식 메뉴 위치' |
| 10 | `normalized(v)` | `String(v??'').toLocaleLowerCase().normalize('NFKC').replace(/[\s’'·.,!?()\[\]{}_:;/-]/g,'')` |
| 11–12 | `state`, `currentMatches` | 2.2 |
| 13 | `notes` | 범위별 안내문. resource는 "원목록 97개에서 중복 1개를 합친 96개 + …" |
| 14 | `card(s)` | 카드 HTML (2.4) |
| 15–20 | `render()` | 2.3 |
| 21 | `reset()` | state·입력창·select 5개를 초기화하고 render |
| 22 | `changeScope(s)` | scope를 바꾸고 `category='all'`, limit=12, render. **다른 필터는 그대로 둔다** |
| 23–27 | 첫 1회 그리기 | 상황 카드, 상황 탭, 범위 탭(개수 포함), select option(`escape` 적용), `#coverage`, `#checked-at` |
| 28·37 | `relatedMap`, `bookCases` | 2.5 |
| 30–35 | `openDetail(id)` | 2.5 |
| 36·38·39 | 리스너, 첫 `render()` | 2.6 |

### 2.2 state

`{scope:'all',category:'all',query:'',audience:'all',subject:'all',sourceType:'all',access:'all',menuGroup:'all',limit:12}`

- scope: all, guide, resource, menu
- audience의 grad 값은 필터에 쓰이지 않는다.
- subject·sourceType·access는 resource 범위에서만, menuGroup은 menu 범위에서만 적용된다.
- limit은 12씩 늘어난다.

### 2.3 검색·필터·render (L15–19)

```js
const terms=state.query.trim().split(/\s+/).filter(Boolean).map(normalized);
currentMatches=records.filter(s=>(state.scope==='all'||s.recordKind===state.scope)&&(state.category==='all'||s.category===state.category)
 &&(state.audience!=='undergrad'||s.audience!=='grad')
 &&(state.scope!=='resource'||(…subject…)&&(…sourceType…)&&(state.access==='all'||s.accessType===state.access))
 &&(state.scope!=='menu'||state.menuGroup==='all'||s.menuGroup===state.menuGroup)
 &&terms.every(term=>normalized([s.name,s.question,s.description,s.officialDescription,s.keywords,s.caution,s.subject,s.sourceType,s.menuGroup,s.menuSubgroup,...(s.steps||[])].join(' ')).includes(term)));
```

**검색 방식:**
- `filter(Boolean)`이 정규화보다 먼저 실행된다. 그래서 기호만 입력하면 `[""]`가 되고 234건이 모두 나온다.
- 필드를 이어 붙인 뒤 공백을 지우고 비교한다. 그래서 필드 경계를 넘어 일치한다(실측: "앱휴대폰" → mobile).
- 검색하지 않는 필드: channel, login, cost, audience, category, source, materials.
- 단어끼리는 AND로 묶고 부분 문자열로 비교한다. 정렬은 없다.
- 정규식은 “ ” ‘ " ※를 지우지 않는다. 처리 순서도 PRD(NFKC → 소문자)와 반대다.

**render를 부르는 곳:**
- 첫 실행
- 검색어 input·submit
- select 5개의 change
- 더 보기
- `reset`, `changeScope`
- `[data-category]` 클릭

**render가 쓰는 곳:**
- `#service-grid.innerHTML`: 카드 limit개
- `#empty.hidden`
- `#load-more`: hidden과 "더 보기 · n / N"
- `#result-count.textContent`: "전체 검색 · N개 결과 · “q” (가이드 a · 자료 b · 메뉴 c)"
- `#scope-note`
- `#resource-filters`, `#menu-filter`, `#category-tabs`의 hidden
- `button[data-category]`(**상황 카드 포함**)와 `button[data-scope]`의 `aria-pressed`

### 2.4 card(s) (L14)

| 종류 | 위 줄 | 질문 줄 | 배지 | 버튼 |
|---|---|---|---|---|
| guide | 상황 이름 | question | channel, 그리고 grad이면 '대학원 대상', 아니면 '세부 조건 확인' | 이용 방법 보기 |
| resource | sourceType | `subject+' 분야에서 활용하기'` | subject, accessType(class trial/open) | 설명·매뉴얼 보기 |
| menu | menuGroup | 없음(`.official-path`) | guide와 같음 | 공식 메뉴 위치 보기 |

버튼은 `data-open="'+s.id+'"`이고 id를 이스케이프하지 않는다.

### 2.5 openDetail · relatedMap · bookCases

**출력 순서 (L34):**
1. h2, 질문, `.kind-note`, 요약
2. `dl.detail-facts`(channel, login, cost)
3. [resource만] 공식 설명과 `.material-note`
4. 단계 `ol`
5. caution
6. [materials가 있을 때] 링크와 `.material-note`
7. [relatedMap에 있을 때] 관련 버튼
8. **맨 끝** `.detail-source`: `a.primary href="'+escape(s.source)+'"`와 면책

그다음 `showModal()`, `scrollTop=0`, `#close-dialog`에 focus를 준다.

**나머지:**
- **버튼 문구 (L32):** resource는 'er-ebook'으로 끝나면 전자책 목록 문구, 아니면 '공식 전자정보원 목록에서 이름 검색하기'. menu는 '공식 메뉴로 이동하기', guide는 '공식 안내에서 확인하기'.
- **매뉴얼 링크 (L33):** `/^https?:\/\//i`로 걸러서 http도 통과한다.
- **relatedMap (L28):** 키 32개. 대상은 모두 기존 가이드다(검증함). 연결이 없는 가이드는 15개다. 대상이 없으면 `byId(key).name`에서 TypeError가 난다.
- **bookCases (L37):** loan, missing, campus, priority, storage는 각자 같은 id로, 'not-owned'는 [wish, dds]로 간다. `#book-result`에 문단과 `data-open` 버튼을 그리고 aria-pressed를 갱신한다.

### 2.6 이벤트

| 대상 | 이벤트 | 효과 |
|---|---|---|
| document (L38 위임) | click | 우선순위대로 처리한다. ① `[data-open]` → openDetail ② `[data-scope]` → preventDefault, changeScope, A 태그면 `$('#services').scrollIntoView({behavior:'smooth'})` ③ `[data-category]` → `state.category=…;state.query='';…$('#search-input').value='';`, 상황 카드면 `state.scope='guide'`와 smooth 스크롤 ④ `[data-book]` |
| `#search-input` / `#search-form` | input / submit | `state.query=value.trim()`, limit=12, render |
| `#audience`와 select 4개 | change | 해당 state 값을 바꾼다 |
| `#load-more`, `#reset`, `#empty-reset` | click | limit+=12 / reset / reset 후 입력창 focus |
| `#close-dialog`, `dialog` | click | 닫기 / 사각형 밖을 누르면 닫기 |

- Escape는 기본 dialog 동작이고, 닫으면 연 버튼으로 포커스가 돌아온다(실측).
- `history`·`location`·`hash`는 한 번도 쓰지 않는다.

## 3. DOM 계약

| index.html 요소 | app.js가 하는 일 |
|---|---|
| `#category-grid` `#category-tabs`(aria-label만) `#scope-tabs`(role 없음) | L23–25 innerHTML. 버튼 `[data-category]` `[data-scope]` |
| 헤더 `a[data-scope="resource"]`, hero `button[data-open]`(stats·maker·night), `button[data-book]` 6개 | 위임 클릭 |
| `#book-result`(aria-live, hidden) | innerHTML |
| `#search-form` `#search-input` | 값 읽기·쓰기(L21·38·39), focus |
| `#audience` `#resource-subject` `#resource-type` `#resource-access` `#menu-group` | change. L26에서 option 추가 |
| `#resource-filters` `#menu-filter` `#empty` `#load-more` | hidden. `#empty` 문구는 고정 |
| `#result-count`(aria-live) `#scope-note` `#coverage` `#checked-at` | textContent |
| `#service-grid` | 카드 innerHTML |
| `#reset` `#empty-reset` | click |
| `#services` | 스크롤 대상 |
| `#detail-dialog` `#detail-category` `#close-dialog` `#detail-content` | 상세 |

- CSS의 `.service-category`는 쓰이지 않는다.
- index.html의 `.muted`에는 CSS 규칙이 없다.

## 4. styles.css

- **토큰:** `--ink:#1c3029` `--muted:#66716a` `--green:#245b43` `--paper:#fbfaf6` `--line:#dddeda` `--soft:#eef2ea` `--white:#fff` `--radius:16px` `--font`
- **하드코딩 색:** 포커스 #73a98e, 배경 #f0f3ec·#e9eee4, 배지 3쌍 등 15개 이상. 다크 모드는 없다.
- **구간:**
  - L1: 기본 → 헤더 → hero → 상황 → 책 → 검색·`.tabs` → result-heading → 카드·배지 → empty → about → footer → dialog → 미디어쿼리
  - L3: scope-tabs, resource-filters, record-kind, badge.trial/open, load-more, official-excerpt, material-*, kind-note, 재정의 규칙
- **미디어쿼리:** `@media(max-width:850px)`, `@media(max-width:560px)` 2벌(L1·L3), `@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}*{transition:none!important}}`
- **중복 정의:**

  | 선택자 | 처음 | 다시 |
  |---|---|---|
  | `.result-heading` | L1 `align-items:center` | L3 `flex-start;gap:14px` |
  | `.result-heading p` | L1 `margin:0` | L3 `max-width:75%` |
  | `.service-card h3` | L1 글꼴 | L3 `overflow-wrap:anywhere` |
  | `.coverage` | L1 | L3 |
  | `.kind-note` | L3 | L3 |
  | `button` | cursor | color(따로 정의) |

- **포커스·대비:**
  - 포커스 규칙은 `button,a,input,select:focus-visible{outline:3px solid #73a98e;outline-offset:4px}` 하나다. 대비는 paper 2.58, soft 2.38로 3:1 미달이다.
  - muted 글자 대비: soft 4.48(`.resource-filters>div`, `.detail-facts dt`), #e9eee4 4.31(`.book-guide p`), paper 4.86.
  - `html{scroll-behavior:smooth}`
- **누르는 영역(실측):** 데스크톱은 `.tabs button` 36, `#reset` 22, nav 22, 카드 버튼 35px. 모바일은 상황 탭 33, 범위 탭 37, 찾기 34px.
- **모바일 nav:** `@media(max-width:560px){nav>a:not(.official){display:none}}`가 있어 '공식 도서관'만 남는다.

## 5. data.js

**최상위:**
- `checkedAt`
- `categories[6]` `{id,name,question,desc}`
- `services[47]`, `resources[98]`, `directory[89]`
- `metadata`: 97·96·2·98·89·47, duplicateMerged

| 종류 | 필드 |
|---|---|
| guide (47) | id, name, question, category, description, audience(all 45, grad 2), channel, login, cost, caution, steps(3~4개, 합 142), source, keywords(문자열), checkedAt, recordKind. materials는 `hours`에만 있다 |
| resource (er-001~098) | question이 없다. 추가로 subject(13종), officialDescription, sourceType(6종), accessType(이용 범위 확인 88/공개자료 안내 6/시범서비스 4), materials(150개, 빈 배열 13), duplicateCount |
| menu (menu-001~089) | guide 필드에 menuGroup(6종), menuSubgroup을 더한다 |

**반복 문구:**
- resource: caution 86개("…무료·원문 이용을 보장하지 않습니다…"), steps 96·90·90개
- menu: question 89개, caution 88개, keywords 89개가 모두 "… 공식 메뉴"로 끝남

**값 표기와 확인일:** 가이드의 channel 31종, login 20종, cost 19종(26/47이 '공식 안내 확인'). checkedAt은 모두 같은 날짜다.

**화면에서 쓰는 곳:**
- 검색: 2.3의 필드
- 필터: recordKind, category, audience, subject, sourceType, accessType, menuGroup
- 카드: 2.4
- 상세: channel, login, cost, officialDescription, steps, caution, duplicateCount, materials, source, checkedAt
- 표시하지 않음: keywords, menuSubgroup

## 6. ① 요구사항별 코드 접점

| ID | 바뀔 곳 | 위험·메모 |
|---|---|---|
| P1-01 | 새 `tests/` | 7장. "지난 Playwright 확인 35개 항목" 목록은 docs/·_비공개/ 어디에도 없다. WebKit이 설치되어 있지 않다(ms-playwright에는 chromium만 있음). 헤드리스에서는 smooth 스크롤 애니메이션이 관찰되지 않으므로 `scrollIntoView` 인자를 가로채 검사한다 |
| P1-02 | app.js·CSS 전체 | 파일을 나누면 IIFE 지역 변수를 공유할 수 없다. 공용 전역 하나와 defer 순서를 문서화해야 한다. CSS 중복을 합칠 때는 L3가 이기던 값을 보존해야 한다 |
| P1-03 | L3, L28, L37 | relatedMap·bookCases는 JS 객체 표기라 Node `vm`으로 추출한다(실측 성공). 이 둘을 옮기면 L3과 L34·L38의 참조가 바뀐다 |
| P1-04 | L6, L14·23·24·34·38의 이스케이프하지 않은 id, L34 `href=escape(s.source)`(스킴 검사 없음), L33 http 허용 | 지금 id는 모두 `[a-z0-9-]+`이고 source는 모두 https다. relatedMap·bookCases 대상의 존재 여부도 검사해야 한다 |
| P1-05 | 데이터: `hours`·`remote`·`print`, 키워드, er-007·er-035·er-010의 공통 caution. 화면: openDetail에 `facts` 출력 | `hours` caution은 "06:00~24:00"인데 keywords에는 "시험기간 … 24시간"이 있다. remote: "교외에서도 … 학교 인증으로 접속", "별도 프로그램이나 설정 없이". print: cost "스캔 무료", "인쇄 100원". 키워드: remote "무료", er-037 "무료", er-098 "무제한" |
| P1-06 | 새 공지 데이터(위치 미정), 홈 컨테이너, hours 상세 | 날짜는 로컬 `YYYY-MM-DD` 문자열로 비교한다. hours의 공지 링크는 10/26 이후 낡는다. Playwright 1.62에 `page.clock`이 있다 |
| P1-07 | L14 배지, L34 상단, `eligibilityNote`/`costNote` | 조건 근거: group·maker "재학생·교직원 대상", locker "재학생 대상", 책나래 `delivery`(audience all인데 "장애인 이용자"), WSJ er-085 "학내 IP 대역에서만 등록 가능", NICE er-057 "[회사직원 초대링크]" |
| P1-08 | L10, L15, 안내 상태, 정렬 | ① `editage`의 고유 caution "무료는 일부 부가서비스에 해당하며…"가 남아 "무료 0건"이 실패한다. ② er-098 공식 원문의 "무제한"이 검색 필드에 있다. ③ "영어논문"은 데이터에 붙여 쓴 곳이 없어 키워드를 보강해야 한다. ④ 메뉴 keywords의 "공식 메뉴" 때문에 '메뉴' 95건이 남는다. ⑤ 필드별 비교에서 공통 문구를 빼면 교외접속 98→2, 무료 89→3이 되고 QA-v2 수치는 그대로다(시뮬레이션). ⑥ 여러 단어 검색의 ① 정렬 기준이 없다 |
| P1-09 | L38 `query=''` 제거, `.result-heading` 근처 필터 표시, `#empty` "필터를 풀면 N건" | 드러나지 않는 상태가 셋이다. ① changeScope가 다른 필터를 유지한다(실측: 자료→전체→자료로 돌아오면 5건) ② 상황 카드가 scope를 guide로 강제한다 ③ audience는 모든 범위에 적용된다 |
| P1-10 | 헤더·검색 위치, 560 미디어쿼리 | 검색창이 2,061/6,584px에 있다. `#search-input`을 L21·38·39가 참조하므로 입력창을 복제하면 id가 겹친다. sticky로 만들면 `scroll-padding-top:24px`에 영향이 간다 |
| P1-11 | L31–34 순서·면책, L32, `.detail-source` | 버튼 위치/화면 높이(실측): stats 793/763px, 모바일 JSTOR 1327/715px. 면책은 guide 2개, resource 4개다. 목록형 source는 자료 98개와 가이드 8개다. 위치(층·호실) 데이터가 없다 |
| P1-12 | L16·39 포커스, L38 smooth 2곳, `--muted`·`#73a98e`, L23 `h3`, 탭 role, 44px | aria-pressed 버튼 묶음에는 tablist보다 `role=group`이 맞다 |
| P1-13 | 가이드 레코드 추가, relatedMap | 47→48, 234→235가 된다. 탭·coverage·notes는 length로 계산해 자동 반영되지만 `metadata.guideCount`·README·QA는 손으로 고쳐야 한다. 상위 3개에 들려면 ① 정렬이 필요하다 |
| P1-14 | head(og·favicon 없음), 버전 표시, `#empty`·L34에 폼 링크(`encodeURIComponent`) | https만 허용 |
| P1-15 | L9, L13, L14 '세부 조건 확인'(가이드 45 + 메뉴 87), L25·27·31·32·34 문구, index.html의 nav·"제공 표시"·"공식 분류"·about, `.audience-control` | option **value는 데이터 값과 같아야 하므로** 이름만 바꾼다. '국외DB'는 표시용 대응표가 필요하다. RESEARCH.md L3 "33개" |

## 7. QA 기준선 (v2 실측)

**표기:** 유지 = ①에서도 같아야 한다. → Pn = 그 기능에서 바뀌므로 결함 재현 테스트로 바꾼다.

| # | 입력 → 기대 | 구분 |
|---|---|---|
| Q1 | 데이터: 가이드 47, 자료 98, 메뉴 89, 합계 234. id 고유. er-001~098·menu-001~089 존재 | 개수 → P1-13, ID 유지 |
| Q2 | 필수 필드 누락 0, source는 모두 https, 자료 매뉴얼 링크 150, password 입력 0, 콘솔 오류 0 | 유지 |
| Q3 | 첫 화면 "전체 검색 · 234개 결과 (가이드 47 · 자료 98 · 메뉴 89)", 카드 12, "더 보기 · 12 / 234" | → P1-13 |
| Q4 | 무선인터넷 → wifi + menu-046. SDI → 가이드 1 + 메뉴 2. 외국어 교정 → 2 + 2. Naxos → culture + er-055. CAS BioFinder → er-096. 크레마클럽 → ebook + er-098 | 유지 |
| Q5 | 전자정보원 98, 공개자료 6, 시범서비스 4, 통계·기업 5, My Library 17, 더 보기 → 24 | 유지 |
| Q6 | Statista 상세: facts 3, 매뉴얼 1, 맨 끝 버튼 '공식 전자정보원 목록에서 이름 검색하기' → `#/search/er` | → P1-05·07·11·15 |
| Q7 | 가이드 + 학부생 45. 전체 + 학부생 230. 전체 + 대학원생 234 | → P1-13·15 |
| Q8 | 상황 카드 '공부 공간' → 가이드 5, 학부생이면 seat·group·hours·floor | 유지 |
| Q9 | 없는 검색어 → `#empty`. 초기화 → 234 | 유지 |
| Q10 | '학교에 없는 책' → 희망도서·상호대차 버튼, aria-pressed | 유지 |
| Q11 | 390×844: scrollWidth 390, JSTOR 1건, 상세 폭 ≤ 뷰포트(실측 354px. QA-v2의 339px는 쓰지 않는다), Escape·배경 클릭으로 닫힘 | 유지 |
| D1 | `!!!`·`???` → 234 | → P1-08 |
| D2 | 무료 → 89 | → P1-08 (0건) |
| D3 | 교외접속 98, 인증 110 | → P1-08 |
| D4 | “통계”, 영어논문 → 0 | → P1-08 |
| D5 | 책 반납 → loan·missing·delivery. 학위논문 1위 overseas | → P1-13, P1-08 |
| D6 | 상황 탭이 검색어를 지움. 상황 + "통계" → 0건 고정 문구 | → P1-09 |
| D7 | 공식 버튼이 화면 밖 | → P1-11 |
| D8 | 포커스 BODY·카드. h3 6개. role 없음. 탭 33~37px | → P1-12 |
| D9 | 모바일 검색창 2,061px | → P1-10 |
| D10 | '세부 조건 확인' 배지 | → P1-15 |

QA.md(v1)의 수치(33개, 통계 1개)는 쓰지 않는다.

## 8. 결함 검증

| 결함 | 판정 | 근거 |
|---|---|---|
| 기호만 입력하면 234건 | 확인 | L15 `.filter(Boolean).map(normalized)` → `[""]` |
| 2장 0건 검색어 | 확인 | 동의어가 없고, L10에 “ ” ‘ "가 없다 |
| 2장 열람실·좌석 예약에서 seat 빠짐 | 확인 | seat keywords "자리 발권 노트북 열람실 공부"에 '예약'이 없다 |
| 2장 정렬 없음 | 확인 | L15에 sort가 없다 |
| 2장 같은 문장이 결과를 덮음 | 확인 | L15가 `s.caution`과 `...(s.steps||[])`를 검색한다. 메뉴 95 |
| 2장 3중 표시 | 확인 | 묶는 코드가 없다. 같은 source인 메뉴 34개(AUDIT는 33) |
| 2장 숨은 필터·검색어 삭제 | 확인 | input 핸들러가 category를 그대로 둔다. L38 `state.query=''` |
| 4장 모바일 검색·메뉴 | 확인 | 2,061px. CSS `display:none` |
| 4장 탭 크기 | 확인 | `.tabs button{padding:7px 14px}` |
| 4장 URL 상태 없음 | 확인 | history 0회, L38 `preventDefault` |
| 4장 포커스 | 확인 | L16 `hidden=…` 뒤 BODY. L38에 focus 호출이 없다 |
| 4장 동작 줄이기 무시 | 확인(코드) | L38이 `{behavior:'smooth'}`를 조건 없이 쓴다. CSS는 `html{scroll-behavior}`만 되돌린다 |
| 4장 대비·구조 | 확인 | 4.48·4.31·2.58. L23 `<button…><h3>`. 탭 묶음 role 없음 |
| 6장 압축·CSS 중복·테스트 없음 | 확인 | 1·4장 |
| 6장 relatedMap·bookCases | 확인 | L28·L37 |
| 6장 값 표기·오타 | 확인 | 31·20·19종. "(KISA )", "Sage Premire", "최업정보", "트랜드". 매뉴얼/메뉴얼 혼용 |
| 6장 보안 | 확인 | L14 `data-open="'+s.id+'"`, L34 `href="'+escape(s.source)+'"`. 지금 데이터로는 실제 위험이 없다 |

**AUDIT와 다른 수치:**
- "무료"는 87이 아니라 **89건**이다(가이드 2 + 자료 87).
- '세부 조건 확인' 배지는 **가이드 45 + 메뉴 87**에 붙는다.
- 목록형 링크를 쓰는 가이드는 **8개**다.
