"""외부 패키지 없는 테스트 등록·판정 도구."""
REGISTRY = []


class Fail(AssertionError):
    pass


def test(stage=1, viewport='desktop', motion='reduce'):
    def deco(fn):
        REGISTRY.append({'fn': fn, 'stage': stage, 'viewport': viewport, 'motion': motion,
                         'name': f'{fn.__module__}::{fn.__name__}'})
        return fn
    return deco


def check(cond, msg):
    if not cond:
        raise Fail(msg)
