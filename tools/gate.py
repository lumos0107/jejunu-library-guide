"""push 전 검사(PRD 2장 9번, K17, D16). 사용: python tools/gate.py"""
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
PY = sys.executable
STEPS = [
    ('데이터 생성', [PY, 'tools/build_data.py']),
    ('생성물이 커밋된 상태와 같은지', ['git', 'diff', '--exit-code', '--', 'data.js']),
    ('데이터 검사', [PY, 'tests/check_data.py', '--stage', '1']),
    ('Playwright', [PY, 'tests/smoke.py', '--stage', '1', '--browsers', 'chromium,webkit', '--modes', 'file,http']),
]


def clean_tree():
    out = subprocess.run(['git', 'status', '--porcelain'], cwd=ROOT, capture_output=True, check=True).stdout.decode('utf-8')
    return out.strip() == ''


def private_ok():
    # 경로를 직접 지정해 묻는다. 출력 문자열 검색은 한글 경로가 8진수로 바뀌면 놓친다(S17)
    tracked = subprocess.run(['git', 'ls-files', '-z', '--', '_비공개'], cwd=ROOT, capture_output=True, check=True).stdout
    ignored = subprocess.run(['git', 'check-ignore', '-q', '_비공개/x'], cwd=ROOT).returncode == 0
    return tracked == b'' and ignored


def main():
    print('== 작업 트리 확인', flush=True)
    if not clean_tree():
        print('게이트 실패: 커밋하지 않은 변경이 있습니다. 커밋한 뒤 다시 실행하세요(테스트한 파일 = push할 커밋, D16).')
        sys.exit(1)
    for name, cmd in STEPS:
        print(f'== {name}', flush=True)
        if subprocess.run(cmd, cwd=ROOT).returncode != 0:
            print(f'게이트 실패: {name}. push하지 마세요.')
            sys.exit(1)
    print('== .nojekyll 확인')
    if not subprocess.run(['git', 'ls-files', '--', '.nojekyll'], cwd=ROOT, capture_output=True, check=True).stdout.strip():
        print('게이트 실패: .nojekyll이 없습니다. 없으면 GitHub Pages가 docs/*.md를 noindex 없는 HTML로 만듭니다.')
        sys.exit(1)
    print('== _비공개/ 제외 확인')
    if not private_ok():
        print('게이트 실패: _비공개/가 추적되거나 제외되지 않았습니다.')
        sys.exit(1)
    print('게이트 통과: push해도 됩니다.')


if __name__ == '__main__':
    main()
