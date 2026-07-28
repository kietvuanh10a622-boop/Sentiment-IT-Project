import json
from pathlib import Path

path = Path('articles_backup.json')
out_path = Path('signals_dataset.js')
with path.open(encoding='utf-8') as f:
    rows = json.load(f)

out = []
for item in rows:
    title = str(item.get('title') or '').replace('\n', ' ').replace('\r', ' ').strip()
    link = str(item.get('link') or '').strip()
    source = str(item.get('source_name') or item.get('source') or 'Unknown').strip()
    category = str(item.get('category') or item.get('category_hint') or 'General').strip()
    sentiment = str(item.get('sentiment_label') or item.get('sentiment') or 'Neutral').strip()
    score = float(item.get('sentiment_score') or 0)
    date = str(item.get('date') or '')
    out.append({
        'date': date,
        'title': title,
        'link': link,
        'source': source,
        'source_name': source,
        'category': category,
        'sentiment': sentiment,
        'sentiment_score': score,
    })

out_path.write_text('const dataset = ' + json.dumps(out, ensure_ascii=False, indent=2) + ';\nwindow.__signalsDataset = dataset;\n', encoding='utf-8')
print(f'Wrote {len(out)} rows to {out_path}')
