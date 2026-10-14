"""본문 글꼴 만들기(D21): 원본 글꼴에서 KS X 1001 한글 2,350자·영문·자모·기호만 남긴 woff2 한 개.
수정본이라 이름은 GuideSans로 바꾼다(OFL — 예약 글꼴 이름을 쓰지 않는다). 지금 글꼴은 고운돋움(2026-10-14 사용자 선택).
결과: fonts/guide-sans.woff2, fonts/glyphs.txt(글꼴에 든 글자 — 데이터 검사가 글자 누락을 찾을 때 쓴다), fonts/OFL.txt
필요: pip install fonttools brotli (글꼴을 다시 만들 때만. 게이트·테스트에는 필요 없다)
사용: python tools/build_font.py [--font gowun-dodum|pretendard] [--src 내려받아 둔 원본]"""
import argparse
import hashlib
import pathlib
import re
import urllib.request

from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

ROOT = pathlib.Path(__file__).resolve().parents[1]
FAMILY = 'GuideSans'
GF = 'https://cdn.jsdelivr.net/gh/google/fonts@16a2143d6f6d3a722f4c1bd96a76a637b952c412/ofl/gowundodum/'
SOURCES = {
    'gowun-dodum': {  # 고운돋움 2.000(The Gowun Dodum Project Authors, SIL OFL 1.1), 굵기 1종
        'url': GF + 'GowunDodum-Regular.ttf',
        'sha256': 'a6e457933227483a11758fd0947bc74422a106d46f0bf057fdaa5af94a30067d',
        'license': GF + 'OFL.txt',
        'name': 'Gowun Dodum', 'credit': 'Gowun Dodum 2.000 by The Gowun Dodum Project Authors', 'wght': None,
    },
    'pretendard': {  # 2026-10-13~14 배포본(가변 400~700)
        'url': 'https://cdn.jsdelivr.net/npm/pretendard@1.3.9/dist/web/variable/woff2/PretendardVariable.woff2',
        'sha256': '9599f12fd42fc0bce1cd50b47a0c022e108d7aa64dd0d1bb0ed44f3282d900b4',
        'license': 'https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/LICENSE',
        'name': 'Pretendard', 'credit': 'Pretendard 1.3.9 by Kil Hyung-jin', 'wght': (400, 700),
    },
}
# 화면 문구·공식 인용에 쓰는 기호(새 기호가 데이터에 들어오면 데이터 검사가 알려 준다)
PUNCT = '·×–—‘’“”…※→←↑↓↗↘•∙①②③④⑤〈〉「」『』《》（）＊％～○●□■◇◆△▲▷▶☎♡▣'


def fetch(url, path):
    with urllib.request.urlopen(url, timeout=120) as r:
        path.write_bytes(r.read())


def subset_text():
    ksx = ''.join(chr(c) for c in range(0xAC00, 0xD7A4) if len(chr(c).encode('euc_kr')) == 2)
    assert len(ksx) == 2350, len(ksx)
    ascii_ = ''.join(chr(c) for c in range(0x20, 0x7F))
    jamo = ''.join(chr(c) for c in range(0x3131, 0x3164))
    return ksx + ascii_ + jamo + PUNCT


def rename(font, src):
    """원래 이름을 쓰지 않는다. 저작권(0)·라이선스(13·14) 기록은 그대로 둔다."""
    name = font['name']
    for rec in list(name.names):
        if rec.nameID in (0, 13, 14):
            continue
        text = rec.toUnicode()
        for old in (src['name'], src['name'].replace(' ', '')):
            if old in text:
                text = re.sub(re.escape(old) + r'\s*', FAMILY + ' ', text).replace(FAMILY + ' Variable', FAMILY).strip()
        if rec.nameID in (6, 25):  # PostScript 이름에는 공백을 쓸 수 없다
            text = text.replace(' ', '')
        name.setName(text, rec.nameID, rec.platformID, rec.platEncID, rec.langID)
    name.setName(f'{FAMILY}: KS X 1001 Hangul subset', 3, 3, 1, 0x409)
    name.setName(f'Modified version of {src["credit"]} (SIL OFL 1.1): glyph subset for the 도서관의 쓸모 site', 10, 3, 1, 0x409)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--font', choices=SOURCES, default='gowun-dodum')
    ap.add_argument('--src', help='내려받아 둔 원본(없으면 고정 주소에서 받는다)')
    a = ap.parse_args()
    src = SOURCES[a.font]
    tmp = ROOT / '.tmp'
    tmp.mkdir(exist_ok=True)
    path = pathlib.Path(a.src) if a.src else tmp / src['url'].rsplit('/', 1)[-1]
    if not path.exists():
        fetch(src['url'], path)
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != src['sha256']:
        raise SystemExit(f'원본 해시가 다릅니다: {digest} (기대 {src["sha256"]})')

    opts = subset.Options()
    opts.flavor = 'woff2'
    opts.hinting = False
    opts.desubroutinize = True
    opts.name_IDs = ['*']
    opts.name_languages = ['*']
    font = TTFont(path)
    sub = subset.Subsetter(opts)
    sub.populate(text=subset_text())
    sub.subset(font)
    if src['wght']:
        font = instancer.instantiateVariableFont(font, {'wght': src['wght']})
    rename(font, src)
    out = ROOT / 'fonts'
    out.mkdir(exist_ok=True)
    font.flavor = 'woff2'
    font.save(out / 'guide-sans.woff2')
    chars = sorted(chr(c) for c in font.getBestCmap() if c >= 0x20)
    (out / 'glyphs.txt').write_text(''.join(chars) + '\n', encoding='utf-8', newline='\n')
    fetch(src['license'], out / 'OFL.txt')  # 지금 글꼴의 라이선스로 바꾼다
    size = (out / 'guide-sans.woff2').stat().st_size
    print(f'fonts/guide-sans.woff2 {size / 1024:.0f}KB ({a.font}), 글자 {len(chars)}개, 원본 sha256 {digest[:12]}…')


if __name__ == '__main__':
    main()
