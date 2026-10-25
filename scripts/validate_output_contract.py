import csv
import json

with open('output.csv', 'r', encoding='utf-8') as f:
    reader = csv.reader(f)
    header = next(reader)
    rows = list(reader)

print('Header:', header)
print('Row count:', len(rows))
assert header == ['case_id', 'deletion_status', 'steps_json'], 'Invalid header'
assert len(rows) == 518, f'Expected 518 rows, got {len(rows)}'

# Check sorting
cids = [r[0] for r in rows]
assert cids == sorted(cids), 'Rows are not sorted by case_id string order!'

# Check each row format
na_count = 0
for idx, (cid, status, steps_str) in enumerate(rows):
    assert status in ['COMPLETE', 'INCOMPLETE', 'NOT_APPLICABLE'], f'Invalid status in {cid}: {status}'
    steps = json.loads(steps_str)
    if status == 'NOT_APPLICABLE':
        na_count += 1
        assert steps == [], f'NOT_APPLICABLE case {cid} must have empty steps'
    else:
        for s_idx, s in enumerate(steps, start=1):
            assert s['step_no'] == s_idx, f'Non-consecutive step_no in {cid}'
            assert s['phase'] in ['FINDING', 'REMEDIATION', 'VERIFICATION']

print('Validation PASSED! All 518 rows strictly conform to challenge contract.')
print(f'NOT_APPLICABLE count: {na_count}')
