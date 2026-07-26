#!/usr/bin/env python3
"""Process 20 files per run, caching results"""
import urllib.request, urllib.parse, json, os, re, sys, time

ROWS = {'あ','か','さ','た','な','は','ま','や','ら','わ'}

# Load map from external file
map_file = os.path.join(os.path.dirname(__file__), 'ja_name_map.json')
with open(map_file, 'r', encoding='utf-8') as f:
    JA_NAME_MAP = json.load(f)

cache_file = os.path.join(os.path.dirname(__file__), 'image_cache2.json')
cache = {}
if os.path.exists(cache_file):
    with open(cache_file, 'r', encoding='utf-8') as f:
        cache = json.load(f)

def get_one_image(wiki_name):
    try:
        params = urllib.parse.urlencode({
            'action': 'query', 'prop': 'pageprops|pageimages',
            'titles': wiki_name, 'format': 'json',
            'ppprop': 'page_image_free', 'pithumbsize': 400
        })
        url = f'https://ja.wikipedia.org/w/api.php?{params}'
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        resp = urllib.request.urlopen(req, timeout=10)
        data = json.loads(resp.read())
        for pid, info in data.get('query', {}).get('pages', {}).items():
            if pid != '-1':
                if 'pageprops' in info:
                    img = info['pageprops'].get('page_image_free')
                    if img:
                        enc = urllib.parse.quote(img.replace(' ', '_'), safe='')
                        return f'https://upload.wikimedia.org/wikipedia/commons/thumb/{enc[0]}/{enc[:2]}/{enc}/400px-{enc}'
                if 'thumbnail' in info:
                    return info['thumbnail']['source']
                return None
    except:
        return None
    return None

def add_image(fp, url):
    with open(fp, 'r', encoding='utf-8') as f:
        content = f.read()
    if 'thumbnail:' in content or '<img' in content:
        return
    m = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
    name = m.group(1).strip() if m else ''
    lines = content.split('\n')
    if lines[0].strip() == '---':
        end = next((i for i in range(1, len(lines)) if lines[i].strip() == '---'), None)
        if end: lines.insert(end, f'thumbnail: {url}')
        content = '\n'.join(lines)
    else:
        content = f'---\nthumbnail: {url}\n---\n\n{content}'
    lines = content.split('\n')
    h = next((i for i, l in enumerate(lines) if l.startswith('# ') and not l.startswith('##')), None)
    if h is not None:
        tag = f'<img src="{url}" alt="{name}" class="actress-photo" style="float: right; max-width: 280px; margin-left: 20px; border-radius: 8px;" />'
        ins = h + 1
        if ins < len(lines) and lines[ins].strip() == '': ins += 1
        lines.insert(ins, ''); lines.insert(ins, tag)
        content = '\n'.join(lines)
    with open(fp, 'w', encoding='utf-8') as f:
        f.write(content)

# Collect files needing images
files = []
for root, dirs, fnames in os.walk('src'):
    rel = os.path.relpath(root, 'src')
    parts = rel.replace(os.sep, '/').split('/')
    if len(parts) >= 2 and parts[0] in ROWS and len(parts[1]) == 1:
        for f in fnames:
            if f.endswith('.md') and f not in ('index.md', 'README.md'):
                fp = os.path.join(root, f)
                with open(fp, 'r', encoding='utf-8') as fh:
                    content = fh.read()
                if 'thumbnail:' not in content and '<img' not in content:
                    files.append(fp)

files.sort()
print(f'剩余: {len(files)}', flush=True)

BATCH_SIZE = 15
files = files[:BATCH_SIZE]

added = 0
for fp in files:
    with open(fp, 'r', encoding='utf-8') as f:
        content = f.read()
    if 'thumbnail:' in content or '<img' in content:
        continue
    m = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
    name = m.group(1).strip() if m else ''
    name = re.sub(r'\s*[（(][^）)]*[）)]', '', name).strip()
    
    if name in cache:
        if cache[name]:
            add_image(fp, cache[name])
            added += 1
        continue
    
    ja_name = JA_NAME_MAP.get(name)
    if not ja_name:
        cache[name] = None
        continue
    
    url = get_one_image(ja_name)
    time.sleep(0.5)
    
    if url:
        cache[name] = url
        add_image(fp, url)
        added += 1
    else:
        cache[name] = None

# Save cache
with open(cache_file, 'w', encoding='utf-8') as f:
    json.dump(cache, f, ensure_ascii=False, indent=2)

print(f'本轮添加: {added}', flush=True)
print(f'总成功: {sum(1 for v in cache.values() if v)}', flush=True)
