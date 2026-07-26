#!/usr/bin/env python3
"""
可靠的女优图片获取 - 只使用 Wikipedia 页面本身的图片，不使用搜索结果
（避免拿到其他人的照片）
"""
import os, re, json, urllib.request, urllib.parse, sys, time

ROWS = {'あ','か','さ','た','な','は','ま','や','ら','わ'}

# 知名女优的日文名映射 (中文名 -> 日文维基页面名)
JA_NAME_MAP = {
    'AIKA': 'AIKA',
    'Julia': 'Julia',
    'Miru': '坂道みる',
    'Rio': '柚木ティナ',
    'Hitomi': '田中瞳',
    'ベアトリクス': 'ベアトリクス',
    '天海翼': '天海つばさ',
    '安位薰': '安位薫',
    '彩美旬果': '彩美旬果',
    '新有菜': '新ありな',
    '明日花绮罗': '明日花キララ',
    '有冈美羽': '有岡みう',
    '有栖花绯': '有栖花あか',
    '朝桐光': '朝桐光',
    '朝美穗香': 'みひろ',
    '浅野心春': '浅野心',
    '相泽南': '相沢みなみ',
    '苍井空': '蒼井そら',
    '荒木レナ': '荒木レナ',
    '葵伊吹': '葵いぶき',
    '葵司': '葵つかさ',
    '葵百合香': '葵百合香',
    '麻美由真': '麻美ゆま',
    '一条みお': '一条みお',
    '五日市芽依': '五日市芽依',
    '伊藤舞雪': '伊藤舞雪',
    '市川雅美': '市川まさみ',
    '石原希望': '石原希望',
    '石川澪': '石川澪',
    '饭岛爱': '飯島愛',
    '上原亚衣': '上原亜衣',
    '宇流木さら': '宇流木さら',
    'おりん': 'おりん',
    '乙都咲乃': '乙都咲乃',
    '冲田杏梨': '沖田杏梨',
    '大槻响': '大槻ひびき',
    '奥田咲': '奥田咲',
    '小仓由菜': '小倉由菜',
    '小栗操': '小栗操',
    '小泽玛利亚': '小澤マリア',
    '小那海あや': '小那海あや',
    '小野六花': '小野六花',
    '奏音花音': '奏音かのん',
    '川北彩花': '川北彩花',
    '枫花': '楓ふうか',
    '河北彩花': '河北彩花',
    '河合明日菜': '河合あすな',
    '神咲诗织': '神咲詩織',
    '风间由美': '風間ゆみ',
    '香水纯': '香水じゅん',
    '北川ゆず': '北川ゆず',
    '北川绘里香': '北川エリカ',
    '君岛美绪': '君島みお',
    '君色花音': '君色花音',
    '君野ここ': '君野ここ',
    '希岛爱理': '希島あいり',
    '希崎洁西卡': '希崎ジェシカ',
    '希美由真': '希美まゆ',
    '吉田花': '吉田花',
    '木村愛心': '木村愛心',
    '工藤ララ': '工藤ララ',
    '红音萤': '紅音ほたる',
    '小凑四叶': '小湊よつ葉',
    '小向美奈子': '小向美奈子',
    '樱空桃': '桜空もも',
    '樱井步': '桜井あゆ',
    '樱木凛': '桜木凛',
    '东云美玲': '東雲美玲',
    '白峰美羽': '白峰ミウ',
    '白浜果歩': '白浜果歩',
    '白石茉莉奈': '白石茉莉奈',
    '筱田优': '篠田ゆう',
    '鈴村あいり': '鈴村あいり',
    '高桥圣子': '高橋しょう子',
    '鹰宫唯': '鷹宮ゆい',
    '橘芹那': '橘芹那',
    '壇玲奈': '壇玲奈',
    '千乃あずみ': '千乃あずみ',
    '九十九メイ': '九十九メイ',
    '月雲よる': '月雲よる',
    '蕾': '蕾',
    '天使萌': '天使もえ',
    '天馬ゆい': '天馬ゆい',
    '七泽美亚': '七沢みあ',
    '永瀬ゆい': '永瀬ゆい',
    '永野一夏': '永野いちか',
    '野々浦暖': '野々浦暖',
    '初美沙希': '初美沙希',
    '莲实克蕾儿': '蓮実クレア',
    '波多野结衣': '波多野結衣',
    '早川瀬里奈': '早川瀬里奈',
    '桥本有菜': '橋本ありな',
    '羽咲美晴': '羽咲みはる',
    '羽生ありさ': '羽生ありさ',
    '羽田爱': '羽田あい',
    '姫咲はな': '姫咲はな',
    '姫川ゆうな': '姫川ゆうな',
    '古川伊织': '古川いおり',
    '深田咏美': '深田えいみ',
    '藤かんな': '藤かんな',
    '冬月枫': '冬月かえで',
    'ベアトリクス': 'ベアトリクス',
    '松本一香': '松本いちか',
    '真木今日子': '真木今日子',
    '三上悠亚': '三上悠亜',
    '南梨央奈': '南梨央奈',
    '宫下玲奈': '宮下玲奈',
    '宮島めい': '宮島めい',
    '未步奈奈': '未歩なな',
    '美乃すずめ': '美乃すずめ',
    '美乃雀': '美乃雀',
    '美園和花': '美園和花',
    '美谷朱音': '美谷朱音',
    '水卜樱': '水卜さくら',
    '水菜丽': '水菜麗',
    '蜜美杏': '蜜美杏',
    '惠理': '惠理',
    '森泽佳奈': '森沢かな',
    '守屋よしの': '守屋よしの',
    '百永さりな': '百永さりな',
    '桃乃木香奈': '桃乃木かな',
    '八掛うみ': '八掛うみ',
    '八木奈奈': '八木奈々',
    '山手梨爱': '山手梨愛',
    '弥生みづき': '弥生みづき',
    '梦乃あいか': '夢乃あいか',
    '楪可怜': '楪カレン',
    '由来千岁': '由來ちさと',
    '由爱可奈': '由愛可奈',
    '由良かな': '由良かな',
    '优月真里奈': '優月まりな',
    '柚月向日葵': '柚月ひまわり',
    '吉泽明步': '吉沢明歩',
    '吉高宁宁': '吉高寧々',
    '吉川爱美': '吉川あいみ',
    '吉根ゆりあ': '吉根ゆりあ',
    '凛音とうか': '凛音とうか',
    'AIKA': 'AIKA',
}

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

