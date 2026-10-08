"""Two single-threaded queues, each stopping on the first failed stage."""
import json
import os
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone

queues = {'a': [('FD002', ['contrib/cat_run.py','FD002']), ('FD004', ['contrib/cat_run.py','FD004'])],
          'b': [('FD003', ['contrib/cat_run.py','FD003']), ('PHM08', ['contrib/cat_run.py','PHM08']),
                ('NCMAPSS6', ['contrib/cat_run.py','NCMAPSS6']), ('Battery', ['contrib/cat_battery.py']),
                ('Bearing', ['contrib/cat_bearing.py'])]}


def main():
    key=sys.argv[1]; out=Path('out/contrib')
    for name in ['test_cat.log','cat_equiv.txt','cat_leakage.txt']:
        s=(out/name).read_text()
        assert 'PASS' in s and 'FAIL' not in s and 'STOP' not in s, f'Gate not passed: {name}'
    env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',PYTHONUTF8='1')
    status=[]
    for label,args in queues[key]:
        item={'stage':label,'started_utc':datetime.now(timezone.utc).isoformat(),'state':'running'}
        status.append(item); path=out/f'queue_{key}.json';path.write_text(json.dumps(status,indent=2))
        print(f'Queue {key}: {label} started',flush=True)
        with (out/f'run_{label}_completion.log').open('w',encoding='utf-8') as log:
            r=subprocess.run([sys.executable,*args],env=env,stdout=log,stderr=subprocess.STDOUT)
        item.update(state='passed' if r.returncode==0 else 'failed',exit_code=r.returncode,
                    finished_utc=datetime.now(timezone.utc).isoformat())
        path.write_text(json.dumps(status,indent=2));print(f'Queue {key}: {label} {item["state"]}',flush=True)
        if r.returncode: raise SystemExit(r.returncode)


if __name__=='__main__':main()
