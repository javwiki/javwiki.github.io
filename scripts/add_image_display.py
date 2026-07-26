#!/usr/bin/env python3
"""
将 YAML frontmatter 中的 thumbnail 转换为页面中显示的图片
在 # 标题后添加 <img> 标签
"""
import os, re

ROWS = {'あ','か','さ','た','な','は','ま','や','ら','わ'}

def add_display_image(fp):
    with open(fp, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract thumbnail URL from frontmatter
    m = re.search(r'^thumbnail:\s*(.+)$', content, re.MULTILINE)
    if not m:
        return False, None
    
    url = m.group(1).strip()
    
    # Check if image already displayed
    if '![' in content and url.split('/')[-1] in content:
        return False, 'already displayed'
    
    if '<img' in content:
        return False, 'already has img tag'
    
    # Find the heading and add image after it
    lines = content.split('\n')
    
    # Find the # heading (first line after frontmatter)
    heading_idx = None
    for i, line in enumerate(lines):
        if line.startswith('# ') and not line.startswith('##'):
            heading_idx = i
            break
    
    if heading_idx is None:
        return False, 'no heading'
    
    # Find the next section heading after the heading
    next_section = None
    for i in range(heading_idx + 1, len(lines)):
        if lines[i].startswith('## '):
            next_section = i
            break
    
    # Get name from heading
    name = lines[heading_idx][2:].strip()
    
    # Image HTML - float right
    img_tag = f'<img src="{url}" alt="{name}" class="actress-photo" style="float: right; max-width: 280px; margin-left: 20px; border-radius: 8px;" />'
    
    # Add blank line before and after the image tag
    insert_pos = heading_idx + 1 if len(lines) > heading_idx + 1 and lines[heading_idx + 1].strip() == '' else heading_idx + 1
    
    # Insert at a good position - after heading and its following blank line
    if insert_pos < len(lines) and lines[insert_pos].strip() == '':
        insert_pos = insert_pos + 1
    
    lines.insert(insert_pos, '')
    lines.insert(insert_pos, img_tag)
    
    with open(fp, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    return True, name

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
    
    print(f'总计: {len(files)} 个文件', flush=True)
    
    added = 0
    skipped = 0
    errors = []
    
    for fp in sorted(files):
        result, name = add_display_image(fp)
        if result:
            print(f'  {name}: 已添加图片', flush=True)
            added += 1
        elif name == 'already displayed' or name == 'already has img tag':
            skipped += 1
        else:
            errors.append((fp, name))
    
    print(f'\n完成: 添加{added}, 跳过{skipped}, 错误{len(errors)}', flush=True)
    if errors:
        for fp, reason in errors:
            print(f'  错误: {fp} - {reason}', flush=True)

if __name__ == '__main__':
    main()
