#!/usr/bin/env python3
"""
批量为女优条目添加 Wikipedia 缩略图
"""
import os, re, json, urllib.request, urllib.parse, sys, time

ROWS = {'あ','か','さ','た','な','は','ま','や','ら','わ'}
CACHE_FILE = os.path.join(os.path.dirname(__file__), 'wiki_images_cache.json')

def is_actress_path(rel):
    parts = rel.replace(os.sep, '/').split('/')
    return len(parts) >= 2 and parts[0] in ROWS and len(parts[1]) == 1

def get_wiki_image(name):
    for site, domain in [('zh', 'zh.wikipedia.org'), ('ja', 'ja.wikipedia.org')]:
        # Direct query
        params = urllib.parse.urlencode({
            'action': 'query', 'prop': 'pageimages',
            'titles': name, 'format': 'json', 'pithumbsize': 300
        })
        try:
            req = urllib.request.Request(f'https://{domain}/w/api.php?{params}',
                                        headers={'User-Agent': 'JavWiki/1.0'})
            resp = urllib.request.urlopen(req, timeout=10)
            data = json.loads(resp.read())
            for pid, info in data.get('query', {}).get('pages', {}).items():
                if pid != '-1' and 'thumbnail' in info:
                    return info['thumbnail']['source']
        except:
            pass
        time.sleep(0.3)
        
        # Search
        for search_term in [name, name + ' AV女優']:
            params = urllib.parse.urlencode({
                'action': 'query', 'list': 'search',
                'srsearch': search_term, 'format': 'json', 'srlimit': 3
            })
            try:
                req = urllib.request.Request(f'https://{domain}/w/api.php?{params}',
                                            headers={'User-Agent': 'JavWiki/1.0'})
                resp = urllib.request.urlopen(req, timeout=10)
                data = json.loads(resp.read())
                for r in data.get('query', {}).get('search', []):
                    title = r['title']
                    params2 = urllib.parse.urlencode({
                        'action': 'query', 'prop': 'pageimages',
                        'titles': title, 'format': 'json', 'pithumbsize': 300
                    })
                    try:
                        req2 = urllib.request.Request(f'https://{domain}/w/api.php?{params2}',
                                                     headers={'User-Agent': 'JavWiki/1.0'})
                        resp2 = urllib.request.urlopen(req2, timeout=10)
                        data2 = json.loads(resp2.read())
                        for pid, info in data2.get('query', {}).get('pages', {}).items():
                            if pid != '-1' and 'thumbnail' in info:
                                return info['thumbnail']['source']
                    except:
                        pass
            except:
                pass
            time.sleep(0.3)
    return None

def add_thumbnail(fp, url):
    with open(fp, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if 'thumbnail:' in content:
        return True
    
    lines = content.split('\n')
    found_first = False
    pos = None
    for i, line in enumerate(lines):
        if line.strip() == '---' and not found_first:
            found_first = True
        elif line.strip() == '---' and found_first:
            pos = i
            break
    
    if pos is None:
        return False
    
    lines.insert(pos, f'thumbnail: {url}')
    with open(fp, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    return True

def main():
    src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src'))
    
    files = []
    for root, dirs, fnames in os.walk(src_dir):
        rel = os.path.relpath(root, src_dir)
        if not is_actress_path(rel):
            continue
        for f in fnames:
            if f.endswith('.md') and f not in ('index.md', 'README.md'):
                files.append(os.path.join(root, f))
    
    print(f"女优文件: {len(files)}", flush=True)
    
    cache = {}
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r') as f:
            cache = json.load(f)
    
    stats = {'found': 0, 'not_found': 0, 'error': 0}
    
    for fp in sorted(files):
        with open(fp, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if 'thumbnail:' in content:
            continue
        
        m = re.search(r'^name:\s*(.+)$', content, re.MULTILINE)
        if m:
            name = m.group(1).strip()
        else:
            # Try H1 heading
            m = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
            if m:
                name = m.group(1).strip()
            else:
                name = os.path.splitext(os.path.basename(fp))[0]
        
        if not name:
            print(f"  ERROR: no name in {fp}", flush=True)
            stats['error'] += 1
            continue
        
        if name in cache and cache[name] is None:
            stats['not_found'] += 1
            continue
        if name in cache and cache[name]:
            add_thumbnail(fp, cache[name])
            stats['found'] += 1
            continue
        
        print(f"  {name}... ", end='', flush=True)
        url = get_wiki_image(name)
        time.sleep(0.5)
        
        if url:
            print(f"OK", flush=True)
            cache[name] = url
            add_thumbnail(fp, url)
            stats['found'] += 1
        else:
            print(f"NOT_FOUND", flush=True)
            cache[name] = None
            stats['not_found'] += 1
        
        # Save cache periodically
        if (stats['found'] + stats['not_found']) % 10 == 0:
            with open(CACHE_FILE, 'w') as f:
                json.dump(cache, f, ensure_ascii=False, indent=2)
    
    with open(CACHE_FILE, 'w') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)
    
    print(f"\n结果: 找到{stats['found']}, 未找到{stats['not_found']}, 错误{stats['error']}", flush=True)

if __name__ == '__main__':
    main()
