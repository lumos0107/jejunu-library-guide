# 공식 도서관 사이트 전체 점검 — 우리 사이트에 없는 것 (2026-10-13)

배포본을 써 본 사용자가 "도서관 웹사이트 전부 상호작용해보면서 지금 없는거 뭔지 확인해"라고 요청했다. 공식 사이트를 화면마다 열고 눌러 본 결과를 우리 데이터와 비교했다.

## 방법

- 대상: 공식 사이트 https://lib.jejunu.ac.kr (로그인 없이). 2026-10-13, Playwright(Chromium)로 화면을 하나씩 열었다(화면 사이 1.5초 쉼).
- 홈은 구역별로 기록했다: 머리말(로그인·ENGLISH·분관 사이트·전체 메뉴), 알림줄, 팝업, 바로가기 8개, 공지 탭(일반·학술), 이용시간 위젯, 홍보 슬라이드, 연구학습지원 카드 8개, 신착·인기 도서 탭, 기관 로고 배너 6개, 바닥글. 배너 분류 API(3~7)의 연결 주소도 열었다.
- 화면마다 제목·본문 요약·옆 메뉴·본문 링크·버튼·탭을 기록했다. 주소 없이 눌러야 바뀌는 탭(연혁 연대별, 규정 장별, 통합검색 탭 등)은 눌러서 바뀐 내용도 기록했다.
- 모두 243화면(1차 188 + 2차 53, 홈 별도). 지난 '이달의 추천도서·DVD'·우수학술도서·세종도서 같은 보관 화면 87개는 열기만 하고 분석에서 뺐다.
- 비교: 우리 데이터(할 일 안내 48·전자정보원 자료 98·공식 메뉴 94·공지 2)의 공식 버튼·관련 링크·사실 출처·공지 링크가 그 화면을 가리키는지 봤다. 공식 사이트가 상위 주소를 하위 탭으로 넘겨 주는 경우(예: 대출/반납 → 대출/연장/예약)는 연결된 것으로 봤다.
- 수집 코드와 원자료는 작업 폴더에만 두었다.

## 1. 요약

| 구분 | 수 |
|---|---|
| 실제 화면 | 108 |
| 우리 데이터가 가리키지 않는 화면 | 29 (검색 결과 변형·빈 상위 주소·오타 링크 등 9개 포함) |
| 공식 메뉴 카드만 있고 할 일 안내가 없는 화면 | 36 |
| 다른 화면으로 넘어가는 주소 | 45 (로그인 화면으로 16, 홈으로 6) |
| 보관 화면(지난 추천 목록 등) | 87 |

## 2. 학생에게 쓸모 있는데 우리 사이트에 없는 것

