import sys
import re

sys.stdout.reconfigure(encoding='utf-8')

with open('debug_full.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Look for RSC data
rsc_pattern = r'self\.__next_f\.push\(\[.*?\]\)'
rsc_matches = re.findall(rsc_pattern, html)
print(f'Found {len(rsc_matches)} RSC chunks')

# Check for specific keywords
keywords = ['product', 'item', 'title', 'name', 'image', 'rank', 'cid', 'dmm']
for kw in keywords:
    count = html.lower().count(kw)
    if count > 0:
        print(f'Keyword "{kw}": {count} occurrences')

# Look for URLs with product IDs
url_pattern = r'https?://[^"\'>\s]+'
urls = re.findall(url_pattern, html[:50000])
product_urls = [u for u in urls if '/digital/' in u or '/mono/' in u]
print(f'\nProduct URLs found: {len(product_urls)}')
for u in product_urls[:5]:
    print(f'  {u}')
