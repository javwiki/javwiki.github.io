#!/usr/bin/env python3
"""
批量获取女优 Wikipedia 图片并更新到 YAML frontmatter
用法: PYTHONIOENCODING=utf-8 python scripts/fetch_wiki_images.py
"""
import os, re, json, urllib.request, urllib.parse, sys, time

# 五十音目录
ROWS = {'あ','か','さ','た','な','は','ま','や','ら','わ'}
COLS = {'あ','い','う','え','お'}

def is_actress_dir(rel):
    parts = rel.replace(os.sep, '/').split('/')
    return len(parts) >= 2 and parts[0] in ROWS and parts[1] in COLS

def get_wiki_image(name):
    """从 Wikipedia 获取女优图片 URL。先试中文维基，再试日文维基。"""
    for site, domain in [('zh', 'zh.wikipedia.org'), ('ja', 'ja.wikipedia.org')]:
        # 直接查询
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

        # 搜索
        params = urllib.parse.urlencode({
            'action': 'query', 'list': 'search',
            'srsearch': name, 'format': 'json', 'srlimit': 5
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
    return None

def extract_name(fp):
    with open(fp, 'r', encoding='utf-8') as f:
        content = f.read()
    m = re.search(r'^name:\s*(.+)$', content, re.MULTILINE)
    if m:
        return m.group(1).strip()
    return os.path.splitext(os.path.basename(fp))[0]

def has_thumbnail(fp):
    with open(fp, 'r', encoding='utf-8') as f:
        return 'thumbnail:' in f.read()

def add_thumbnail(fp, url):
    with open(fp, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find the end of YAML frontmatter
    lines = content.split('\n')
    found_first = False
    insert_pos = None
    
    for i, line in enumerate(lines):
        if line.strip() == '---' and not found_first:
            found_first = True
        elif line.strip() == '---' and found_first:
            # End of frontmatter
            insert_pos = i
            break
    
    if insert_pos is None:
        # No frontmatter? Try to add one
        return False
    
    # Insert thumbnail line before the closing ---
    # First check if there's already a thumbnail field
    for i in range(0, insert_pos):
        if lines[i].strip().startswith('thumbnail:'):
            # Already exists
            return True
    
    # Insert thumbnail before the closing ---
    # Find the right spot - after name and type fields
    lines.insert(insert_pos, f'thumbnail: {url}')
    
    with open(fp, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    return True


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    src_dir = os.path.join(script_dir, '..', 'src')
    src_dir = os.path.abspath(src_dir)
    
    # Collect actress files
    files = []
    for root, dirs, fnames in os.walk(src_dir):
        rel = os.path.relpath(root, src_dir)
        if not is_actress_dir(rel):
            continue
        for f in fnames:
            if f.endswith('.md') and f not in ('index.md', 'README.md'):
                files.append(os.path.join(root, f))
    
    print(f"找到 {len(files)} 个女优文件", file=sys.stderr)
    
    # Load existing mapping if available
    mapping_file = os.path.join(script_dir, 'wiki_images.json')
    mapping = {}
    if os.path.exists(mapping_file):
        with open(mapping_file, 'r') as f:
            mapping = json.load(f)
    
    results = {'found': 0, 'not_found': 0, 'skipped': 0, 'error': []}
    
    for fp in sorted(files):
        if has_thumbnail(fp):
            results['skipped'] += 1
            continue
        
        name = extract_name(fp)
        if not name:
            results['error'].append(f"{fp}: no name field")
            continue
        
        # Check cache
        if name in mapping and mapping[name]:
            url = mapping[name]
            add_thumbnail(fp, url)
            results['found'] += 1
            continue
        elif name in mapping and mapping[name] is None:
            results['not_found'] += 1
            continue
        
        # Fetch
        print(f"  {name}...", file=sys.stderr)
        url = get_wiki_image(name)
        time.sleep(0.5)  # Rate limit
        
        if url:
            mapping[name] = url
            add_thumbnail(fp, url)
            print(f"    -> {url}", file=sys.stderr)
            results['found'] += 1
        else:
            mapping[name] = None
            print(f"    -> NOT_FOUND", file=sys.stderr)
            results['not_found'] += 1
        
        # Save mapping periodically
        if results['found'] % 10 == 0:
            with open(mapping_file, 'w') as f:
                json.dump(mapping, f, ensure_ascii=False, indent=2)
    
    # Final save
    with open(mapping_file, 'w') as f:
        json.dump(mapping, f, ensure_ascii=False, indent=2)
    
    print(f"\n完成: 找到{results['found']}, 未找到{results['not_found']}, 跳过{results['skipped']}", file=sys.stderr)

if __name__ == '__main__':
    main()
