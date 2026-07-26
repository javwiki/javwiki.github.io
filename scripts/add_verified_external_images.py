#!/usr/bin/env python3
"""Add actor images manually verified against reliable external profile pages."""

from pathlib import Path

from add_wikidata_actor_images import add_image


# Local article path -> image URL from the source already cited by the article.
VERIFIED_IMAGES = {
    "src/た/つ/九十九メイ.md": (
        "https://cdn.up-timely.com/image/6/actress_main/125780/"
        "cFa9Y6dfmJowrplks2D8nDXQtnZAcSt4KSwWbXwo.jpg"
    ),
    "src/さ/し/白浜果歩.md": (
        "https://image-optimizer.osusume.dmm.co.jp/actress/sirahama_kaho.jpg"
    ),
    "src/ま/も/守屋よしの.md": (
        "https://image.yingzhiben.info/avatar/27iG534UIfE0.jpg"
    ),
    "src/は/べ/ベアトリクス.md": (
        "https://nikkan-spa.hyper-cdn.jp/wp-content/uploads/2020/04/"
        "Beako-01-550x413.jpg"
    ),
}


def main():
    added = 0
    for filename, url in VERIFIED_IMAGES.items():
        path = Path(filename)
        if add_image(path, url):
            print(f"added\t{path}\t{url}")
            added += 1
    print(f"Added {added} manually verified external images.")


if __name__ == "__main__":
    main()
