#!/usr/bin/env python3
"""
删除所有女优条目中自动添加的 Wikipedia 缩略图
- 删除 frontmatter 中的 thumbnail: 行
- 删除 <img> 标签（图片显示）
"""
import os, re

ROWS = {'あ','か','さ','た','な','は','ま','や','ら','わ'}

def remove_thumbs(fp):
    with open(fp, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    changed = False
    
    # 1. Remove thumbnail: line from frontmatter
    content = re.sub(r'^thumbnail:\s*.+$\n?', '', content, flags=re.MULTILINE)
    if content != original:
        changed = True
    
    # 2. Remove <img> tag and adjacent blank lines
    content = re.sub(r'<img\s+src="[^"]*"[^>]*\/?>\n?', '', content)
    
    # 3. Clean up extra blank lines (3+ → 2)
    content = re.sub(r'\n{3,}', '\n\n', content)
    
    if changed:
        with open(fp, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

def main():
    count = 0
    for root, dirs, fnames in os.walk('src'):
        rel = os.path.relpath(root, 'src')
        parts = rel.replace(os.sep, '/').split('/')
        if not (len(parts) >= 2 and parts[0] in ROWS and len(parts[1]) == 1):
            continue
        for f in fnames:
            if f.endswith('.md') and f not in ('index.md', 'README.md'):
                fp = os.path.join(root, f)
                if remove_thumbs(fp):
                    print(f'  已清除: {f}')
                    count += 1
    
    print(f'\n完成: 清理 {count} 个文件')

if __name__ == '__main__':
    main()
