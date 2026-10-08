"""Audit completeness, pairing and provenance without inventing a verdict for missing data."""
import hashlib
import os
import json
from pathlib import Path
import pandas as pd

ROOT = Path('out/contrib')
ENG = ['PHM08', 'FD001', 'FD002', 'FD003', 'FD004', 'NCMAPSS6']
MDS = ['FD001', 'FD002', 'FD003', 'FD004']


def main():
    checks = []
    def check(label, ok):
        checks.append({'check': label, 'pass': bool(ok)})
        print(('PASS  ' if ok else 'FAIL  ') + label)
    plan = Path('contrib/PLAN.md').read_bytes()
    recorded = [line.split()[0] for line in Path('contrib/PLAN.sha256').read_text().splitlines()
                if len(line.split()) >= 2 and len(line.split()[0]) == 64]
    check('amended plan hash unchanged', hashlib.sha256(plan).hexdigest() == recorded[-1])
    inputs = json.loads(Path('tools/DATA_SHA256.json').read_text())
    input_hashes = {name: hashlib.sha256(Path(name).read_bytes()).hexdigest() for name in inputs}
    check('all 21 supplied input hashes unchanged', len(inputs) == 21 and
          all(input_hashes[name] == ref['sha256'] for name, ref in inputs.items()))
    for folder in ['paper5', 'paper6']:
        p = Path(folder)
        # Paper6 reframes the same numerical evidence and has only TeX references.
        reference_numbers = Path('paper5/reference/numbers.json')
        check(f'{folder} numbers match reference values', json.loads((p / 'numbers.json').read_text()) ==
              json.loads(reference_numbers.read_text()))
        for name in ['manuscript.tex', 'supplementary.tex']:
            check(f'{folder} {name} text matches reference', (p / 'tex' / name).read_bytes() ==
                  (p / 'reference' / name).read_bytes())
    for name in ['test_cat.log', 'sim_checks_AC.txt', 'sim_checks_B.txt', 'sim_kmin_checks.txt', 'cat_equiv.txt',
                 'cat_leakage.txt', 'Battery_check.txt', 'Bearing_check.txt']:
        path = ROOT / name
        s = path.read_text(encoding='utf-8') if path.exists() else ''
        check(name, bool(s) and 'FAIL' not in s and 'STOP' not in s and 'PASS' in s)
        if name == 'test_cat.log':
            check('all eight CAT tests completed', 'ALL TESTS PASSED' in s and
                  all(f'PASS  T{i} ' in s for i in range(1, 9)))
    for ds in ENG + ['Battery']:
        p = ROOT / f'{ds}_cost.csv'
        if not p.exists():
            check(f'{ds} outputs present', False)
            continue
        x = pd.read_csv(p, low_memory=False); x = x[~x.policy.str.startswith('rep_')]
        fold = 'split' if ds == 'Battery' else 'fold'
        check(f'{ds} unique cost decisions', not x.duplicated([fold, 'lead_cycles', 'rho', 'policy', 'unit']).any())
        check(f'{ds} positive use and finite costs', x.use.gt(0).all() and x.cost.ge(1).all() and x[['use', 'cost']].notna().all().all())
        check(f'{ds} all splits', x[fold].nunique() == (8 if ds == 'Battery' else 5))
        check(f'{ds} all 16 cost cells', x[['lead_cycles', 'rho']].drop_duplicates().shape[0] == 16)
        sizes = x.groupby([fold, 'lead_cycles', 'rho', 'policy']).size().unstack('policy')
        check(f'{ds} identical unit counts per policy', sizes.notna().all().all() and sizes.nunique(axis=1).eq(1).all())
        for policy in ['CAT_a0.05', 'CATc_a0.05', 'STW_window', 'STW_cost', 'STW_cost_1se', 'age', 'perfect_foresight']:
            check(f'{ds} {policy} present', policy in set(x.policy))
        a = x[x.policy == 'CAT_a0.05'].set_index([fold, 'lead_cycles', 'rho', 'unit']).fail
        c = x[x.policy == 'CATc_a0.05'].set_index([fold, 'lead_cycles', 'rho', 'unit']).fail.reindex(a.index)
        check(f'{ds} cost-aware failure is bounded by bare CAT pointwise', c.notna().all() and (c.astype(int) <= a.astype(int)).all())
    for ds in MDS:
        p = ROOT / f'{ds}_M.csv'
        if not p.exists():
            check(f'{ds} M output', False); continue
        x = pd.read_csv(p)
        check(f'{ds} M unique paired units', not x.duplicated(['split', 'q', 'policy', 'unit']).any())
        check(f'{ds} M full grids', x.q.nunique() == 7 and x.split.nunique() == 5)
        sizes = x.groupby(['split', 'q', 'policy']).size().unstack('policy')
        check(f'{ds} M equal unit counts', sizes.notna().all().all() and sizes.nunique(axis=1).eq(1).all())
        for (split, q), g in x.groupby(['split', 'q']):
            ref = g[g.policy == 'perfect_grid']; perfect = ref.cost.sum() / ref.tlc.sum()
            rates = g.groupby('policy').apply(lambda z: z.cost.sum() / z.tlc.sum())
            check(f'{ds} fold {split} q={q} nonnegative grid M', ((rates / perfect - 1) >= -1e-12).all())
    check('bearing outputs present', all((ROOT / p).exists() for p in ['Bearing_units.csv', 'Bearing_settings.csv']))
    if (ROOT / 'contrib_numbers.json').exists():
        n = json.loads((ROOT / 'contrib_numbers.json').read_text())
        check('complete engine verdict', n['verdicts']['complete_engine_suite'] and n['verdicts']['primary_claim'] != 'incomplete')
    else: check('summary present', False)
    manifest = {}
    for p in sorted(ROOT.glob('*')):
        if p.is_file() and p.suffix in ['.csv', '.gz', '.json', '.txt', '.log', '.png', '.svg'] and p.name not in ['completion_audit.json', 'run_completion_audit.log']:
            manifest[p.name] = hashlib.sha256(p.read_bytes()).hexdigest()
    import platform, numpy, scipy, sklearn
    payload = {'complete': all(c['pass'] for c in checks), 'checks': checks, 'sha256': manifest,
               'environment': {'python': platform.python_version(), 'platform': platform.platform(),
                  'numpy': numpy.__version__, 'pandas': pd.__version__, 'scipy': scipy.__version__,
                  'scikit_learn': sklearn.__version__,
                  'threads': {k: os.environ.get(k) for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']}},
               'plan_sha256': hashlib.sha256(plan).hexdigest(),
               'input_sha256': input_hashes,
               'source_sha256': {str(p).replace('\\', '/'): hashlib.sha256(p.read_bytes()).hexdigest()
                                 for folder in ['.', 'kam', 'contrib', 'docs_contrib'] for p in sorted(Path(folder).glob('*'))
                                 if p.is_file() and p.suffix in ['.py','.md','.sha256','.txt'] and p.name != 'FINAL_REPORT.md'}}
    (ROOT / 'completion_audit.json').write_text(json.dumps(payload, indent=2) + '\n', encoding='utf-8')
    raise SystemExit(0 if payload['complete'] else 1)


if __name__ == '__main__': main()
