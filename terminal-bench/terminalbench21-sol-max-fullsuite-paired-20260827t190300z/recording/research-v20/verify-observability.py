"""Independent numeric-only replay diagnostic check, including absence semantics."""
import hashlib
import json
import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

folder = Path(sys.argv[1])
run = folder.parents[2]
data = json.loads((folder/'observability.json').read_bytes())
source = json.loads((run/'recording/research-v19/replay-final/replay-data.json').read_bytes())
cells = {c['cell']: c for p in source['pairs'] for c in (p['geode'],p['native'])}
assert data['score_authority'] is False and len(data['cells']) == len(cells) == 890
assert len({c['cell'] for c in data['cells']}) == 890
counts, sources = Counter(), json.loads((folder/'source-hashes.private.json').read_bytes())
public_sources = json.loads((folder/'source-hashes.json').read_bytes())
assert public_sources['path_hashes'] == {p:h for p,h in sources.items() if '/agent/sessions/' not in p}
assert public_sources['withheld_native_session_sha256'] == [h for p,h in sources.items() if '/agent/sessions/' in p]
for name, expected in sources.items():
    assert hashlib.sha256((run/name).read_bytes()).hexdigest() == expected
for cell in data['cells']:
    original = cells[cell['cell']]
    for key in ('cell','arm','task_name','repetition','attempt_id'):
        assert cell[key] == original[key]
    usage = cell['usage']
    events = usage['events']
    if events:
        assert usage['status'] == 'verified-call-usage'
        assert usage['aggregate_matches_result'] is True
        assert [e['index'] for e in events] == list(range(1,len(events)+1))
        for key in ('input_tokens','output_tokens'):
            assert sum(e[key] for e in events) == usage[key]
        missing = sum(e['cached_input_tokens'] is None for e in events)
        assert missing == usage['cache_missing_events']
        if missing:
            assert usage['cached_input_tokens'] is None
        else:
            assert usage['cached_input_tokens'] == sum(e['cached_input_tokens'] for e in events)
        counts[cell['arm']+'_usage_trials'] += 1
        counts[cell['arm']+'_usage_events'] += len(events)
    else:
        assert usage['aggregate_matches_result'] is None
        assert usage['cached_input_tokens'] is None
    assert usage['tool_step_mapping'] == 'not-established'
    for phase in cell['phases'].values():
        if phase['status']=='observed':
            start = datetime.fromisoformat(phase['started_at'].replace('Z','+00:00'))
            end = datetime.fromisoformat(phase['finished_at'].replace('Z','+00:00'))
            assert start.tzinfo and end.tzinfo
            assert phase['seconds'] == (end-start).total_seconds() >= 0
        else:
            assert phase['seconds'] is None
    if not original['attempt_id']:
        assert usage['status']=='not-run' and cell['commands']['status']=='not-run'
        assert all(p['status']=='not-run' for p in cell['phases'].values())
        counts['excluded'] += 1
    command = cell['commands']
    if command['status']=='observed':
        assert 0 <= command['nonzero'] <= command['completed']
    else:
        assert command['completed'] is None and command['nonzero'] is None
    assert cell['cost']['billed_usd'] is None
    assert cell['cost']['pricing_revision'] is None
assert counts['excluded']==20
for key in ('geode_usage_trials','native_usage_trials','geode_usage_events','native_usage_events'):
    assert counts[key] == data['coverage'][key]
for file in folder.iterdir():
    if not file.is_file() or file.name.endswith('.private.json'):
        continue
    text = file.read_text()
    assert '/agent/sessions/' not in text, 'Native session identity disclosed'
    for name, pattern in {
        'machine-path': r'/(?:Users|home)/[^\s"<>]+|/var/folders/|[A-Z]:[\\/]|\\\\[A-Za-z]|~/',
        'email': r'[A-Za-z0-9_.+-]+@[A-Za-z0-9-]+\.[A-Za-z]{2,}',
        'credential': r'\b(?:sk-|ghp_|gho_|github_pat_|xoxb-|xoxp-|xapp-)[A-Za-z0-9_-]{16,}',
        'jwt': r'eyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]+',
        'bearer': r'(?i)Bearer\s+[A-Za-z0-9._-]{16,}',
    }.items():
        assert not re.search(pattern,text), (file.name,name)
print(json.dumps(dict(status='passed', source_hashes_verified=len(sources), counts=counts,
    privacy_findings=[], raw_evidence_modified=False)))
