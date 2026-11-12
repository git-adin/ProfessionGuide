from pathlib import Path
import sys, urllib.request
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / '.tools'))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / '.tools'))
from bs4 import BeautifulSoup
cache = Path(__file__).parent / '.source-cache'
cache.mkdir(exist_ok=True)
for slug in sys.argv[1:]:
    path = cache / (slug + '.html')
    if not path.exists():
        request = urllib.request.Request('https://www.wow-professions.com/forever/' + slug + '-leveling-guide', headers={'User-Agent': 'Mozilla/5.0'})
        path.write_bytes(urllib.request.urlopen(request, timeout=30).read())
    print(slug + ': source cached locally (excluded from release)')