| # | 무엇 | 공식 위치 | 공식 내용(요약·인용) | 우리 사이트 지금 |
|---|---|---|---|---|
| 1 | 노트북 사용 가능 구역 | 공지 `#/bbs/notice/6675` (2026-09-22) | "중앙도서관 열람실 내 노트북, 전자기기 등 개인화 기기 사용이 가능한 구역": 1층 로비·PC존 / 2층 로비·타이핑존 / 3층 로비·3·4열람실. "해당 구역에서는 키보드 타건, 마우스 클릭이 가능". 2층 안쪽 자유열람실을 〈타이핑존〉으로 운영 | 열람실 카드에 "노트북 사용 가능 구역은 따로 안내됩니다"만 있음 |
| 2 | 국회도서관·국립중앙도서관 원문 무료 이용(지정 PC) | `#/research/other/assembly` (원문복사/상호대차의 세 번째 탭) | "국회도서관 및 국립중앙도서관 원문을 무료로 이용할 수 있는 서비스", "원문 자료 출력시 프린트 실비는 이용자 부담". 지정 PC: 중앙도서관 1층 PC존 1대(열람만)·1층 제주자료실 1대·3층 3열람실 2대·중앙디지털 1층 미디어라운지 2대(출력 가능), 교대·법학 각 1대(출력 가능), 의학 1대(열람만) | 없음. 국회도서관·국립중앙도서관 배너 카드(D19)와 바로 이어지는 내용 |
| 3 | 상호대차(다른 기관 책 빌리기) 탭 | `#/research/other/ill` | RISS에서 신청, 도착까지 평균 5일, 권당 5,840원(왕복 택배비), 원문복사와 합쳐 학부·대학원생 연 10만원 지원, 수령은 중앙디지털도서관 1층 미디어자료실, 1주일 안에 안 찾으면 반송. 대출기간은 같은 페이지 안에서 "14일(연장 7일)"과 "3주"가 다르다 | 원문복사·상호대차 카드가 원문복사 탭만 연결 |
| 4 | iThenticate 탭 | `#/research/prevent/ithenticate` | "서비스 희망자는 개별적으로 요청 필요"(koreasales@turnitin.com으로 소속·성함·이메일), 가입은 학교 이메일 계정 | 표절 안내 카드 설명에만 언급 |
| 5 | 온라인 이용교육(도서관 이용 동영상) | `#/education/online` → 외부 library.ioneis.com | 시설 안내·자료 검색·서비스 이용 동영상. 신입생은 학번으로 로그인 | 없음 |
| 6 | 학술정보활용교육의 교육일정·교육자료, 10월 DB 온라인 이용교육 | `#/education/calendar`, `#/bbs/dataroom?bulletinCategoryId=6`, 학술공지 6698~6706 | 월별 교육 달력(10월은 "이달의 교육일정이 없습니다"), DBpia·KSDC·KISS·EndNote·Turnitin·ProQuest·Elsevier·EBSCO의 10월 온라인 교육 공지 | 학술정보활용교육 카드가 교육안내 탭만 연결 |
| 7 | JNU 독서주간(지금 진행 중) | 공지 `#/bbs/notice/6561`, 홈 알림줄 | 2026.9.7.~10.16. 럭키세븐 챌린지(2개 이상 주제군에서 7권 이상 대출, 선착순 100명 상품권), 북로그 응모, "연체 탈출! 바로 대출!"(독서주간 한정, 연체도서를 반납하고 요청하면 제재 즉시 해제, 디지털도서관 2층 안내데스크) | '지금 이 시기'에 없음 |
| 8 | 모바일 앱 좌석배정·도서대출 사용법 | `#/service/mobile/seat`, `#/service/mobile/charge` | 앱으로 열람실 좌석 발권·그룹스터디룸 예약·캐럴 선택, NFC 대출 화면 순서 | 모바일 앱 카드는 소개 화면만 |
| 9 | 분관 이용시간 | `#/service/enter/hours` (출입 및 이용시간 탭) | 의학·법학분관 평일 09:00~18:00, 교대분관 1·2층 자료실 평일 09:00~18:00, 3층 열람실 06:00~24:00 | 이용시간 카드는 `#/guide/hoo/hoo`만 연결 |
| 10 | 영어 사이트·분관 사이트 | 머리말 ENGLISH(https://lib.jejunu.ac.kr/en/), 의학·법학전문·교육대학도서관 | 유학생용 영문 홈, 분관별 사이트. 서식자료실에 "외국인 유학생을 위한 도서관 이용안내 리플렛"도 있다 | 없음 |
| 11 | 지금 진행 중인 다른 홈 알림 | 알림줄·팝업, 공지 6922·6921 | (BK21) '전지적 논문시점' 프로그램 신청 2026.10.13.~10.23. 공지 본문이 포스터 이미지라 대상·내용은 확인하지 못했다 | 없음 |
| 12 | 도서관 이용지침, 오시는 길 | `#/guide/rule/use`, `#/guide/location/map` | 이용 규칙 전문, 카카오맵 길찾기 | 규정·위치 메뉴 카드만 있음(이 탭들은 연결 안 됨) |

### 반영(2026-10-13, D20)

1~10과 12는 기존 카드 보완·관련 링크·공지로 반영했다. 2(국가도서관 원문)는 새 할 일 안내 카드로 만들었다. 11(BK21 프로그램)은 본문이 포스터 이미지라 보류했다. 사실 인용은 [official_facts.md 13장](official_facts.md).

## 3. 공식 메뉴 카드만 있고 할 일 안내가 없는 것(②에서 할 일 카드로 묶을 후보)

- **자료 검색(9화면):** 통합검색, 단행본, 연속간행물(구미·일중 학술지 탭), 제주자료, 학위논문, 비도서, 학술논문(Articles), 전자저널, 상세검색. "책·논문을 어떻게 검색하지?"를 설명하는 할 일 안내가 없다(청구기호 카드는 검색한 다음 단계다).
- **읽을거리·독서(10화면):** 신착도서, 인기도서, 이달의 추천도서·추천DVD, 우수학술도서, 세종도서, 책읽는 제주대학교, JNU 북로그, 제주지역신문 「제주메모리」, 프로그램 일정.
- **이용자별 안내(4화면):** 대학원생, 교직원, 졸업생·수료생, 지역주민·도서관회원제(학부생·장애학생은 안내 카드가 있다).
- **도서관 안내 등(14화면):** 연혁, 도서관규정, 일반현황, 조직/연락처, 자료기증, 공지사항(일반·학술), FAQ, 1:1문의, 서식자료실, 시설 전체, 캠퍼스 내 위치, 홈.

## 4. 공식 사이트 쪽 문제로 보이는 것

- 공식 메뉴 '일정' `#/schedule/calendar`는 홈으로 돌아간다(기존 기록).
- 학술정보활용교육 '정규교육신청' 탭 `#/education/result`는 로그인 없이 열면 홈으로 간다. 교육신청결과·원문복사 신청결과·희망도서 신청결과·프로그램 신청결과도 로그인 화면이 아니라 홈으로 간다.
- '최신연구동향서비스' 페이지의 교육자료 링크에 따옴표 오타(`bulletinCategoryId=6”target=`)가 있어 빈 목록이 열린다.
- '학과별 주제가이드' `#/research/subject-guide`는 "준비중입니다"인데 대학원생 안내에서 연결된다.
- 상호대차 페이지 안에서 대출기간이 "14일(연장 7일)"과 "3주"로 다르다.
- 통합검색 등 일부 화면은 브라우저 제목이 비어 있다(" | 제주대학교 중앙도서관").
- 보안 연결(https)이 아닌 링크: RISS 배너, 원문복사·상호대차의 RISS 신청, 온라인 이용교육, 책나래, 캠퍼스 무선인터넷 안내 등.

## 5. 로그인이 필요해 확인하지 못한 것

My Library 화면들(대출·예약·신청 현황, 개인정보), 사물함 신청 게시판, 원문복사·희망도서·맞춤교육 신청서, 로그인·아이디 찾기·비밀번호 재설정. 우리 사이트는 공식 메뉴 카드로 위치만 안내한다.

## 6. 이번에 보지 않은 것

- 도서관 앱(제주대학교 모바일 도서관): 시험기간 야간버스 팝업 같은 앱 전용 공지가 있다(사용자 제보, 웹 공지 6789와 같은 표).
- 분관 사이트 3곳, 영어 사이트, 외부 사이트(RISS 등)의 내부.
- 게시판 글 본문(공지 6789·6675·6561·6922만 열어 봄), 1:1문의 글(비공개).
- 라우터에는 있지만 화면에서 연결되지 않은 주소 7개(`/proxy`, `/logout`, `/kci-search`, `/code`, `/tempitems`, `/endnote`, `/lope.pyxis.license`).

## 부록. 화면 목록(보관 화면 제외)

'우리 연결'은 그 화면을 가리키는 우리 레코드 종류(guide 할 일 안내, resource 전자정보원 자료, menu 공식 메뉴, notice 공지)다.

| 주소 | 제목 | 우리 연결 | 넘어감 |
|---|---|---|---|
| `/` | 제주대학교 중앙도서관 | menu |  |
| `/bbs` | 연혁 | 없음 | → /guide/history/history |
| `/bbs/booklog` | JNU 독서주간: 북로그 | menu |  |
| `/bbs/contact` | 서비스별 연락처 | guide·menu |  |
| `/bbs/dataroom?bulletinCategoryId=6` | 학술정보활용교육 | 없음 |  |
| `/bbs/dataroom?bulletinCategoryId=6%E2%80%9Dtarget%3D` | 학술정보활용교육 | 없음 |  |
| `/bbs/dataroom?bulletinCategoryId=7` | 학술정보활용교육 | 없음 |  |
| `/bbs/faq` | FAQ | menu |  |
| `/bbs/form` | 서식자료실 | menu |  |
| `/bbs/locker` | 제주대학교 중앙도서관 | menu | → /login |
| `/bbs/lost` | 유실물게시판 | guide·menu |  |
| `/bbs/notice` | 공지사항 | menu |  |
| `/bbs/notice?bulletinCategoryId=8` | 공지사항 | menu |  |
| `/bbs/notice?bulletinCategoryId=9` | 공지사항 | menu |  |
| `/bbs/qna` | 1:1문의 | menu |  |
| `/bbs/readingbook` | 책읽는 제주대학교 | menu |  |
| `/bbs/sci` | 등재 학술지 리스트 | guide·menu |  |
| `/bbs/trend` | 최신연구동향서비스 | 없음 |  |
| `/eds/pf/si` | 전자저널 | menu |  |
| `/eds/si` | 학술논문(Articles) | menu |  |
| `/education` | 등재 학술지 리스트 | 없음 | → /bbs/sci |
| `/education/calendar` | 학술정보활용교육 | 없음 |  |
| `/education/guide` | 학술정보활용교육 | guide·menu |  |
| `/education/online` | 온라인이용교육 | 없음 |  |
| `/education/request-result` | 제주대학교 중앙도서관 | menu | → / |
| `/education/result` | 제주대학교 중앙도서관 | 없음 | → / |
| `/guide` | 제주대학교 중앙도서관 | 없음 |  |
| `/guide/donation` | 자료기증 | menu |  |
| `/guide/group` | 조직/연락처 | menu |  |
| `/guide/history` | 연혁 | 없음 | → /guide/history/history |
| `/guide/history/director` | 역대관장 | 없음 |  |
| `/guide/history/history` | 연혁 | menu |  |
| `/guide/hoo` | 이용시간 | 없음 | → /guide/hoo/hoo |
| `/guide/hoo/floor` | 층별안내 | guide |  |
| `/guide/hoo/floor-digital` | 층별안내 | 없음 |  |
| `/guide/hoo/hoo` | 이용시간 | guide·menu |  |
| `/guide/location` | 캠퍼스내 도서관 위치 | menu | → /guide/location/campus |
| `/guide/location/campus` | 캠퍼스내 도서관 위치 | menu |  |
| `/guide/location/map` | 오시는 길 | 없음 |  |
| `/guide/rule` | 도서관규정 | 없음 | → /guide/rule/rule |
| `/guide/rule/donation` | 자료 등록 및 관리 지침 | 없음 |  |
| `/guide/rule/rule` | 도서관규정 | menu |  |
| `/guide/rule/use` | 도서관 이용지침 | 없음 |  |
| `/guide/state` | 일반현황 | menu |  |
| `/guide/system` | 자료 분류체계 | guide·menu |  |
| `/libprg` | 대출/연장/예약 | 없음 | → /service/circulation/charges |
| `/libprg/calendar` | 프로그램 일정 | menu |  |
| `/libprg/culture-lecture` | 프로그램 신청 | guide·menu |  |
| `/mylibrary/abr` | 제주대학교 중앙도서관 | menu | → /login |
| `/mylibrary/blocks` | 제주대학교 중앙도서관 | menu | → /login |
| `/mylibrary/ccl` | 제주대학교 중앙도서관 | menu | → /login |
| `/mylibrary/charges` | 제주대학교 중앙도서관 | menu | → /login |
| `/mylibrary/collections` | 제주대학교 중앙도서관 | menu | → /login |
| `/mylibrary/dashboard` | 제주대학교 중앙도서관 | guide·menu | → /login |
| `/mylibrary/dds/add` | 제주대학교 중앙도서관 | 없음 | → /login |
| `/mylibrary/dds/result` | 제주대학교 중앙도서관 | menu | → / |
| `/mylibrary/educationrequest/add` | 제주대학교 중앙도서관 | 없음 | → /login |
| `/mylibrary/fcl` | 제주대학교 중앙도서관 | menu | → /login |
| `/mylibrary/ibl` | 제주대학교 중앙도서관 | menu | → /login |
| `/mylibrary/libprg/result` | 제주대학교 중앙도서관 | menu | → / |
| `/mylibrary/myinfo` | 제주대학교 중앙도서관 | menu | → /login |
| `/mylibrary/olv/result` | 제주대학교 중앙도서관 | menu | → /login |
| `/mylibrary/request-book/add` | 제주대학교 중앙도서관 | 없음 | → /login |
| `/mylibrary/request-book/result` | 제주대학교 중앙도서관 | menu | → / |
| `/mylibrary/reservations` | 제주대학교 중앙도서관 | menu | → /login |
| `/mylibrary/sdi/keywords/result` | 제주대학교 중앙도서관 | menu | → /login |
| `/new` | 신착도서 | 없음 | → /new/ex |
| `/new/ex` | 신착도서 | menu |  |
| `/new?from-date-received=2026-08-13&to-date-received=2026-10-13` | 신착도서 | 없음 | → /new/ex?from-date-received=2026-08-13&to-date-received=2026-10-13 |
| `/popular-charged-book` | 신착도서 | 없음 | → /new/ex?from-date-received=2026-08-13&to-date-received=2026-10-13 |
| `/popular-charged-book/result` | 인기도서 | menu |  |
| `/research` | 등재 학술지 리스트 | 없음 | → /bbs/sci |
| `/research/correction` | 외국어 교정 공동웹페이지 서비스(에디티지) | guide·menu |  |
| `/research/correction-enago` | 외국어 교정 공동웹페이지 서비스(이나고) | guide·menu |  |
| `/research/offacess` | 교외접속 | guide·menu |  |
| `/research/other` | 원문복사 | menu | → /research/other/dds |
| `/research/other/assembly` | 국가도서관원문이용 | 없음 |  |
| `/research/other/dds` | 원문복사 | guide·menu |  |
| `/research/other/ill` | 상호대차 | 없음 |  |
| `/research/prevent` | 표절예방(Turnitin, iThenticate) | 없음 |  |
| `/research/prevent-copykiller` | 표절예방(카피킬러) | guide·menu·resource |  |
| `/research/prevent/ithenticate` | Ithenticate | 없음 |  |
| `/research/prevent/turnitin` | Turnitin | guide·menu |  |
| `/research/reference` | 참고문헌관리 | guide·menu |  |
| `/research/sdi` | SDI서비스 | guide·menu |  |
| `/research/subject-guide` | 학과별 주제가이드 | 없음 |  |
| `/research/thesis-submission` | 학위논문제출 | guide·menu |  |
| `/research/trend` | 최신연구동향서비스 | guide·menu |  |
| `/sc` | 제주대학교 중앙도서관 | 없음 |  |
| `/sc/academy` | 우수학술도서 | menu |  |
| `/sc/archive` | 제주지역신문 「제주메모리」 | menu |  |
| `/sc/movie` | 이달의 추천DVD | 없음 |  |
| `/sc/movie?scId1=288` | 이달의 추천DVD | menu |  |
| `/sc/recommend` | 이달의 추천도서 | menu |  |
| `/sc/sejong` | 세종도서 | menu |  |
| `/schedule/calendar` | 제주대학교 중앙도서관 | menu | → / |
| `/search` | 제주대학교 중앙도서관 | 없음 | → /total-search |
| `/search/cr` | 제주대학교 중앙도서관 | 없음 |  |
| `/search/cr/ex` | 연속간행물 | menu |  |
| `/search/ebook` | 제주대학교 중앙도서관 | 없음 |  |
| `/search/ebook/ex` | 전자책 | 없음 |  |
| `/search/elearning` | 동영상 강의 | guide·menu |  |
| `/search/er` | 전자정보원 | guide·menu·resource |  |
| `/search/er-ebook` | 전자책 | guide·menu·resource |  |
| `/search/ex` | 상세검색 | 없음 |  |
| `/search/journal?journalType=AA` | 연속간행물 | 없음 |  |
| `/search/journal?journalType=CJ` | 연속간행물 | 없음 |  |
| `/search/local` | 제주대학교 중앙도서관 | 없음 | → /total-search |
| `/search/local/ex` | 제주자료 | menu |  |
| `/search/mon` | 제주대학교 중앙도서관 | 없음 | → /total-search |
| `/search/mon/ex` | 단행본 | menu |  |
| `/search/nonbook` | 제주대학교 중앙도서관 | 없음 |  |
| `/search/nonbook/ex` | 비도서 | menu |  |
| `/search/thesis` | 제주대학교 중앙도서관 | 없음 | → /total-search |
| `/search/thesis/ex` | 학위논문 | menu |  |
| `/search?mashup=PYXIS` | 제주대학교 중앙도서관 | 없음 | → /total-search |
| `/service` | 대출/연장/예약 | 없음 | → /service/circulation/charges |
| `/service/absent-book-report` | 부재도서 신고 | guide·menu |  |
| `/service/booknarae` | 책나래서비스 | guide·menu |  |
| `/service/campus-loan` | 캠퍼스대출 | guide·menu |  |
| `/service/ccl` | 보존서고 자료이용 | guide·menu |  |
| `/service/circulation` | 대출/연장/예약 | guide·menu | → /service/circulation/charges |
| `/service/circulation/charges` | 대출/연장/예약 | guide·menu |  |
| `/service/circulation/return` | 대출/연장/예약 | guide |  |
| `/service/enter` | 출입 | 없음 | → /service/enter/mobileid |
| `/service/enter/hours` | 이용시간 | 없음 |  |
| `/service/enter/mobileid` | 출입 | guide·menu |  |
| `/service/facility` | 전체 | menu | → /service/facility/all |
| `/service/facility/all` | 전체 | menu |  |
| `/service/facility/carrel` | 캐럴 | guide |  |
| `/service/facility/makerstudio` | 메이커스튜디오 | guide |  |
| `/service/facility/readingroom` | 일반열람실 | guide |  |
| `/service/facility/studyroom` | 그룹스터디룸 | guide |  |
| `/service/fcl` | 우선정리도서 | guide·menu |  |
| `/service/lan` | 무선인터넷 | guide·menu |  |
| `/service/locker` | 사물함 | guide·menu |  |
| `/service/mobile` | 모바일 어플리케이션 소개 | guide | → /service/mobile/introduction |
| `/service/mobile/charge` | 도서대출 | 없음 |  |
| `/service/mobile/introduction` | 모바일 어플리케이션 소개 | guide·menu |  |
| `/service/mobile/seat` | 좌석배정 | 없음 |  |
| `/service/night-bus` | 야간버스 사용 | guide·menu |  |
| `/service/olv` | 타도서관 열람의뢰 | guide·menu |  |
| `/service/print` | 스캔/인쇄/복사 | guide·menu |  |
| `/service/request-book` | 희망도서신청 | guide·menu |  |
| `/service/reservations` | 야간 예약도서 대출서비스 | guide·menu |  |
| `/service/user` | 학부생 | 없음 | → /service/user/user01 |
| `/service/user/user01` | 학부생 | guide·menu |  |
| `/service/user/user02` | 대학원생 | menu |  |
| `/service/user/user03` | 교직원 | menu |  |
| `/service/user/user04` | 장애학생 | guide·menu |  |
| `/service/user/user05` | 졸업생 / 수료생 | menu |  |
| `/service/user/user06` | 지역주민 / 도서관회원제 | menu |  |
| `/total-search` | 제주대학교 중앙도서관 | menu |  |