def get_wiki_pageimage(wiki_name, site_domain):
    """从 Wikipedia 页面获取 pageimage（仅当页面存在且有图片）"""
    params = urllib.parse.urlencode({
        'action': 'query', 'prop': 'pageimages',
        'titles': wiki_name, 'format': 'json', 'pithumbsize': 400
    })
    url = f'https://{site_domain}/w/api.php?{params}'
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'JavWikiBot/1.0'})
        resp = urllib.request.urlopen(req, timeout=10)
        data = json.loads(resp.read())
        for pid, info in data.get('query', {}).get('pages', {}).items():
            if pid != '-1' and 'thumbnail' in info:
                thumb_url = info['thumbnail']['source']
                # Only accept JPG files (not PNG/SVG which are logos)
                if '.jpg' in thumb_url.lower() or '.jpeg' in thumb_url.lower():
                    return thumb_url
    except:
        pass
    return None

def add_image_to_file(fp, url):
    with open(fp, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if has_image(content):
        return False
    
    m = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
    name = m.group(1).strip() if m else ''
    
    lines = content.split('\n')
    
    if lines[0].strip() == '---':
        end_idx = None
        for i in range(1, len(lines)):
            if lines[i].strip() == '---':
                end_idx = i
                break
        if end_idx:
            lines.insert(end_idx, f'thumbnail: {url}')
            content = '\n'.join(lines)
    else:
        content = f'---\nthumbnail: {url}\n---\n\n{content}'
    
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
    return True

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
    have_img = 0
    not_found = []
    already = 0
    
    for fp in sorted(files):
        name, content = extract_name(fp)
        if not name:
            continue
        
        if has_image(content):
            already += 1
            continue
        
        # Get Japanese Wikipedia name from map
        ja_name = JA_NAME_MAP.get(name)
        if not ja_name:
            not_found.append(f'{name} (无日文名映射)')
            continue
        
        # Try Japanese Wikipedia first (most complete)
        url = get_wiki_pageimage(ja_name, 'ja.wikipedia.org')
        if url:
            add_image_to_file(fp, url)
            print(f'  {name}: ✅ JA', flush=True)
            added += 1
        else:
            # Try Chinese Wikipedia as fallback
            url = get_wiki_pageimage(name, 'zh.wikipedia.org')
            if url:
                add_image_to_file(fp, url)
                print(f'  {name}: ✅ ZH', flush=True)
                added += 1
            else:
                print(f'  {name}: ❌ 无图片', flush=True)
                not_found.append(name)
        
        time.sleep(0.5)
    
    print(f'\n完成: 添加{added}, 已有{already}, 未找到{len(not_found)}')
    if not_found:
        for n in not_found:
            print(f'  ❌ {n}')

if __name__ == '__main__':
    main()
