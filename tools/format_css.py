"""CSS를 규칙·값 변경 없이 한 줄에 선언 하나로 푼다. 사용: python tools/format_css.py styles.css"""
import pathlib
import sys


def format_css(src):
    out, cur, depth, paren, i = [], '', 0, 0, 0
    while i < len(src):
        if src.startswith('/*', i):
            j = src.index('*/', i) + 2
            if cur.strip():
                out.append('  ' * depth + cur.strip())
                cur = ''
            out.append('  ' * depth + src[i:j].strip())
            i = j
            continue
        ch = src[i]
        if ch in '"\'':
            j = i + 1
            while src[j] != ch:
                j += 2 if src[j] == '\\' else 1
            cur += src[i:j + 1]
            i = j + 1
            continue
        if ch == '(':
            paren += 1
        elif ch == ')':
            paren -= 1
        if ch == '{' and not paren:
            out.append('  ' * depth + ' '.join(cur.split()) + ' {')
            cur, depth = '', depth + 1
        elif ch == ';' and not paren:
            if cur.strip():
                out.append('  ' * depth + ' '.join(cur.split()) + ';')
            cur = ''
        elif ch == '}' and not paren:
            if cur.strip():
                out.append('  ' * depth + ' '.join(cur.split()) + ';')
            cur, depth = '', depth - 1
            out.append('  ' * depth + '}')
        else:
            cur += ch
        i += 1
    return '\n'.join(line.rstrip() for line in out) + '\n'


if __name__ == '__main__':
    p = pathlib.Path(sys.argv[1])
    p.write_text(format_css(p.read_text(encoding='utf-8')), encoding='utf-8', newline='\n')
