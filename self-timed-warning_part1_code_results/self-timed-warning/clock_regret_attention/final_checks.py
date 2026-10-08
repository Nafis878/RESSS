"""Capture final tests/verifiers with clean UTF-8 outputs and real exit codes."""
import json
from pathlib import Path
import subprocess
import sys
from clock_regret_attention.run import OUT,protect


def main():
    checks={}
    commands=[('unit-tests.log',['-m','unittest','clock_regret_attention.test_core','clock_regret_attention.test_integration','-v']),
              ('verification.json',['-m','clock_regret_attention.verify']),
              ('followup-verification.json',['-m','clock_regret_attention.verify_followup']),
              ('hybrid-demo.log',['-m','clock_regret_attention.demo'])]
    for name,args in commands:
        result=subprocess.run([sys.executable,*args],capture_output=True,text=True,encoding='utf-8')
        (OUT/name).write_text(result.stdout+result.stderr,encoding='utf-8')
        assert result.returncode==0,(name,result.stdout,result.stderr)
        checks[name]=dict(exit_code=0)
        print(name+' passed',flush=True)
    checks['protected_artifacts_unchanged']=protect()
    (OUT/'final-checks.json').write_text(json.dumps(checks,indent=2),encoding='utf-8')


if __name__=='__main__':main()
