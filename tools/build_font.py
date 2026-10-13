"""본문 글꼴 만들기(D21): Pretendard 1.3.9 가변 글꼴에서 KS X 1001 한글 2,350자·영문·자모·기호만 남기고
굵기 축을 400~700으로 줄인 woff2 한 개. OFL 1.1의 예약 글꼴 이름(Pretendard) 때문에 수정본 이름은 GuideSans로 바꾼다.
결과: fonts/guide-sans.woff2, fonts/glyphs.txt(글꼴에 든 글자 — 데이터 검사가 글자 누락을 찾을 때 쓴다), fonts/OFL.txt
필요: pip install fonttools brotli (글꼴을 다시 만들 때만. 게이트·테스트에는 필요 없다)
사용: python tools/build_font.py [--src 내려받은 PretendardVariable.woff2]"""
import argparse
import hashlib
import pathlib
import re
import urllib.request

from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC_URL = 'https://cdn.jsdelivr.net/npm/pretendard@1.3.9/dist/web/variable/woff2/PretendardVariable.woff2'
SRC_SHA256 = '9599f12fd42fc0bce1cd50b47a0c022e108d7aa64dd0d1bb0ed44f3282d900b4'
LICENSE_URL = 'https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/LICENSE'
FAMILY = 'GuideSans'
# 화면 문구·공식 인용에 쓰는 기호(새 기호가 데이터에 들어오면 데이터 검사가 알려 준다)
PUNCT = '·×–—‘’“”…※→←↑↓↗↘•∙①②③④⑤〈〉「」『』《》（）＊％～○●□■◇◆△▲▷▶☎♡'


def fetch(url, path):
    with urllib.request.urlopen(url, timeout=60) as r:
        path.write_bytes(r.read())


def subset_text():
    ksx = ''.join(chr(c) for c in range(0xAC00, 0xD7A4) if len(chr(c).encode('euc_kr')) == 2)
    assert len(ksx) == 2350, len(ksx)
    ascii_ = ''.join(chr(c) for c in range(0x20, 0x7F))
    jamo = ''.join(chr(c) for c in range(0x3131, 0x3164))
    return ksx + ascii_ + jamo + PUNCT


def rename(font):
    """예약 글꼴 이름을 쓰지 않는다. 저작권(0)·라이선스(13·14) 기록은 그대로 둔다."""
    name = font['name']
    for rec in list(name.names):
        if rec.nameID in (0, 13, 14):
            continue
        text = rec.toUnicode()
        if 'Pretendard' in text:
            name.setName(re.sub(r'Pretendard\s*', FAMILY + ' ', text).replace(FAMILY + ' Variable', FAMILY).strip(),
                         rec.nameID, rec.platformID, rec.platEncID, rec.langID)
    name.setName(f'{FAMILY}: KS X 1001 Hangul subset, wght 400-700', 3, 3, 1, 0x409)
    name.setName('Modified version of Pretendard 1.3.9 by Kil Hyung-jin (SIL OFL 1.1): '
                 'glyph subset and weight range 400-700 for the 도서관의 쓸모 site', 10, 3, 1, 0x409)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--src', help='내려받아 둔 PretendardVariable.woff2(없으면 고정 주소에서 받는다)')
    a = ap.parse_args()
    tmp = ROOT / '.tmp'
    tmp.mkdir(exist_ok=True)
    src = pathlib.Path(a.src) if a.src else tmp / 'PretendardVariable-1.3.9.woff2'
    if not src.exists():
        fetch(SRC_URL, src)
    digest = hashlib.sha256(src.read_bytes()).hexdigest()
    if digest != SRC_SHA256:
        raise SystemExit(f'원본 해시가 다릅니다: {digest} (기대 {SRC_SHA256})')

    opts = subset.Options()
    opts.flavor = 'woff2'
    opts.hinting = False
    opts.desubroutinize = True
    opts.name_IDs = ['*']
    opts.name_languages = ['*']
    font = TTFont(src)
    sub = subset.Subsetter(opts)
    sub.populate(text=subset_text())
    sub.subset(font)
    font = instancer.instantiateVariableFont(font, {'wght': (400, 700)})
    rename(font)
    out = ROOT / 'fonts'
    out.mkdir(exist_ok=True)
    font.flavor = 'woff2'
    font.save(out / 'guide-sans.woff2')
    chars = sorted(chr(c) for c in font.getBestCmap() if c >= 0x20)
    (out / 'glyphs.txt').write_text(''.join(chars) + '\n', encoding='utf-8', newline='\n')
    lic = out / 'OFL.txt'
    if not lic.exists():
        fetch(LICENSE_URL, lic)
    size = (out / 'guide-sans.woff2').stat().st_size
    print(f'fonts/guide-sans.woff2 {size / 1024:.0f}KB, 글자 {len(chars)}개, 원본 sha256 {digest[:12]}…')


if __name__ == '__main__':
    main()
