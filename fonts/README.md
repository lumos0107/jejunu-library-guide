# 본문 글꼴 GuideSans

이 사이트의 본문 글꼴은 [Pretendard](https://github.com/orioncactus/pretendard) 1.3.9(길형진, SIL Open Font License 1.1)를 줄인 수정본입니다.

| 항목 | 값 |
|---|---|
| 원본 | Pretendard 1.3.9 가변 글꼴 `PretendardVariable.woff2` |
| 원본 주소 | https://cdn.jsdelivr.net/npm/pretendard@1.3.9/dist/web/variable/woff2/PretendardVariable.woff2 |
| 원본 sha256 | `9599f12fd42fc0bce1cd50b47a0c022e108d7aa64dd0d1bb0ed44f3282d900b4` |
| 남긴 글자 | KS X 1001 한글 2,350자, 영문·숫자(ASCII), 한글 자모, 화면에 쓰는 기호(`tools/build_font.py`의 `PUNCT`) — 모두 `glyphs.txt` |
| 굵기 | 가변 축 400~700(본문 400, 라벨·버튼 600, 제목 700) |
| 이름 | OFL의 예약 글꼴 이름(Pretendard) 때문에 수정본 이름을 `GuideSans`로 바꿨습니다 |
| 라이선스 | `OFL.txt`(원본 저장소 v1.3.9의 LICENSE 그대로) |

## 다시 만들기

```
pip install fonttools brotli
python tools/build_font.py            # 원본을 받아 해시를 확인한 뒤 fonts/guide-sans.woff2, glyphs.txt를 만든다
```

데이터나 화면 문구에 `glyphs.txt`에 없는 글자가 들어오면 데이터 검사(`tests/check_data.py`)가 알려 줍니다. 그 글자를 `PUNCT`에 넣고 다시 만들거나 다른 글자로 바꿉니다. 공식 원문을 인용한 `∙`·`▣`는 Pretendard에도 없어 시스템 글꼴로 보이며, 검사에서 예외로 둡니다.
