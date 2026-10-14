# 본문 글꼴 GuideSans

이 사이트의 본문 글꼴은 [고운돋움](https://github.com/yangheeryu/Gowun-Dodum)(Gowun Dodum 2.000, The Gowun Dodum Project Authors, SIL Open Font License 1.1)을 줄인 수정본입니다. 2026-10-14 사용자가 미리보기에서 고른 글꼴입니다(그전에는 Pretendard 1.3.9).

| 항목 | 값 |
|---|---|
| 원본 | Gowun Dodum 2.000 `GowunDodum-Regular.ttf`(Google Fonts 저장소, 커밋 고정) |
| 원본 주소 | https://cdn.jsdelivr.net/gh/google/fonts@16a2143d6f6d3a722f4c1bd96a76a637b952c412/ofl/gowundodum/GowunDodum-Regular.ttf |
| 원본 sha256 | `a6e457933227483a11758fd0947bc74422a106d46f0bf057fdaa5af94a30067d` |
| 남긴 글자 | KS X 1001 한글 2,350자, 영문·숫자(ASCII), 한글 자모, 화면에 쓰는 기호(`tools/build_font.py`의 `PUNCT`) — 모두 `glyphs.txt` |
| 굵기 | 1종(400). 제목·버튼처럼 600·700을 쓰는 글자는 브라우저가 굵게 만든다 |
| 크기 | woff2 약 151KB |
| 이름 | 수정본이라 원래 이름 대신 `GuideSans`로 바꿨습니다 |
| 라이선스 | `OFL.txt`(원본 저장소의 OFL.txt 그대로) |

## 다시 만들기

```
pip install fonttools brotli
python tools/build_font.py                      # 고운돋움(기본값)
python tools/build_font.py --font pretendard    # 이전 글꼴로 되돌릴 때(CSS의 font-weight도 400 700으로)
```

원본을 받아 해시를 확인한 뒤 `fonts/guide-sans.woff2`, `glyphs.txt`, `OFL.txt`를 만듭니다. 데이터나 화면 문구에 `glyphs.txt`에 없는 글자가 들어오면 데이터 검사(`tests/check_data.py`)가 알려 줍니다. 그 글자를 `PUNCT`에 넣고 다시 만들거나 다른 글자로 바꿉니다.
