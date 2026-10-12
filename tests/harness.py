"""외부 패키지 없는 테스트 등록·판정 도구."""
REGISTRY = []


class Fail(AssertionError):
    pass


def test(stage=1, viewport='desktop', motion='reduce', clock=True):
    # clock=False: 시계를 고정하지 않는다. Playwright의 가짜 시계는 performance.mark도 아무 일 안 하게 바꾼다
    def deco(fn):
        REGISTRY.append({'fn': fn, 'stage': stage, 'viewport': viewport, 'motion': motion, 'clock': clock,
                         'name': f'{fn.__module__}::{fn.__name__}'})
        return fn
    return deco


def check(cond, msg):
    if not cond:
        raise Fail(msg)
