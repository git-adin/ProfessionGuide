"""Build and verify a clean, directly installable ZIP; no runtime dependencies."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import hashlib, re
ROOT=Path(__file__).resolve().parents[1]
toc=(ROOT/'ProfessionGuide.toc').read_text()
files=[line.strip() for line in toc.splitlines() if line.strip() and not line.startswith('#')]
files+=['ProfessionGuide.toc','README.md','SOURCES.md','LICENSE']
version=re.search(r'^## Version: (.+)$',toc,re.M)[1]
out=ROOT/'dist'; out.mkdir(exist_ok=True)
for name in ['ProfessionGuide.zip',f'ProfessionGuide-{version}.zip']:
    with ZipFile(out/name,'w',ZIP_DEFLATED) as z:
        for file in sorted(files):
            z.write(ROOT/file,'ProfessionGuide/'+file)
    with ZipFile(out/name) as z:
        assert z.testzip() is None
        assert set(z.namelist())=={'ProfessionGuide/'+f for f in files}
        assert 'ProfessionGuide/ProfessionGuide.toc' in z.namelist()
sums=''.join(hashlib.sha256((out/name).read_bytes()).hexdigest()+'  '+name+'\n'
    for name in ['ProfessionGuide.zip',f'ProfessionGuide-{version}.zip'])
(out/'SHA256SUMS.txt').write_text(sums)
print(f'Built and verified {out / "ProfessionGuide.zip"}')
