"""배포본이 HEAD와 같은지 확인한 뒤 배포 주소에서 테스트한다. 사용: python tools/deploy_check.py https://<배포 주소>/"""
import hashlib
import pathlib
import subprocess
import sys
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
FILES = ['index.html', 'styles.css', 'data.js', 'js/config.js', 'js/lib.js', 'js/app.js', 'favicon.svg']


def main():
    base = sys.argv[1].rstrip('/') + '/'
    stale = []
    for f in FILES:
        local = subprocess.run(['git', 'show', f'HEAD:{f}'], cwd=ROOT, capture_output=True, check=True).stdout
        with urllib.request.urlopen(base + f + '?nocache=1') as r:
            remote = r.read()
        if hashlib.sha256(local).digest() != hashlib.sha256(remote).digest():
            stale.append(f)
    if stale:
        print('배포본이 아직 HEAD와 다릅니다:', stale, '— 잠시 뒤 다시 실행하세요.')
        sys.exit(1)
    print('배포본 = HEAD 확인')
    sys.exit(subprocess.run([sys.executable, 'tests/smoke.py', '--stage', '1', '--browsers', 'chromium,webkit', '--base', base], cwd=ROOT).returncode)


if __name__ == '__main__':
    main()
