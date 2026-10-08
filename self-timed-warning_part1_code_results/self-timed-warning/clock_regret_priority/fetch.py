"""Public primary-source retrieval; preserve status and never bypass access controls."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
from urllib.request import Request, urlopen
import pymupdf

OUT=Path('out/clock_regret_priority')
SOURCES={
    'drent2020_preprint':'https://www.eurandom.tue.nl/wp-content/uploads/2020/04/005-report.pdf',
    'khan2024_final':'https://raw.githubusercontent.com/mlresearch/v235/main/assets/khan24b/khan24b.pdf',
    'khan2024_arxiv':'https://arxiv.org/pdf/2305.11812v2',
    'fox1966_publisher':'https://pubsonline.informs.org/doi/pdf/10.1287/opre.14.3.533',
    'fox1966_jstor':'https://www.jstor.org/stable/pdf/168209.pdf',
}


def one(item):
    name,url=item
    result={'name':name,'url':url}
    try:
        with urlopen(Request(url,headers={'User-Agent':'Research verification'}),timeout=20) as response:
            body=response.read()
            result.update(status=response.status,resolved_url=response.url,bytes=len(body))
        if not body.startswith(b'%PDF'):
            result.update(pdf_recovered=False,reason='Response was not a PDF')
            return result
        destination=OUT/'primary_cache'/f'{name}.pdf'
        destination.write_bytes(body)
        doc=pymupdf.open(destination)
        text='\n\n'.join(f'=== PDF PAGE {i+1} ===\n'+p.get_text() for i,p in enumerate(doc))
        destination.with_suffix('.txt').write_text(text,encoding='utf-8')
        result.update(pdf_recovered=True,pages=len(doc),text_characters=len(text),
                      sha256=hashlib.sha256(body).hexdigest(),local_pdf=destination.as_posix())
    except Exception as error:
        result.update(pdf_recovered=False,reason=str(error))
    return result


def main():
    (OUT/'primary_cache').mkdir(parents=True,exist_ok=True)
    with ThreadPoolExecutor(max_workers=4) as pool:
        results=list(pool.map(one,SOURCES.items()))
    (OUT/'retrieval.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
    print(json.dumps(results,indent=2),flush=True)


if __name__=='__main__': main()
