#!/usr/bin/env python3
"""
全面审计所有女优条目的缩略图，标记出可疑的图片。
规则：
- 如果图片文件名包含女优的姓名（汉字/罗马音/片假名），则标记为 "OK-命名匹配"
- 如果图片明显不是人物（Logo、风景等），标记为 "❌ 明显错误"
- 如果图片是活动照但文件名不包含姓名，标记为 "⚠️ 需确认"
- 如果无图片，标记为 "无图片"
- 将 AIKA、Julia、Miru、Rio、Hitomi 等英文名特殊处理
"""
import os, re, json

ROWS = {'あ','か','さ','た','な','は','ま','や','ら','わ'}
SCREENSHOT_KEYWORDS = [
    'logo', 'Logo', 'LOGO',
    'Tpowers_logo', 'Alice_Japan_logo',
    'MinatoMirai', 'Yokohama',
    'Tokyo_Yushun', 'Race',
    'placeholder', 'default',
]

def extract_name_from_file(fp):
    """从文件中提取女优姓名"""
    with open(fp, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Try # heading
    m = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
    if m:
        name = m.group(1).strip()
        # Clean up parenthetical additions
        name = re.sub(r'\s*[（(][^）)]*[）)]', '', name).strip()
        return name, content
    
    basename = os.path.splitext(os.path.basename(fp))[0]
    return basename, content

def get_thumbnail_url(content):
    """从 frontmatter 或 <img> 标签获取 URL"""
    m = re.search(r'^thumbnail:\s*(.+)$', content, re.MULTILINE)
    if m:
        return m.group(1).strip()
    m = re.search(r'<img\s+src="([^"]+)"', content)
    if m:
        return m.group(1).strip()
    return None

def normalize_name(name):
    """生成名字的各种变体用于匹配"""
    variants = set()
    variants.add(name)
    variants.add(name.lower())
    variants.add(name.replace(' ', '_').replace(' ', ''))
    
    # English / Romanji specific handling
    name_upper = name.upper()
    variants.add(name_upper)
    
    # For names with spaces, also add without spaces
    if ' ' in name:
        variants.add(name.replace(' ', ''))
        variants.add(name.replace(' ', '_'))
    
    # For special known actresses
    known_map = {
        'AIKA': ['AIKA', 'aika'],
        'Julia': ['Julia', 'julia', 'JULIA'],
        'Miru': ['Miru', 'miru', 'MIRU', '坂道みる'],
        'Rio': ['Rio', 'rio', 'RIO', '柚木ティナ', 'Yuzuki Tina'],
        'Hitomi': ['Hitomi', 'hitomi', 'HITOMI', '田中瞳'],
        'ベアトリクス': ['Beatrix', 'ベアトリクス'],
    }
    
    for key, alts in known_map.items():
        if name == key or name in alts:
            variants.update(alts)
    
    return variants

def check_filename_against_name(filename, name_variants):
    """检查文件名是否包含名字的任何变体"""
    fname_lower = filename.lower()
    for variant in name_variants:
        if variant.lower() in fname_lower:
            return True
        # Also check without common suffixes
        clean_var = variant.lower().replace(' ', '_').replace(' ', '')
        if clean_var in fname_lower:
            return True
    return False

def is_obviously_wrong(filename):
    """检查文件名是否明显不是人物照片"""
    for kw in SCREENSHOT_KEYWORDS:
        if kw in filename:
            return True
    # Check file extensions - PNG files are often not photos
    # Check for common non-person keywords
    fname_lower = filename.lower()
    if any(ext in fname_lower for ext in ['.png', '.svg', '.gif']):
        # Only flag PNG if it doesn't look like a photo
        if 'photo' not in fname_lower and 'portrait' not in fname_lower:
            return True
    return False

def classify_image(url, name):
    """分类图片质量"""
    if not url:
        return '无图片', ''
    
    filename = url.split('/')[-1]
    # Remove size prefixes like 330px-
    clean_filename = re.sub(r'^\d+px-', '', filename)
    # Remove extension
    name_part = os.path.splitext(clean_filename)[0]
    
    name_variants = normalize_name(name)
    
    # Check for obviously wrong
    if is_obviously_wrong(clean_filename):
        return '❌ 明显错误', f'文件名疑为非人物图片: {clean_filename}'
    
    # Check if filename contains any name variant
    if check_filename_against_name(name_part, name_variants):
        return '✅ OK', f'文件名含姓名标识: {clean_filename}'
    
    # Check if it's a Trend Girls or Kindai Mahjong event photo
    if 'Trend_Girls' in clean_filename or 'Kindai_Mahjong' in clean_filename or 'TRE' in clean_filename:
        return '⚠️ 活动照', f'活动照片,文件名无姓名: {clean_filename}'
    
    # Otherwise suspicious
    return '❓ 可疑', f'文件名无姓名匹配: {clean_filename}'

def main():
    files = []
    for root, dirs, fnames in os.walk('src'):
        rel = os.path.relpath(root, 'src')
        parts = rel.replace(os.sep, '/').split('/')
        if not (len(parts) >= 2 and parts[0] in ROWS and len(parts[1]) == 1):
            continue
        for f in fnames:
            if f.endswith('.md') and f not in ('index.md', 'README.md'):
                files.append(os.path.join(root, f))
    
    results = {
        '✅ OK': [],
        '⚠️ 活动照': [],
        '❓ 可疑': [],
        '❌ 明显错误': [],
        '无图片': [],
    }
    
    for fp in sorted(files):
        name, content = extract_name_from_file(fp)
        url = get_thumbnail_url(content)
        classification, reason = classify_image(url, name)
        results[classification].append((name, fp, url, reason))
    
    print(f'========== 女优缩略图审计报告 ==========')
    print(f'总计检查: {len(files)} 个文件\n')
    
    for category in ['❌ 明显错误', '❓ 可疑', '⚠️ 活动照', '✅ OK', '无图片']:
        items = results[category]
        print(f'\n{"="*60}')
        print(f'{category}: {len(items)} 个')
        print(f'{"="*60}')
        for name, fp, url, reason in items:
            print(f'{name}: {reason}')
            if url:
                print(f'  URL: {url}')
    
    print(f'\n\n========== 摘要 ==========')
    for category, items in results.items():
        print(f'{category}: {len(items)}')

if __name__ == '__main__':
    main()
