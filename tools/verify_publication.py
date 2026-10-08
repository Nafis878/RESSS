"""Verify every staged file against the byte-preserving publication inventory."""
import hashlib
import json
from pathlib import Path
import subprocess
from prepare_publication import ROOT,STATE,GIT


def verify():
    inventory=json.loads((STATE/'inventory.json').read_text())
    expected={r['path']:r for r in inventory['files']}
    data=subprocess.check_output([str(GIT),'ls-files','--stage','-z'],cwd=ROOT)
    records=[r for r in data.split(b'\0') if r];seen=set()
    for record in records:
        metadata,rawpath=record.split(b'\t',1);mode,object_id,stage=metadata.split()
        name=rawpath.decode('utf-8');seen.add(name)
        assert stage==b'0' and name in expected
        content=(ROOT/name).read_bytes()
        assert hashlib.sha256(content).hexdigest()==expected[name]['sha256'],name
        header=b'blob '+str(len(content)).encode('ascii')+b'\0'
        assert hashlib.sha1(header+content).hexdigest().encode('ascii')==object_id,name
    assert seen==set(expected)
    summary=dict(staged_files_verified=len(seen),staged_blobs_equal_original_bytes=True,
                 credential_findings=inventory['credential_findings'],old_protected_hashes=inventory['protected_old'],
                 attention_protected_hashes=inventory['protected_attention'])
    (STATE/'verification.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print(json.dumps(summary,indent=2))


if __name__=='__main__':verify()
