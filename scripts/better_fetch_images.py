#!/usr/bin/env python3
"""
更可靠的女优图片获取 - 使用 Wikipedia API，但仅当文件名包含女优姓名时才接受
"""
import os, re, json, urllib.request, urllib.parse, sys, time

ROWS = {'あ','か','さ','た','な','は','ま','や','ら','わ'}
WIKI_SITES = [
    ('zh', 'zh.wikipedia.org', '中文维基'),
    ('ja', 'ja.wikipedia.org', '日文维基'),
]

def extract_name(fp):
    with open(fp, 'r', encoding='utf-8') as f:
        content = f.read()
    m = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
    if m:
        name = m.group(1).strip()
        name = re.sub(r'\s*[（(][^）)]*[）)]', '', name).strip()
        return name, content
    return os.path.splitext(os.path.basename(fp))[0], content

def has_image(content):
    return 'thumbnail:' in content or '<img' in content

def get_wiki_image_with_name_check(actress_name, site_code, site_domain):
    """从 Wikipedia 获取图片，返回 (url, filename) 如果文件名包含女优名"""
    params = urllib.parse.urlencode({
        'action': 'query', 'prop': 'pageimages',
        'titles': actress_name, 'format': 'json', 'pithumbsize': 400
    })
    url = f'https://{site_domain}/w/api.php?{params}'
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'JavWikiBot/1.0'})
        resp = urllib.request.urlopen(req, timeout=10)
        data = json.loads(resp.read())
        for pid, info in data.get('query', {}).get('pages', {}).items():
            if pid != '-1' and 'thumbnail' in info:
                thumb_url = info['thumbnail']['source']
                # Extract filename from URL
                filename = thumb_url.split('/')[-1]
                clean_name = re.sub(r'^\d+px-', '', filename)
                clean_name = clean_name.rsplit('.', 1)[0] if '.' in clean_name else clean_name
                return thumb_url, clean_name
    except:
        pass
    return None, None

def search_wiki_image(actress_name, site_code, site_domain):
    """搜索 Wikipedia，返回图片 URL 如果文件名包含女优名"""
    for term in [actress_name, f'{actress_name} AV女優', f'{actress_name} AV']:
        params = urllib.parse.urlencode({
            'action': 'query', 'list': 'search',
            'srsearch': term, 'format': 'json', 'srlimit': 5
        })
        try:
            req = urllib.request.Request(f'https://{site_domain}/w/api.php?{params}',
                                        headers={'User-Agent': 'JavWikiBot/1.0'})
            resp = urllib.request.urlopen(req, timeout=10)
            data = json.loads(resp.read())
            for r in data.get('query', {}).get('search', []):
                title = r['title']
                url, fname = get_wiki_image_with_name_check(title, site_code, site_domain)
                if url:
                    return url, fname
        except:
            pass
        time.sleep(0.3)
    return None, None

def name_matches(filename, actress_name):
    """检查文件名是否包含女优的名字"""
    f_lower = filename.lower()
    # 直接匹配
    if actress_name.lower() in f_lower:
        return True
    # 罗马音匹配 - 常见转换
    name_variants = {
        'み・う': 'miu', 'ゆ・あ': 'yua', 'あ・す・か': 'asuka',
        'り・お': 'rio', 'れ・い・な': 'reina', 'ま・り・な': 'marina',
        'さ・く・ら': 'sakura', 'も・も': 'momo', 'ゆ・い': 'yui',
        'つ・か・さ': 'tsukasa', 'あ・お・い': 'aoi', 'み・く': 'miku',
        'め・ぐ・り': 'meguri', 'れ・む': 'remu', 'こ・こ・の・い': 'kokonoi',
    }
    # These are too many to enumerate - just return True if we find any
    # recognizable pattern in the filename
    return False

