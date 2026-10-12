"""v2 실행 확인에 썼던 Playwright 점검 35개 항목의 원본(2026-10-12, Chromium file://, 데스크톱 30 + 모바일 5).
P1-01 회귀 테스트(tests/test_regression.py)의 출처. 대응표는 docs/v3/RESEARCH.md 6장.
사용: python qa_playwright_35.py <사이트 폴더> <스크린샷 폴더>"""
import sys, pathlib
from playwright.sync_api import sync_playwright

SITE = pathlib.Path(sys.argv[1]).resolve() / "index.html"
OUT = pathlib.Path(sys.argv[2])
OUT.mkdir(parents=True, exist_ok=True)
URL = SITE.as_uri()
results = []

def check(name, cond, detail=""):
    results.append((name, bool(cond), detail))

def count_text(p):
    return p.locator("#result-count").inner_text()

def cards(p):
    return p.locator("#service-grid .service-card").count()

def search(p, q):
    p.fill("#search-input", q)
    p.press("#search-input", "Enter")
    p.wait_for_timeout(150)

with sync_playwright() as pw:
    b = pw.chromium.launch()
    p = b.new_page(viewport={"width": 1440, "height": 900})
    errors = []
    p.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))
    p.on("console", lambda m: errors.append(f"console.{m.type}: {m.text}") if m.type == "error" else None)
    p.goto(URL)
    p.wait_for_selector("#service-grid .service-card")
    p.screenshot(path=str(OUT / "01_desktop_top.png"))

    check("초기 결과 문구", "234개 결과" in count_text(p), count_text(p))
    check("초기 카드 12개", cards(p) == 12, str(cards(p)))
    check("상황 카드 6개", p.locator("#category-grid .category-card").count() == 6)
    check("확인일 표시", p.locator("#checked-at").inner_text().strip() != "", p.locator("#checked-at").inner_text())

    p.click("#load-more"); p.wait_for_timeout(100)
    check("더 보기 → 24개", cards(p) == 24, str(cards(p)))

    for q in ["무선인터넷", "SDI", "외국어 교정", "Naxos", "CAS BioFinder", "크레마클럽"]:
        search(p, q)
        check(f"검색 '{q}'", cards(p) > 0, count_text(p))

    search(p, "zzzz없는검색어qq")
    check("없는 검색어 → 빈 결과", p.locator("#empty").is_visible() and cards(p) == 0, count_text(p))
    p.click("#empty-reset"); p.wait_for_timeout(100)
    check("초기화 후 234개 복귀", "234개 결과" in count_text(p), count_text(p))

    # 전자정보원 범위 + 필터
    p.click("#scope-tabs [data-scope=resource]"); p.wait_for_timeout(100)
    check("전자정보원 98개", "98개 결과" in count_text(p), count_text(p))
    check("전자정보원 필터 표시", p.locator("#resource-filters").is_visible())
    p.select_option("#resource-access", "공개자료 안내"); p.wait_for_timeout(100)
    check("공개자료 필터 6개", "6개 결과" in count_text(p), count_text(p))
    p.select_option("#resource-access", "시범서비스"); p.wait_for_timeout(100)
    check("시범서비스 필터 4개", "4개 결과" in count_text(p), count_text(p))
    p.select_option("#resource-access", "all")
    subj = [o for o in p.locator("#resource-subject option").all_inner_texts() if "통계" in o]
    if subj:
        p.select_option("#resource-subject", label=subj[0]); p.wait_for_timeout(100)
        check(f"분야 '{subj[0]}' 5개", "5개 결과" in count_text(p), count_text(p))
    else:
        check("통계 분야 옵션 존재", False)
    p.select_option("#resource-subject", "all")

    search(p, "Statista")
    p.locator("#service-grid .service-card button[data-open]").first.click()
    p.wait_for_selector("#detail-dialog[open]")
    detail = p.locator("#detail-content").inner_text()
    check("Statista 상세창 열림", "Statista" in p.locator("#detail-dialog").inner_text())
    check("Statista 매뉴얼 링크", p.locator("#detail-content a[href^='http']").count() > 0,
          f"링크 {p.locator('#detail-content a[href^=http]').count()}개")
    p.screenshot(path=str(OUT / "02_statista_detail.png"))
    p.keyboard.press("Escape"); p.wait_for_timeout(150)
    check("Escape로 상세창 닫힘", p.locator("#detail-dialog[open]").count() == 0)

    # 공식 메뉴
    p.click("#reset"); p.wait_for_timeout(100)
    p.click("#scope-tabs [data-scope=menu]"); p.wait_for_timeout(100)
    check("공식 메뉴 89개", "89개 결과" in count_text(p), count_text(p))
    ml = [o for o in p.locator("#menu-group option").all_inner_texts() if "My Library" in o]
    if ml:
        p.select_option("#menu-group", label=ml[0]); p.wait_for_timeout(100)
        check("My Library 17개", "17개 결과" in count_text(p), count_text(p))

    # 이용 가이드 + 학부생
    p.click("#reset"); p.wait_for_timeout(100)
    p.click("#scope-tabs [data-scope=guide]"); p.wait_for_timeout(100)
    check("이용 가이드 47개", "47개 결과" in count_text(p), count_text(p))
    p.select_option("#audience", "undergrad"); p.wait_for_timeout(100)
    check("학부생 필터 45개", "45개 결과" in count_text(p), count_text(p))
    study = p.locator("#category-tabs button[data-category]").all_inner_texts()
    tgt = [t for t in study if "공부" in t or "공간" in t]
    if tgt:
        p.locator("#category-tabs button[data-category]", has_text=tgt[0]).click(); p.wait_for_timeout(100)
        check(f"'{tgt[0]}' + 학부생 4개", "4개 결과" in count_text(p), count_text(p))

    # 책 상황
    p.click("#reset")
    p.click("[data-book='not-owned']"); p.wait_for_timeout(100)
    br = p.locator("#book-result").inner_text()
    check("학교에 없는 책 → 희망도서·상호대차", p.locator("#book-result").is_visible() and "희망도서" in br, br.replace("\n", " / "))
    p.locator("#book-result").scroll_into_view_if_needed()
    p.screenshot(path=str(OUT / "03_book_result.png"))

    # 히어로 버튼 → 상세
    p.evaluate("window.scrollTo(0,0)")
    p.click(".hero-aside [data-open=maker]")
    p.wait_for_selector("#detail-dialog[open]")
    check("히어로 '메이커 스튜디오' 상세", "메이커" in p.locator("#detail-dialog").inner_text())
    p.click("#close-dialog"); p.wait_for_timeout(100)
    check("닫기 버튼으로 닫힘", p.locator("#detail-dialog[open]").count() == 0)

    check("데스크톱 콘솔/페이지 오류 없음", not errors, "; ".join(errors))

    # 모바일
    m = b.new_page(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True)
    merr = []
    m.on("pageerror", lambda e: merr.append(str(e)))
    m.goto(URL)
    m.wait_for_selector("#service-grid .service-card")
    m.screenshot(path=str(OUT / "04_mobile_top.png"))
    sw = m.evaluate("document.documentElement.scrollWidth")
    check("모바일 가로 넘침 없음", sw <= 390, f"scrollWidth={sw}")
    m.click("#scope-tabs [data-scope=resource]")
    search(m, "JSTOR")
    check("모바일 JSTOR 1개", "1개 결과" in count_text(m), count_text(m))
    m.locator("#service-grid .service-card button[data-open]").first.click()
    m.wait_for_selector("#detail-dialog[open]")
    box = m.locator("#detail-dialog").bounding_box()
    check("모바일 상세창 뷰포트 안", box["x"] >= 0 and box["x"] + box["width"] <= 390, f"x={box['x']:.0f} w={box['width']:.0f}")
    m.screenshot(path=str(OUT / "05_mobile_detail.png"))
    m.keyboard.press("Escape"); m.wait_for_timeout(150)
    check("모바일 Escape 닫힘", m.locator("#detail-dialog[open]").count() == 0)
    check("모바일 페이지 오류 없음", not merr, "; ".join(merr))
    b.close()

ok = sum(r[1] for r in results)
for name, passed, d in results:
    print(("PASS" if passed else "FAIL"), name, ("— " + d) if d else "")
print(f"\n{ok}/{len(results)} 통과")
