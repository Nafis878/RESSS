"""Inventory, inspect for credentials, preserve hashes and stage exact bytes."""
import collections
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

ROOT=Path(__file__).resolve().parents[1]
PROJECT=ROOT/'self-timed-warning_part1_code_results'/'self-timed-warning'
STATE=ROOT/'.publish-state'
GIT=Path('C:/Program Files/Git/cmd/git.exe')
EXCLUDE={'.venv','venv','__pycache__','.git','node_modules','.pytest_cache','.mypy_cache',
         '.ruff_cache','.ipynb_checkpoints','tmp','.publish-state'}
PATTERNS={
    'github_token':rb'\b(?:gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{50,})\b',
    'aws_access_key':rb'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b',
    'private_key':rb'-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----',
    'slack_token':rb'\bxox[baprs]-[A-Za-z0-9-]{20,}\b',
}


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def git(*args):
    return subprocess.run([str(GIT),*args],cwd=ROOT,check=True,capture_output=True,text=True,encoding='utf-8')


def main():
    STATE.mkdir(exist_ok=True);files=[];excluded=collections.Counter();findings=[]
    for folder,dirs,names in os.walk(ROOT):
        for d in list(dirs):
            if d in EXCLUDE:excluded[d]+=1;dirs.remove(d)
        for name in names:
            p=Path(folder)/name
            if p.suffix.lower() in {'.pyc','.pyo'} or name in {'.DS_Store','Thumbs.db'}:continue
            assert not p.is_symlink(),f'Symlink requires review: {p.relative_to(ROOT)}'
            files.append(p)
    files.sort()
    for p in files:
        rel=p.relative_to(ROOT).as_posix()
        if p.name.lower() in {'.env','credentials.json','credentials.yml','id_rsa','id_ed25519'}:
            findings.append(dict(path=rel,reason='credential-like filename'))
        if p.stat().st_size<=12*1024**2 and p.suffix.lower() in {'.py','.md','.txt','.json','.yaml','.yml','.toml','.ini','.cfg','.sh','.ps1','.js','.env'}:
            data=p.read_bytes()
            for kind,pattern in PATTERNS.items():
                if re.search(pattern,data):findings.append(dict(path=rel,reason=kind))
    (STATE/'credential_scan.json').write_text(json.dumps(dict(findings=findings,values_never_printed=True),indent=2),encoding='utf-8')
    assert not findings,'Credential-like material found; inspect metadata privately before publishing'
    for p in files:assert p.stat().st_size<100*1024**2,f'LFS required: {p.relative_to(ROOT)}'
    protected=json.loads((PROJECT/'out/clock_regret_attention/protected_before.json').read_text())
    assert len(protected)==1025
    for name,digest in protected.items():assert sha(PROJECT/name)==digest,name
    manifest=json.loads((PROJECT/'out/clock_regret_attention/completion_manifest.json').read_text())
    for name,digest in manifest['frozen_hashes'].items():assert sha(PROJECT/name)==digest,name
    inventory=[dict(path=p.relative_to(ROOT).as_posix(),bytes=p.stat().st_size,sha256=sha(p)) for p in files]
    (STATE/'inventory.json').write_text(json.dumps(dict(files=inventory,excluded=dict(excluded),
        protected_old=1025,protected_attention=len(manifest['frozen_hashes']),credential_findings=0),indent=2),encoding='utf-8')
    pathspec=STATE/'paths.nul';pathspec.write_bytes(b''.join(r['path'].encode('utf-8')+b'\0' for r in inventory))
    git('init','--initial-branch=main')
    git('config','user.name','Nafis Wadud Ansari');git('config','user.email','ansari2305341800@diu.edu.bd')
    git('config','core.autocrlf','false');git('config','core.safecrlf','false')
    existing=git('remote').stdout.split()
    if 'origin' not in existing:git('remote','add','origin','https://github.com/Nafis878/RESSS.git')
    else:assert git('remote','get-url','origin').stdout.strip()=='https://github.com/Nafis878/RESSS.git'
    git('add','--force','--pathspec-from-file='+str(pathspec),'--pathspec-file-nul')
    tracked=git('ls-files','-z').stdout.split('\0');tracked=[p for p in tracked if p]
    assert set(tracked)=={r['path'] for r in inventory}
    print(json.dumps(dict(staged_files=len(tracked),total_mib=round(sum(r['bytes'] for r in inventory)/1024**2,2),
        credential_findings=0,old_hashes_verified=1025,attention_hashes_verified=len(manifest['frozen_hashes']),excluded=dict(excluded)),indent=2))


if __name__=='__main__':main()
