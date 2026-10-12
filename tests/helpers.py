"""화면을 '행동' 단위로 다루는 도우미. 테스트는 선택자를 직접 쓰지 않고 이 클래스를 쓴다."""
import json
import re

VIEWPORTS = {'desktop': {'width': 1440, 'height': 900}, 'mobile': {'width': 390, 'height': 844}}


class Site:
    def __init__(self, page, base, errors):
        self.page, self.base, self.errors = page, base, errors

    def open(self, hash_=''):
        self.page.goto(self.base + 'index.html' + hash_)
        self.page.wait_for_selector('#service-grid .service-card')

    def search(self, q):
        self.page.fill('#search-input', q)
        self.page.press('#search-input', 'Enter')
        self.page.wait_for_timeout(120)

    def query_value(self):
        return self.page.input_value('#search-input')

    def count(self):
        m = re.search(r'(\d+)개 결과', self.page.inner_text('#result-count'))
        return int(m.group(1)) if m else None

    def result_ids(self):
        return self.page.eval_on_selector_all('#service-grid [data-open]', 'els => els.map(e => e.dataset.open)')

    def card_count(self):
        return self.page.locator('#service-grid .service-card').count()

    def scope(self, s):
        self.page.click(f'#scope-tabs [data-scope="{s}"]')
        self.page.wait_for_timeout(80)

    def category_tab(self, cid):
        self.page.click(f'#category-tabs [data-category="{cid}"]')
        self.page.wait_for_timeout(80)

    def category_card(self, cid):
        self.page.click(f'#category-grid [data-category="{cid}"]')
        self.page.wait_for_timeout(150)

    def select(self, sel_id, value):
        self.page.select_option(f'#{sel_id}', value)
        self.page.wait_for_timeout(80)

    def load_more(self):
        self.page.click('#load-more')
        self.page.wait_for_timeout(80)

    def open_detail(self, rid):
        self.page.locator(f'#service-grid [data-open="{rid}"]').first.click()
        self.page.wait_for_selector('#detail-dialog[open]')

    def open_any(self, rid):
        """목록에 없어도 상세를 연다(앱의 클릭 위임을 그대로 사용)."""
        self.page.evaluate("""rid => { const b = document.createElement('button');
            b.dataset.open = rid; b.hidden = true; document.body.append(b); b.click(); b.remove(); }""", rid)
        self.page.wait_for_selector('#detail-dialog[open]')

    def detail_text(self):
        return self.page.inner_text('#detail-content')

    def official_href(self):
        return self.page.get_attribute('#detail-content a.primary', 'href')

    def close_detail(self):
        self.page.keyboard.press('Escape')
        self.page.wait_for_timeout(120)

    def close_with_button(self):
        self.page.click('#close-dialog')
        self.page.wait_for_timeout(120)

    def dialog_open(self):
        return self.page.locator('#detail-dialog[open]').count() == 1

    def book_case(self, key):
        self.page.click(f'[data-book="{key}"]')
        self.page.wait_for_timeout(80)

    def open_from_hero(self, rid):
        self.page.click(f'.hero-aside [data-open="{rid}"]')
        self.page.wait_for_selector('#detail-dialog[open]')

    def material_links(self):
        return self.page.eval_on_selector_all('#detail-content .material-list a', 'els => els.map(e => e.getAttribute("href"))')

    def category_card_count(self):
        return self.page.locator('#category-grid .category-card').count()

    def resource_filters_visible(self):
        return self.page.locator('#resource-filters').is_visible()

    def console_errors(self):
        return [e for e in self.errors if 'favicon' not in e]

    def data(self):
        return self.page.evaluate('window.LIBRARY_GUIDE')


TEST_NOTICE = {'id': 'fixture-exam', 'text': '테스트 공지: 열람실 24시간 개방',
               'link': 'https://lib.jejunu.ac.kr/#/bbs/notice/6789', 'source': 'https://lib.jejunu.ac.kr/#/bbs/notice/6789',
               'checkedAt': '2026-10-13', 'startsOn': '2026-10-07', 'endsOn': '2026-10-26', 'taskIds': ['hours']}


def notices_fixture(items):
    """window.LIBRARY_GUIDE 대입을 가로채 notices만 바꾸는 초기화 스크립트(file://에서도 동작)."""
    return ("(() => { let v; Object.defineProperty(window, 'LIBRARY_GUIDE', { configurable: true, get() { return v; },"
            " set(x) { x.notices = " + json.dumps(items, ensure_ascii=False) + "; v = x; } }); })();")
