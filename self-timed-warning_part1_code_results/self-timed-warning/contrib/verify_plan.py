"""Verify the hashes of contrib/PLAN.md: the original plan (text before the first amendment, with '(none)' under
'## Amendments', exactly as hashed on 2026-10-06) and the full amended file. Usage: python contrib/verify_plan.py"""
import hashlib
raw = open('contrib/PLAN.md', 'rb').read(); txt = raw.decode('utf-8')
recorded = [l.split()[0] for l in open('contrib/PLAN.sha256').read().splitlines() if len(l.split()) >= 2 and len(l.split()[0]) == 64]
original = txt.split('\n\n### Amendment 1')[0] + '\n(none)\n'
ok_orig = hashlib.sha256(original.encode('utf-8')).hexdigest() == recorded[0]
ok_full = hashlib.sha256(raw).hexdigest() == recorded[-1]
print(f'{"PASS" if ok_orig else "FAIL"}  original plan (before amendments) matches {recorded[0][:12]}')
print(f'{"PASS" if ok_full else "FAIL"}  full plan with amendments matches {recorded[-1][:12]}')
raise SystemExit(0 if ok_orig and ok_full else 1)
