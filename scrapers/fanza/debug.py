from bs4 import BeautifulSoup
import re

with open('../../src/_meta/rankings/debug_202412.html', 'r', encoding='utf-8') as f:
    html = f.read()

soup = BeautifulSoup(html, 'html.parser')

# Find all links with /cid/
links = soup.find_all('a', href=re.compile(r'/cid/'))
print(f'Found {len(links)} links with /cid/')

for i, link in enumerate(links[:5]):
    print(f'\nLink {i}:')
    print(f'  href: {link.get("href")}')
    print(f'  text: {link.get_text(strip=True)[:100]}')
    print(f'  parent: {link.parent.name if link.parent else None}')

# Find list items
items = soup.select('ul[class*="list"] li')
print(f'\nFound {len(items)} list items')

for i, item in enumerate(items[:3]):
    print(f'\nItem {i}:')
    print(f'  text: {item.get_text(strip=True)[:200]}')
    print(f'  html: {str(item)[:500]}')
