#!/usr/bin/env python3
"""Export visible Codex rollout events to contest schema 1.0; never invent events.

The official collector at 10743591 uses Claude message envelopes for Codex too,
which does not parse response_item rollouts. This adapter preserves visible
messages and tool calls/results, and records source line numbers and SHA-256.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re


def export(source, root, team, login):
    raw = source.read_bytes()
    rows = [json.loads(line) for line in raw.splitlines() if line.strip()]
    meta = rows[0]['payload']
    if meta.get('source') != 'cli':
        raise ValueError('Only a primary CLI session may be exported')
    sid = meta['id']
    # Original transcript dates, not the backfill date.
    day = meta['timestamp'][:10]
    rel = Path(login) / day / f'codex__{sid}.jsonl'
    events, skipped, calls = [], Counter(), {}
    model = None
    for lineno, raw_event in enumerate(rows, 1):
        p = raw_event.get('payload', {})
        if raw_event.get('type') == 'turn_context':
            model = p.get('model', model)
        if raw_event.get('type') != 'response_item':
            skipped[raw_event.get('type', 'unknown')] += 1
            continue
        kind = p.get('type')
        ev = None
        if kind == 'message' and p.get('role') in ('user', 'assistant'):
            if p.get('channel') in ('analysis', 'summary'):
                skipped['internal_channel'] += 1
                continue
            content = p.get('content', [])
            chunks = [c['text'] for c in content if c.get('type') in ('input_text', 'output_text')]
            text = '\n'.join(chunks)
            if p.get('role') == 'user' and text.startswith(('# AGENTS.md', '<environment_context>', '<permissions')):
                skipped['environment_instructions'] += 1
                continue
            if text:
                ev = {'role': p['role'], 'text': text}
        elif kind in ('function_call', 'custom_tool_call'):
            name, call = p['name'], p['call_id']
            calls[call] = name
            data = p.get('arguments', p.get('input'))
            if isinstance(data, str):
                try: data = json.loads(data)
                except ValueError: pass
            ev = {'role': 'tool', 'tool_name': name, 'tool_call_id': call, 'input': data, 'output': None}
        elif kind in ('function_call_output', 'custom_tool_call_output'):
            call = p['call_id']
            ev = {'role': 'tool', 'tool_name': calls.get(call, '<result>'), 'tool_call_id': call, 'input': None, 'output': p.get('output')}
        if ev is None:
            skipped[kind or 'unknown_response'] += 1
            continue
        item = {'schema_version': '1.0', 'session_id': sid, 'team_id': team,
                'github_login': login, 'tool': 'codex', 'seq': len(events),
                'ts': raw_event['timestamp'], **ev,
                'metadata': {'source_line': lineno, 'source_type': kind}}
        if model: item['model'] = model
        events.append(item)
    encoded = ''.join(json.dumps(e, ensure_ascii=False) + '\n' for e in events)
    # Stop before writing; do not publish or silently rewrite credential-bearing sessions.
    secret_patterns = [r'gh[pousr]_[A-Za-z0-9]{30,}', r'github_pat_[A-Za-z0-9_]{40,}',
                       r'sk-[A-Za-z0-9_-]{32,}', r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----[\r\n]+[A-Za-z0-9+/=\r\n]{64,}']
    for pattern in secret_patterns:
        if re.search(pattern, encoded): raise ValueError('Potential credential detected; session not exported')
    dest = root / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(encoded)
    manifest = {'schema_version': '1.0', 'team_id': team, 'github_login': login,
                'generator': 'velamotion-codex-rollout-adapter@1.0.0',
                'updated_at': datetime.now(timezone.utc).isoformat(),
                'sessions': [{'session_id': sid, 'tool': 'codex',
                              'started_at': events[0]['ts'], 'last_event_at': events[-1]['ts'],
                              'event_count': len(events), 'file_path': 'logs/' + str(rel),
                              'collection_mode': 'cli',
                              'data_completeness_warning': 'Historical backfill of visible user/assistant messages and tool calls/results only. Environment instructions, reasoning, images and runtime bookkeeping excluded; no claim of official automatic collection or complete project history.',
                              'source_file': source.name, 'source_sha256': hashlib.sha256(raw).hexdigest(),
                              'export_sha256': hashlib.sha256(encoded.encode()).hexdigest(),
                              'skipped_event_types': dict(skipped)}]}
    (root / login / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'file': str(dest), 'events': len(events), 'bytes': len(encoded.encode()), 'source_sha256': hashlib.sha256(raw).hexdigest()}))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--team', required=True)
    parser.add_argument('--login', required=True)
    a = parser.parse_args()
    export(a.source, a.out, a.team, a.login)
