import glob, os, re

files_to_check = [
    ('河北彩花', 'src/か/か/*彩花*'),
    ('河合明日菜', 'src/か/か/*明日菜*'),
    ('神咲诗织', 'src/か/か/*神咲*'),
    ('奏音花音', 'src/か/か/*花音*'),
    ('樱空桃', 'src/さ/さ/*樱空*'),
    ('澁谷果歩', 'src/さ/し/*果歩*'),
    ('高桥圣子', 'src/た/た/*圣子*'),
    ('橘芹那', 'src/た/た/*芹那*'),
    ('七泽美亚', 'src/な/な/*美亚*'),
    ('波多野结衣', 'src/は/は/*结衣*'),
    ('桥本有菜', 'src/は/は/*有菜*'),
    ('三上悠亚', 'src/ま/み/*悠亚*'),
    ('美谷朱音', 'src/ま/み/*朱音*'),
    ('美園和花', 'src/ま/み/*和花*'),
    ('由爱可奈', 'src/や/ゆ/*由爱*'),
    ('凛音とうか', 'src/ら/り/*凛音*'),
    ('相泽南', 'src/あ/あ/*相泽*'),
    ('苍井空', 'src/あ/あ/*苍井*'),
    ('小仓由菜', 'src/あ/お/*由菜*'),
    ('伊藤舞雪', 'src/あ/い/*舞雪*'),
]

for name, pattern in files_to_check:
    matches = glob.glob(pattern)
    if matches:
        filepath = matches[0]
        print(f"--- {name} ---")
        print(f"Path: {filepath}")
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        thumbnail = None
        
        # Try YAML frontmatter for thumbnail
        yaml_match = re.search(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
        if yaml_match:
            yaml = yaml_match.group(1)
            img_match = re.search(r'thumbnail\s*:\s*(.+?)\s*$', yaml, re.MULTILINE)
            if img_match:
                thumbnail = img_match.group(1).strip().strip('"').strip("'")
        
        # Try markdown image
        if not thumbnail:
            img_tag_match = re.search(r'!\[.*?\]\(([^)]+)\)', content)
            if img_tag_match:
                thumbnail = img_tag_match.group(1)
        
        # Try <img> tag
        if not thumbnail:
            img_html_match = re.search(r'<img[^>]+src=([^\s>]+)', content)
            if img_html_match:
                thumbnail = img_html_match.group(1).strip('"').strip("'")
        
        print(f"Thumbnail URL: {thumbnail or 'NONE'}")
        if thumbnail:
            fname = thumbnail.split('/')[-1].split('?')[0]
            print(f"Filename: {fname}")
    else:
        print(f"--- {name} --- NOT FOUND")
