"""데이터 검사기가 잘못된 데이터를 실제로 잡는지 확인한다(음성 테스트, 5차 평가). 브라우저는 쓰지 않는다."""
import copy
import pathlib
import sys

from harness import check, test

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import check_data  # noqa: E402
import datajs  # noqa: E402

SRC = 'https://lib.jejunu.ac.kr/'


def errors_after(mutate):
    d = copy.deepcopy(datajs.load(ROOT / 'data.js'))
    mutate(d)
    return check_data.run_checks(d, 1, '2026-10-15')


def bad_fact(d):
    d['services'][0].setdefault('facts', []).append({'text': 't', 'source': SRC, 'checkedAt': '2026-99-99'})


def note_with_location_only(d):
    d['services'][1].update({'eligibilityNote': 'x', 'facts': [{'kind': 'location', 'text': 't', 'source': SRC, 'checkedAt': '2026-10-13'}]})


CASES = {
    'steps가 문자열': lambda d: d['services'][0].__setitem__('steps', '문장'),
    '달력에 없는 날짜': bad_fact,
    '예약된 id': lambda d: d['resources'][0].__setitem__('id', 'constructor'),
    '예약된 키': lambda d: d['related'].__setitem__('__proto__', ['loan']),
    'recordKind 불일치': lambda d: d['resources'][0].__setitem__('recordKind', 'guide'),
    '위치만 있는 대상 요약': note_with_location_only,
    '주장 필드의 무료': lambda d: d['services'][0].__setitem__('description', '무료로 쓸 수 있어요'),
    'http 링크': lambda d: d['services'][0].__setitem__('source', 'http://lib.jejunu.ac.kr/'),
    '책 상황 키 누락': lambda d: d['bookCases'].pop('loan'),
    '이름에 없는 검색어': lambda d: d['resources'][0].__setitem__('findTerm', '이름에없는말'),
    '자료 카드의 버튼 이름': lambda d: d['resources'][0].__setitem__('sourceLabel', '여기 열기'),
    '가는 곳을 말하지 않는 버튼 이름': lambda d: d['services'][0].__setitem__('sourceLabel', '바로가기'),
    '글꼴에 없는 글자': lambda d: d['services'][0].__setitem__('description', '똠양꿍 설명'),
    '상황 카드와 화면이 다름': lambda d: d['categories'][0].__setitem__('question', '바뀐 질문'),
}

BAD_CSS = {
    ':root 밖의 색': 'a { color: #fff }',
    '글자 크기 직접 값': 'a { font-size: 13px }',
    '굵기 650': 'a { font-weight: 650 }',
    '긴 전환': 'a { transition: color .5s }',
    '그라데이션': 'a { background: linear-gradient(red, blue) }',
    '부드러운 스크롤': 'html { scroll-behavior: smooth }',
}


@test()
def t_check_data_catches_bad_data(site):
    check(errors_after(lambda d: None) == [], '현재 데이터가 검사에 걸림')
    missed = [name for name, mutate in CASES.items() if not errors_after(mutate)]
    check(not missed, f'검사기가 놓친 잘못된 데이터: {missed}')
    missed_css = [name for name, css in BAD_CSS.items() if not check_data.css_errors(':root { --x:#fff; }\n' + css)]
    check(not missed_css, f'CSS 규칙 검사가 놓친 것: {missed_css}')
    check(check_data.css_errors((ROOT / 'styles.css').read_text(encoding='utf-8')) == [], 'styles.css가 디자인 규칙 위반')
