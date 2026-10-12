"""v2 data.js에서 ID 기준 목록(tests/fixtures/v2-ids.json)을 만든다. 1회만 실행."""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import datajs  # noqa: E402

data = datajs.load(ROOT / 'data.js')
ids = {k: [r['id'] for r in data[k]] for k in ('services', 'resources', 'directory')}
out = ROOT / 'tests' / 'fixtures' / 'v2-ids.json'
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(ids, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
print(out, {k: len(v) for k, v in ids.items()})
