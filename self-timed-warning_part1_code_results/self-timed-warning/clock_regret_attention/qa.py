"""Render and inspectable text-bound checks; visual review remains required."""
import json
import fitz
from clock_regret_attention.run import OUT


def main():
    folder=OUT/'qa'; folder.mkdir(exist_ok=True); doc=fitz.open(OUT/'manuscript.pdf'); rows=[]
    for i,page in enumerate(doc):
        path=folder/f'page-{i+1}.png';page.get_pixmap(matrix=fitz.Matrix(1.4,1.4)).save(path)
        blocks=page.get_text('blocks'); content=[b for b in blocks if b[3]<page.rect.height-35]
        assert all(b[0]>=48 and b[2]<=page.rect.width-48 and b[1]>=35 for b in content)
        rows.append(dict(page=i+1,characters=len(page.get_text()),first_line=page.get_text().splitlines()[0],
                         body_bottom=max(b[3] for b in content),render=str(path)))
    assert doc.metadata['author']=='Nafis Wadud Ansari'
    (OUT/'pdf-qa.json').write_text(json.dumps(dict(pages=len(doc),metadata=doc.metadata,page_checks=rows,
        text_bounds_pass=True,visual_review='pending'),indent=2),encoding='utf-8')
    print(json.dumps(rows,indent=2))


if __name__=='__main__':main()
