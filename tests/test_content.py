"""공식 사실 기반 콘텐츠(2026-10-13 확인)가 데이터에 들어 있는지 확인한다. 근거: RESEARCH 5장."""
from harness import check, test

SRC = 'https://lib.jejunu.ac.kr/'
COMMON_CAUTION = '목록에 등재되어 있다는 사실만으로'


def rec(d, rid):
    return next(r for k in ('services', 'resources', 'directory') for r in d[k] if r['id'] == rid)


def facts(d, rid, kind=None):
    return [f for f in rec(d, rid).get('facts', []) if kind is None or f.get('kind') == kind]


def texts(d, rid, kind=None):
    return ' '.join(f['text'] for f in facts(d, rid, kind))


@test()
def t_content_hours_print(site):
    site.open()
    d = site.data()
    hours = rec(d, 'hours')
    rule = texts(d, 'hours', 'hours')
    check('3주간 24시간 개방' in rule and '1~4열람실' in rule, f'hours: 24시간 개방 규칙과 적용 공간 {rule}')
    check('교대분관' in hours['caution'], 'hours: 교대분관 미확인 표시 없음')
    check(not hours.get('materials'), 'hours: 지난 공지 링크가 카드에 남아 있음(M3)')
    loc = texts(d, 'print', 'location')
    check('3층 3열람실' in loc and '미디어라운지' in loc, f'print 위치 {loc}')
    check('09:00~20:00' in texts(d, 'print', 'hours'), 'print: 미디어라운지 시간 없음')
    check('06:00~24:00' in texts(d, 'print', 'hours') and '방학' in texts(d, 'print', 'hours'), 'print: 3열람실·방학 시간 없음')
    check('일부열람실' in texts(d, 'hours') and '일부열람실' in texts(d, 'seat'), '열람실 페이지의 "일부열람실" 표현 불일치 표시 없음')
    check(rec(d, 'print')['login'] != '불필요', 'print: 근거 없는 "인증 불필요" 단정')
    exam = next(n for n in d['notices'] if n['id'] == 'exam-2026-2-midterm') if d['notices'] else None
    check(exam is None or {'hours', 'seat'} <= set(exam['taskIds']), '시험기간 공지가 열람실 좌석 카드에 연결되지 않음')


@test()
def t_content_spaces(site):
    site.open()
    d = site.data()
    for rid, note in (('group', '재학생·교직원'), ('maker', '재학생·교직원'), ('carrel', '대학원생·교직원'),
                      ('locker', '재학생'), ('delivery', '장애인')):
        check(note in (rec(d, rid).get('eligibilityNote') or ''), f'{rid}: eligibilityNote')
        check(facts(d, rid), f'{rid}: 대상 근거(facts) 없음')
    group_loc = texts(d, 'group', 'location')
    check('201~210호' in group_loc and '층' not in group_loc, f'group 위치는 호실만(층은 미확인): {group_loc}')
    check(any(f['source'].endswith('#/guide/hoo/floor') for f in facts(d, 'maker', 'location')), 'maker 층의 출처는 층별안내')
    check('미소장' in texts(d, 'delivery') and '확인하지 못했' in rec(d, 'delivery')['caution'], '책나래: 범위 차이·미확인 표시 없음')
    check('3월' in texts(d, 'locker') and len(facts(d, 'locker')) >= 3, '사물함: 신청 시기·경로 없음')
    check('미확인' in (rec(d, 'seat').get('eligibilityNote') or ''), '일반열람실: 대상 미확인 표시 없음(PRD 2장 3번)')
    check('09:00~20:00' in texts(d, 'group', 'hours') and '30분' in texts(d, 'group'), '그룹스터디룸: 운영시간·예약 방법 없음')
    check('자동 취소' in texts(d, 'maker'), '메이커: 예약 방법 없음')
    for rid, page in (('group', 'studyroom'), ('maker', 'makerstudio'), ('carrel', 'carrel'), ('seat', 'readingroom')):
        check(rec(d, rid)['source'] == SRC + '#/service/facility/' + page, f'{rid}: 공식 링크가 개별 시설 페이지가 아님')


@test()
def t_content_remote_and_resources(site):
    site.open()
    d = site.data()
    check('무료' not in rec(d, 'remote')['keywords'], 'remote 키워드에 무료')
    check('별도 가입·등록 필요' in texts(d, 'remote', 'auth'), 'remote: 인증 요약이 "로그인 예외"로 읽힘')
    check('신청 필수' in texts(d, 'editage', 'auth'), 'editage: 학교 웹메일 조건의 근거 없음')
    check('학위취득예정자' in (rec(d, 'thesis-submit').get('eligibilityNote') or '') and facts(d, 'thesis-submit'), 'thesis-submit: 대상 요약·근거 없음')
    check('WSJ' in texts(d, 'culture', 'auth'), 'culture: 고친 WSJ 문구의 근거 없음')
    for rid in ('er-007', 'er-010', 'er-035'):
        check('로그인' in texts(d, rid, 'auth'), f'{rid}: 새 주의 문구의 로그인 근거 없음')
    check('openlink' in texts(d, 'remote'), 'remote: 공식 이용법(openlink) 없음')
    for rid, word in (('er-085', '학내 IP'), ('er-057', '초대링크'), ('er-090', '로그인 후'), ('er-093', '학교 이메일'),
                      ('er-094', '학교 이메일'), ('er-095', '학교 이메일'), ('er-096', '학교 이메일')):
        check(word in texts(d, rid, 'auth'), f'{rid}: 인증 사실({word}) 없음')
    for rid in ('er-093', 'er-094', 'er-095', 'er-096'):
        check(rec(d, rid)['name'].endswith(' Trial'), f'{rid}: 공식 목록 표기(Trial) 아님')
    for rid in ('er-007', 'er-010', 'er-017', 'er-035'):
        check(COMMON_CAUTION not in rec(d, rid)['caution'], f'{rid}: 성격에 맞지 않는 공통 주의 문구')
    for rid in ('editage', 'enago'):
        check('협약가' in texts(d, rid), f'{rid}: 비용 근거 없음')


@test()
def t_content_sources(site):
    site.open()
    d = site.data()
    for r in [r for k in ('services', 'resources') for r in d[k]]:
        for f in r.get('facts', []):
            check(f['source'].startswith(SRC) and f['checkedAt'] >= '2026-10-13', f'{r["id"]}: facts 출처·확인일')
            check(f.get('kind') in (None, 'location', 'auth', 'hours'), f'{r["id"]}: facts.kind {f.get("kind")}')


@test()
def t_book_return_guide(site):
    site.open()
    d = site.data()
    g = rec(d, 'book-return')
    check(g['source'] == SRC + '#/service/circulation/return', f'반납 source {g["source"]}')
    check(g['category'] == 'books', '반납 분류')
    check('제증명' in texts(d, 'book-return'), '연체 시 제증명 발급 제한 없음')
    check(g['cost'] == '연체료 유무는 공식 안내에서 확인하지 못함', f'반납 비용 칸: {g["cost"]}')
    check('다음 운영일' in g['caution'] and '자동반납기' in g['caution'], '반납함 처리 시점(2018 FAQ)·자동반납기 위치 미확인 표시 없음')
    check('book-return' in d['related'].get('loan', []), 'loan → book-return 관련 안내 없음')
