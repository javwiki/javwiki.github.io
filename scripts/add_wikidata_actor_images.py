#!/usr/bin/env python3
"""Add identity-verified actor images from Wikidata P18 claims."""

import hashlib
import json
import re
import urllib.parse
import urllib.request
from pathlib import Path


ROWS = set("あかさたなはまやらわ")
USER_AGENT = "JavWikiBot/1.0 (https://github.com/javwiki/javwiki.github.io)"


def actor_pages():
    for path in Path("src").rglob("*.md"):
        parts = path.relative_to("src").parts
        if (
            len(parts) >= 3
            and parts[0] in ROWS
            and len(parts[1]) == 1
            and path.name not in {"index.md", "README.md"}
        ):
            yield path


def api_json(url, params):
    query = urllib.parse.urlencode(params)
    request = urllib.request.Request(f"{url}?{query}", headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def wikidata_images(qids):
    images = {}
    for start in range(0, len(qids), 50):
        data = api_json(
            "https://www.wikidata.org/w/api.php",
            {
                "action": "wbgetentities",
                "format": "json",
                "ids": "|".join(qids[start : start + 50]),
                "props": "claims",
            },
        )
        for qid, entity in data["entities"].items():
            try:
                filename = entity["claims"]["P18"][0]["mainsnak"]["datavalue"]["value"]
            except (KeyError, IndexError):
                continue
            if filename.lower().endswith((".jpg", ".jpeg")):
                images[qid] = filename
    return images


def commons_thumbnail(filename):
    normalized = filename.replace(" ", "_")
    digest = hashlib.md5(normalized.encode()).hexdigest()
    encoded = urllib.parse.quote(normalized, safe="()_',!~")
    return (
        "https://upload.wikimedia.org/wikipedia/commons/thumb/"
        f"{digest[0]}/{digest[:2]}/{encoded}/500px-{encoded}"
    )


def add_image(path, url):
    content = path.read_text(encoding="utf-8")
    if re.search(r"^thumbnail:\s*\S+", content, re.MULTILINE) or re.search(
        r"<img\b[^>]*\bsrc=", content, re.IGNORECASE
    ):
        return False

    heading = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    if not heading:
        return False
    name = re.sub(r"\s*[（(][^）)]*[）)]", "", heading.group(1)).strip()

    frontmatter = re.match(r"\A---\n(.*?)\n---", content, re.DOTALL)
    if frontmatter:
        insert_at = frontmatter.end() - 3
        content = content[:insert_at] + f"thumbnail: {url}\n" + content[insert_at:]
    else:
        content = f"---\nthumbnail: {url}\n---\n\n{content}"

    heading = re.search(r"^#\s+.+$", content, re.MULTILINE)
    image = (
        f'<img src="{url}" alt="{name}" class="actress-photo" '
        'style="float: right; max-width: 280px; margin-left: 20px; '
        'border-radius: 8px;" />'
    )
    insert_at = heading.end()
    content = content[:insert_at] + f"\n\n{image}" + content[insert_at:]
    path.write_text(content, encoding="utf-8")
    return True


def main():
    entries = []
    for path in actor_pages():
        content = path.read_text(encoding="utf-8")
        if "thumbnail:" in content or re.search(r"<img\b", content, re.IGNORECASE):
            continue
        match = re.search(r"wikidata\.org/wiki/(Q\d+)", content)
        if match:
            entries.append((path, match.group(1)))

    images = wikidata_images([qid for _, qid in entries])
    added = 0
    for path, qid in entries:
        filename = images.get(qid)
        if filename and add_image(path, commons_thumbnail(filename)):
            print(f"added\t{path}\t{qid}\t{filename}")
            added += 1
    print(f"Added {added} identity-verified JPEG images.")


if __name__ == "__main__":
    main()
