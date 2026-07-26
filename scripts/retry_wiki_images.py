#!/usr/bin/env python3
"""
针对未找到图片的女优，尝试使用日文名/英文名搜索 Wikipedia 图片
"""
import os, re, json, urllib.request, urllib.parse, sys, time

ROWS = {'あ','か','さ','た','な','は','ま','や','ら','わ'}

def get_wiki_image(name):
    """Search with a specific name on Wikipedia and return image URL."""
    for site, domain in [('zh', 'zh.wikipedia.org'), ('ja', 'ja.wikipedia.org')]:
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
        time.sleep(0.5)
        
        # Search
        for term in [name, name + ' AV女優']:
            params = urllib.parse.urlencode({
                'action': 'query', 'list': 'search',
                'srsearch': term, 'format': 'json', 'srlimit': 5
            })
            try:
                req = urllib.request.Request(f'https://{domain}/w/api.php?{params}',
                                            headers={'User-Agent': 'JavWiki/1.0'})
                resp = urllib.request.urlopen(req, timeout=10)
                data = json.loads(resp.read())
                for r in data.get('query', {}).get('search', []):
                    title = r['title']
                    if 'AV女優' in title or '(女優)' in title or '(女优)' in title:
                        continue  # Skip category pages
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

def extract_jp_name(content):
    """Extract Japanese name from markdown fields."""
    m = re.search(r'-\s*\*\*日文名\*\*\s*:\s*(.+)$', content, re.MULTILINE)
    if m: return m.group(1).strip()
    m = re.search(r'-\s*\*\*读音\*\*\s*:\s*(.+)$', content, re.MULTILINE)
    if m: return m.group(1).strip()
    m = re.search(r'-\s*\*\*英文名\*\*\s*:\s*(.+)$', content, re.MULTILINE)
    if m: return m.group(1).strip()
    return None

def main():
    # Find files without thumbnails
    files = []
    for root, dirs, fnames in os.walk('src'):
        rel = os.path.relpath(root, 'src')
        parts = rel.replace(os.sep, '/').split('/')
        if not (len(parts) >= 2 and parts[0] in ROWS and len(parts[1]) == 1):
            continue
        for f in fnames:
            if f.endswith('.md') and f not in ('index.md', 'README.md'):
                files.append(os.path.join(root, f))
    
    print(f'总计: {len(files)} 个文件', flush=True)
    
    cache_file = 'scripts/wiki_images_cache.json'
    cache = {}
    if os.path.exists(cache_file):
        with open(cache_file, 'r') as f:
            cache = json.load(f)
    
    # Known manual mappings for actresses on Japanese Wikipedia
    manual_map = {
        '蒼井空': '蒼井そら',
        '波多野結衣': '波多野結衣',
        '桃乃木かな': '桃乃木かな',
        '桃乃木香奈': '桃乃木かな',
        '橋本有菜': '橋本有菜',
        '三上悠亚': '三上悠亜',
        '水卜樱': '水卜さくら',
        '水卜さくら': '水卜さくら',
        '桜木凛': '桜木凛',
        '春菜はな': '春菜はな',
        '水菜丽': '水菜麗',
        '泷泽萝拉': '滝沢ローラ',
        '松本一香': '松本いちか',
        '美園和花': '美園和花',
        '美谷朱音': '美谷朱音',
        '由愛可奈': '由愛可奈',
        '篠田步美': '篠田ゆう',
        '白鳥香里奈': '白鳥香里奈',
        '澁谷果歩': '澁谷果歩',
        '神咲詩織': '神咲詩織',
    }
    
    found_count = 0
    notfound_count = 0
    
    for fp in sorted(files):
        with open(fp, 'r', encoding='utf-8') as fh:
            content = fh.read()
        
        if 'thumbnail:' in content:
            continue
        
        # Get name from heading
        m = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        cn_name = m.group(1).strip() if m else os.path.splitext(os.path.basename(fp))[0]
        
        # Skip if already in cache as found
        if cn_name in cache and cache.get(cn_name):
            # Add thumbnail that was in cache but not in file
            add_thumbnail(fp, cache[cn_name])
            found_count += 1
            continue
        
        # In cache as NOT_FOUND - try again with alternate names
        in_cache_as_notfound = cn_name in cache and cache.get(cn_name) is None
        
        # Collect all names to try (including retry of original)
        names_to_try = [cn_name]
        jp_name = extract_jp_name(content)
        if jp_name and jp_name not in names_to_try:
            names_to_try.append(jp_name)
        if cn_name in manual_map and manual_map[cn_name] not in names_to_try:
            names_to_try.append(manual_map[cn_name])
        
        # Also try traditional Chinese (common mapping for common chars)
        trad_map = str.maketrans('爱体国学会画节续绝结奖泽亚啬樱', '愛體國學會畫節續絕結獎澤亞嗇櫻')
        trad_name = cn_name.translate(trad_map)
        if trad_name != cn_name and trad_name not in names_to_try:
            names_to_try.append(trad_name)
        
        print(f'  {cn_name} ({len(names_to_try)} variants)... ', end='', flush=True)
        
        url = None
        for try_name in names_to_try:
            url = get_wiki_image(try_name)
            if url:
                break
            time.sleep(0.3)
        
        if url:
            print('OK', flush=True)
            cache[cn_name] = url
            add_thumbnail(fp, url)
            found_count += 1
        else:
            print('NOT_FOUND', flush=True)
            cache[cn_name] = None
            notfound_count += 1
        
        # Save periodically
        if (found_count + notfound_count) % 10 == 0:
            with open(cache_file, 'w') as f:
                json.dump(cache, f, ensure_ascii=False, indent=2)
    
    with open(cache_file, 'w') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)
    
    print(f'\n完成: 新增{found_count}, 仍无{notfound_count}', flush=True)

def add_thumbnail(fp, url):
    with open(fp, 'r', encoding='utf-8') as f:
        content = f.read()
    if 'thumbnail:' in content:
        return True
    
    if content.startswith('---'):
        lines = content.split('\n')
        found_first = False
        pos = None
        for i, line in enumerate(lines):
            if line.strip() == '---' and not found_first:
                found_first = True
            elif line.strip() == '---' and found_first:
                pos = i
                break
        if pos is not None:
            lines.insert(pos, f'thumbnail: {url}')
            with open(fp, 'w', encoding='utf-8') as f:
                f.write('\n'.join(lines))
            return True
    else:
        # No YAML frontmatter - add it
        lines = content.split('\n')
        # First line is # name
        new_lines = ['---', f'thumbnail: {url}', '---', '', *lines]
        with open(fp, 'w', encoding='utf-8') as f:
            f.write('\n'.join(new_lines))
        return True
    return False

if __name__ == '__main__':
    main()