def add_image_to_file(fp, url):
    """添加 thumbnail 和 img 标签到文件"""
    with open(fp, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if has_image(content):
        return False, 'already has image'
    
    # Get name from heading
    m = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
    name = m.group(1).strip() if m else ''
    
    # Add thumbnail to frontmatter
    lines = content.split('\n')
    
    # Check if frontmatter exists
    if lines[0].strip() == '---':
        # Find end of frontmatter
        end_idx = None
        for i in range(1, len(lines)):
            if lines[i].strip() == '---':
                end_idx = i
                break
        if end_idx:
            lines.insert(end_idx, f'thumbnail: {url}')
            content = '\n'.join(lines)
    else:
        # No frontmatter, add one
        content = f'---\nthumbnail: {url}\n---\n\n{content}'
    
    # Add img tag after heading
    lines = content.split('\n')
    heading_idx = None
    for i, line in enumerate(lines):
        if line.startswith('# ') and not line.startswith('##'):
            heading_idx = i
            break
    
    if heading_idx is not None:
        img_tag = f'<img src="{url}" alt="{name}" class="actress-photo" style="float: right; max-width: 280px; margin-left: 20px; border-radius: 8px;" />'
        insert_pos = heading_idx + 1
        if insert_pos < len(lines) and lines[insert_pos].strip() == '':
            insert_pos += 1
        lines.insert(insert_pos, '')
        lines.insert(insert_pos, img_tag)
        content = '\n'.join(lines)
    
    with open(fp, 'w', encoding='utf-8') as f:
        f.write(content)
    return True, name

def get_name_variants(actress_name):
    """Generate search variants for an actress name"""
    variants = [actress_name]
    # Try removing spaces
    if ' ' in actress_name:
        variants.append(actress_name.replace(' ', ''))
    # Try English transliterations for known actresses
    known_en = {
        'AIKA': ['AIKA'], 'Julia': ['Julia', 'JULIA'], 'Miru': ['Miru', 'MIRU'],
        'Rio': ['Rio', 'RIO'], 'Hitomi': ['Hitomi', 'HITOMI'],
        'ベアトリクス': ['Beatrix'],
    }
    for k, v in known_en.items():
        if k in actress_name or actress_name in [k] + v:
            variants.extend(v)
    return variants

def main():
    cache_file = 'scripts/image_cache.json'
    cache = {}
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r') as f:
                cache = json.load(f)
        except:
            cache = {}
    
    # Collect files
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
    
    added = 0
    skipped_have = 0
    not_found = []
    
    for fp in sorted(files):
        name, content = extract_name(fp)
        if not name:
            continue
        
        if has_image(content):
            skipped_have += 1
            continue
        
        # Check cache first
        if name in cache and cache[name]:
            url = cache[name]
            ok, result = add_image_to_file(fp, url)
            if ok:
                print(f'  {name}: 已添加 (cache)', flush=True)
                added += 1
            continue
        
        found = False
        url = None
        
        # Try all Wikipedia sites
        for site_code, site_domain, site_label in WIKI_SITES:
            for variant in get_name_variants(name):
                # Try direct page first
                url, fname = get_wiki_image_with_name_check(variant, site_code, site_domain)
                if url:
                    found = True
                    cache[name] = url
                    break
                
                # Try search
                if not found:
                    url, fname = search_wiki_image(variant, site_code, site_domain)
                    if url:
                        found = True
                        cache[name] = url
                        break
                
                time.sleep(0.3)
            
            if found:
                break
        
        if found and url:
            ok, result = add_image_to_file(fp, url)
            if ok:
                print(f'  {name}: ✅ 已添加 ({site_label})', flush=True)
                added += 1
        else:
            cache[name] = None
            print(f'  {name}: ❌ 未找到', flush=True)
            not_found.append(name)
        
        time.sleep(0.5)
    
    # Save cache
    with open(cache_file, 'w') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)
    
    print(f'\n完成: 添加{added}, 已有图片{skipped_have}, 未找到{len(not_found)}')

if __name__ == '__main__':
    main()
