import codecs

with codecs.open('scratch_output.txt', 'r', 'utf-16le', errors='ignore') as f:
    text = f.read()

import sys
sys.stdout.reconfigure(encoding='utf-8')

for doc in text.split('--- '):
    if not doc.strip(): continue
    doc_id = doc.split(' ---')[0]
    print(f"\\nDOC: {doc_id}")
    pages = doc.split('Page ')
    for page in pages[1:]:
        page_num = page.split(':')[0]
        content = page.split(':', 1)[1] if ':' in page else page
        
        keywords = ['attendance', 'condonation', 'grace', 'pass', 'supplementary', 'backlog', 'cgpa', 'hostel', 'credit', 'fee']
        lines = content.split('\\n')
        for i, line in enumerate(lines):
            line_lower = line.lower()
            if any(k in line_lower for k in keywords) and len(line.strip()) > 10:
                print(f"P{page_num}: {line.strip()}")
