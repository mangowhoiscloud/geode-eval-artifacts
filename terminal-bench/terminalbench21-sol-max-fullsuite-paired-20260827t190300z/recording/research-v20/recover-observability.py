"""Recover numeric diagnostics; never rewrite native evidence or infer absent values."""
import argparse
import hashlib
import importlib.util
import json
import math
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path


def digest(data):
    return hashlib.sha256(data).hexdigest()


def write(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, ensure_ascii=False, separators=(',', ':'), allow_nan=False)
        stream.write('\n')


def number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def stamp(value):
    d = datetime.fromisoformat(value.replace('Z', '+00:00'))
    assert d.tzinfo is not None, 'Unknown source timezone'
    return d.astimezone(UTC)


def phase(value, not_run=False):
    start, end = (value or {}).get('started_at'), (value or {}).get('finished_at')
    elapsed = (stamp(end) - stamp(start)).total_seconds() if start and end else None
    assert elapsed is None or elapsed >= 0
    return dict(started_at=start, finished_at=end, seconds=elapsed,
                status='not-run' if not_run else 'observed' if elapsed is not None
                else 'not-reached' if not start and not end else 'incomplete')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--usage-dir', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    run, output = args.run.resolve(), args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    producer = Path(__file__).resolve()
    hashes = {str(producer.relative_to(run)): digest(producer.read_bytes())}

    def read(path, expected=None):
        raw = path.read_bytes()
        h = digest(raw)
        if expected:
            assert h == expected, 'Source digest mismatch'
        hashes[str(path.relative_to(run))] = h
        return json.loads(raw)

    replay_path = run/'recording/research-v19/replay-final/replay-data.json'
    replay = read(replay_path, 'fd934ee47e6c26b250378bfcf57ad25146d03579c87f757faf8bc44e7b3eaeed')
    old = read(run/'recording/research-v13/usage-source-hashes.json')
    for rel, expected in old.items():
        assert digest((run/rel).read_bytes()) == expected, 'v13 source changed'
    module_path = run/'recording/research-v13/analyze.py'
    spec = importlib.util.spec_from_file_location('usage_v13', module_path)
    native = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(native)
    hashes[str(module_path.relative_to(run))] = digest(module_path.read_bytes())
    receipts = read(run/'verifier-receipts.json')['receipts']
    results = {r['attempt_id']: (r, read(run/r['raw_result'], r['raw_result_sha256'])) for r in receipts}
    sessions = {}
    for r, result in results.values():
        sid = ((result.get('agent_result') or {}).get('metadata') or {}).get('geode_session_id')
        if r['arm'] == 'geode' and sid:
            assert sid not in sessions
            sessions[sid] = r['attempt_id']
    usage = defaultdict(list)
    private_sources = []
    for month in ('2026-08', '2026-09'):
        source = args.usage_dir/(month+'.jsonl')
        raw = source.read_bytes()
        matched = 0
        for line_number, line in enumerate(raw.splitlines(), 1):
            if not line.strip():
                continue
            row = json.loads(line)
            attempt = sessions.get(row.get('session'))
            if not attempt or row.get('source'):
                continue
            inp, out, cached = row.get('in'), row.get('out'), row.get('cache_r')
            assert all(number(v) and v >= 0 for v in (inp, out))
            assert cached is None or (number(cached) and 0 <= cached <= inp)
            time = datetime.fromtimestamp(row['ts'], UTC)
            r = results[attempt][1]
            assert stamp(r['started_at']) <= time <= stamp(r['finished_at'])
            usage[attempt].append(dict(timestamp_utc=time.isoformat().replace('+00:00', 'Z'),
                input_tokens=inp, output_tokens=out, cached_input_tokens=cached,
                source_record_sha256=digest(line), source_month=month, source_line=line_number))
            matched += 1
        private_sources.append(dict(kind='private-geode-monthly-usage', month=month,
            bytes=len(raw), sha256=digest(raw), matched_records=matched,
            classification='withheld-private', path_disclosed=False))

    cells, counter, stage_counts = [], Counter(), {'geode': Counter(), 'native': Counter()}
    for pair in replay['pairs']:
        for arm in ('geode', 'native'):
            cell = pair[arm]
            row = dict(cell=cell['cell'], arm=arm, task_name=cell['task_name'],
                repetition=cell['repetition'], attempt_id=cell['attempt_id'])
            no_run = not cell['attempt_id']
            receipt, result = results.get(cell['attempt_id'], ({}, {}))
            agent = result.get('agent_result') or {}
            row['phases'] = {name: phase(result.get(name), no_run) for name in
                             ('environment_setup', 'agent_setup', 'agent_execution', 'verifier')}
            for name, value in row['phases'].items():
                if value['status'] == 'observed':
                    stage_counts[arm][name] += 1
            if receipt:
                row['result_ref'] = dict(path=receipt['raw_result'], sha256=receipt['raw_result_sha256'])
            events, source_ref = [], None
            if arm == 'geode':
                events = usage.get(cell['attempt_id'], [])
                if events:
                    assert len({e['source_record_sha256'] for e in events}) == len(events)
                    source_ref = dict(kind='private-geode-monthly-usage',
                        source_inventory='private-source-inventory.json')
            elif receipt:
                paths = list((run/receipt['raw_result']).parent.joinpath('agent/sessions').rglob('*.jsonl'))
                assert len(paths) <= 1, 'Ambiguous native session'
                if paths:
                    p = paths[0]
                    hashes[str(p.relative_to(run))] = digest(p.read_bytes())
                    parsed, repeated = native.native_events(p)
                    counter['native_repeated_snapshots_ignored'] += repeated
                    events = [{k: e[k] for k in ('timestamp_utc','input_tokens','output_tokens','cached_input_tokens')} for e in parsed]
                    source_ref = dict(kind='private-native-session', sha256=hashes[str(p.relative_to(run))])
            if events:
                assert sum(e['input_tokens'] for e in events) == agent['n_input_tokens']
                assert sum(e['output_tokens'] for e in events) == agent['n_output_tokens']
                assert all(stamp(a['timestamp_utc']) <= stamp(b['timestamp_utc']) for a,b in zip(events,events[1:]))
                if arm == 'native':
                    assert sum(e['cached_input_tokens'] for e in events) == agent['n_cache_tokens']
                counter[arm+'_usage_trials'] += 1
                counter[arm+'_usage_events'] += len(events)
            missing = sum(e['cached_input_tokens'] is None for e in events)
            observed = [e['cached_input_tokens'] for e in events if e['cached_input_tokens'] is not None]
            if any(v > 0 for v in observed):
                counter[arm+'_positive_cache_trials'] += 1
            counter[arm+'_cache_missing_events'] += missing
            row['usage'] = dict(status='verified-call-usage' if events else 'not-run' if no_run else 'unavailable',
                input_tokens=agent.get('n_input_tokens'), output_tokens=agent.get('n_output_tokens'),
                cached_input_tokens=sum(observed) if events and not missing else None,
                observed_cached_tokens=sum(observed) if observed else None,
                cache_missing_events=missing, events=[dict(index=i+1, **e) for i,e in enumerate(events)],
                aggregate_matches_result=True if events else None, source_ref=source_ref,
                tool_step_mapping='not-established')
            exits, source_ref = [], None
            if receipt:
                p = (run/receipt['raw_result']).parent/'agent'/('trajectory.json' if arm=='geode' else 'codex.txt')
                if p.exists():
                    hashes[str(p.relative_to(run))] = digest(p.read_bytes())
                    source_ref = dict(path=str(p.relative_to(run)), sha256=hashes[str(p.relative_to(run))])
                    if arm == 'geode':
                        trajectory = json.loads(p.read_bytes())
                        for step in trajectory.get('steps', []):
                            for observation in step.get('observation', {}).get('results', []):
                                content = observation.get('content')
                                try:
                                    value = json.loads(content) if isinstance(content,str) else content
                                except json.JSONDecodeError:
                                    continue
                                if isinstance(value,dict) and type(value.get('return_code')) is int:
                                    exits.append(value['return_code'])
                    else:
                        for line in p.read_text().splitlines():
                            try:
                                value = json.loads(line)
                            except json.JSONDecodeError:
                                continue
                            if not isinstance(value,dict):
                                continue
                            item = value.get('item') or {}
                            if value.get('type')=='item.completed' and item.get('type')=='command_execution' and type(item.get('exit_code')) is int:
                                exits.append(item['exit_code'])
            counter[arm+'_command_exits'] += len(exits)
            counter[arm+'_nonzero_exits'] += sum(e != 0 for e in exits)
            row['commands'] = dict(status='observed' if exits else 'not-run' if no_run else 'unavailable',
                completed=len(exits) if exits else None, nonzero=sum(e != 0 for e in exits) if exits else None,
                source_ref=source_ref, definition='Structured completed shell-command exit status; not tool invocation failure. Trial-level only.')
            cost = agent.get('cost_usd')
            row['cost'] = dict(reported_estimate_usd=cost if number(cost) else None,
                billed_usd=None, pricing_revision=None, status='producer-estimate-not-billing' if number(cost) else 'unavailable')
            cells.append(row)
    assert len(cells)==890 and len({c['cell'] for c in cells})==890
    assert counter['geode_usage_trials']==401 and counter['geode_usage_events']==4709
    assert counter['native_usage_trials']==418 and counter['native_usage_events']==12214
    assert counter['geode_positive_cache_trials']==384 and counter['geode_cache_missing_events']==648
    payload = dict(run_id=run.name, method='source-joined-numeric-observability-v1', score_authority=False,
        producer_sha256=digest(producer.read_bytes()),
        replay_source_sha256=digest(replay_path.read_bytes()), coverage=dict(counter),
        phase_coverage=stage_counts, cells=cells,
        limitations=['Retrospective derived diagnostics; original scores and attempt selection unchanged.',
            'Recorded LLM usage events are not ATIF steps or user turns. No exact usage-to-tool mapping.',
            'Absent cache fields stay null; observed cached-token subtotal is not a complete total.',
            'Process nonzero exit is not tool invocation failure. Cross-arm command populations differ.',
            'CPU utilization, peak RAM, TTFT and actual subscription charges were not recovered.'])
    write(output/'observability.json',payload)
    write(output/'private-source-inventory.json',private_sources)
    write(output/'source-hashes.private.json',hashes)
    write(output/'source-hashes.json',dict(
        path_hashes={p:h for p,h in hashes.items() if '/agent/sessions/' not in p},
        withheld_native_session_sha256=[h for p,h in hashes.items() if '/agent/sessions/' in p]))
    write(output/'recovery-check.json',dict(new_model_calls=0, raw_evidence_modified=False,
        v13_sources_verified=len(old), source_hashes_verified=len(hashes),
        usage_sums_match_result=True, cache_missing_not_zero=True,
        coverage=dict(counter), phase_coverage=stage_counts,
        output_hashes={p.name:digest(p.read_bytes()) for p in output.iterdir() if p.is_file()}))
    print(json.dumps(dict(coverage=counter,phase_coverage=stage_counts),indent=2))


if __name__=='__main__':
    main()
