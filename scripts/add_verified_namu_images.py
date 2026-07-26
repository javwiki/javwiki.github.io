#!/usr/bin/env python3
"""Add actor images from manually verified Namu Wiki actor pages."""

import html
import re
import urllib.parse
import urllib.request
from pathlib import Path

from add_wikidata_actor_images import add_image


USER_AGENT = "Mozilla/5.0 (compatible; JavWikiBot/1.0; +https://github.com/javwiki/javwiki.github.io)"

# Local article path -> verified Namu Wiki article title.
VERIFIED_PAGES = {
    "src/ら/り/凛音とうか.md": "린네 토우카",
    "src/ら/り/Rio.md": "리오(AV 배우)",
    "src/た/つ/蕾.md": "つぼみ",
    "src/た/た/壇玲奈.md": "단 레이나",
    "src/や/ゆ/优月真里奈.md": "유즈키 마리나",
    "src/や/ゆ/柚月向日葵.md": "유즈키 히마와리",
    "src/や/ゆ/由爱可奈.md": "미즈카와 준",
    "src/や/や/山手梨爱.md": "야마테 리아",
    "src/さ/さ/佐佐木明希.md": "사사키 아키",
    "src/さ/し/澁谷果歩.md": "시부야 카호",
    "src/さ/し/篠田步美.md": "시노다 아유미",
    "src/さ/し/筱田优.md": "시노다 유",
    "src/さ/さ/岬奈奈美.md": "미사키 나나미",
    "src/あ/う/宇流木さら.md": "우루키 사라라",
    "src/あ/い/五日市芽依.md": "이츠카이치 메이",
    "src/あ/い/饭岛爱.md": "이이지마 아이",
    "src/あ/い/市川雅美.md": "이치카와 마사미",
    "src/あ/い/一条みお.md": "이치조 미오",
    "src/あ/あ/荒木レナ.md": "아라키 레나",
    "src/あ/あ/有栖花绯.md": "나기 히카루",
    "src/あ/あ/相泽南.md": "아이자와 미나미",
    "src/あ/あ/天海翼.md": "아마미 츠바사",
    "src/あ/あ/葵百合香.md": "아오이 유리카",
    "src/あ/お/乙都咲乃.md": "오토 사키노",
    "src/な/に/西宫梦.md": "니시미야 유메",
    "src/な/に/二宫光.md": "니노미야 히카리",
    "src/な/な/成濑心美.md": "나루세 코코미",
    "src/な/な/永野一夏.md": "나가노 이치카",
    "src/な/な/永瀬ゆい.md": "나가세 유이",
    "src/か/こ/九井スナオ.md": "코코노이 스나오",
    "src/か/く/工藤ララ.md": "쿠도 라라",
    "src/か/く/红音萤.md": "아카네 호타루",
    "src/か/か/奏音花音.md": "카나데 카논",
    "src/か/き/北川绘里香.md": "키타가와 에리카",
    "src/か/き/木村愛心.md": "키무라 아코",
    "src/ま/み/水菜丽.md": "미즈나 레이",
    "src/ま/み/美乃すずめ.md": "미노 스즈메",
    "src/ま/み/美乃雀.md": "미노 스즈메",
    "src/ま/み/水卜樱.md": "미우라 사쿠라",
    "src/ま/み/未步奈奈.md": "미호 나나",
    "src/ま/み/蜜美杏.md": "미츠미 안",
    "src/は/は/羽生ありさ.md": "하뉴 아리사",
    "src/は/ふ/冬月枫.md": "후유츠키 카에데",
    "src/は/ふ/藤かんな.md": "후지 칸나",
}


def fetch_page(title):
    encoded = urllib.parse.quote(title, safe="")
    request = urllib.request.Request(
        f"https://namu.wiki/w/{encoded}", headers={"User-Agent": USER_AGENT}
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8", "replace")


def primary_image(document):
    for tag in re.findall(r"<img\b[^>]+>", document, re.IGNORECASE):
        source = re.search(
            r"""src=['"](//i\.namu\.wiki/i/[^'"]+\.webp)['"]""",
            tag,
            re.IGNORECASE,
        )
        if not source:
            continue
        alt_match = re.search(r"""alt=['"]([^'"]*)['"]""", tag, re.IGNORECASE)
        alt = html.unescape(alt_match.group(1) if alt_match else "")
        if any(word in alt.lower() for word in ("서명", "signature", "아이콘", "logo", "로고")):
            continue
        return "https:" + source.group(1)
    return None


def main():
    added = 0
    for filename, title in VERIFIED_PAGES.items():
        path = Path(filename)
        content = path.read_text(encoding="utf-8")
        if "thumbnail:" in content or re.search(r"<img\b", content, re.IGNORECASE):
            continue
        document = fetch_page(title)
        if "해당 문서를 찾을 수 없습니다" in document:
            print(f"missing\t{path}\t{title}")
            continue
        url = primary_image(document)
        if url and add_image(path, url):
            print(f"added\t{path}\t{title}")
            added += 1
        else:
            print(f"no-image\t{path}\t{title}")
    print(f"Added {added} manually verified Namu Wiki images.")


if __name__ == "__main__":
    main()
