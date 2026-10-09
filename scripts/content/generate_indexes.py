"""Generate organization indexes and complete localized navigation from content."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from urllib.parse import quote

import yaml

ROOT = Path(__file__).resolve().parents[2]
LANGUAGES = {"zh": "zensical.toml", "ja": "zensical.ja.toml", "en": "zensical.en.toml"}
SECTION_ORDER = ("人物", "作品", "产业", "资料", "专题")
CHILD_ORDER = {
    "人物": ("女优", "男优", "导演", "组合"),
    "作品": ("单部", "系列", "番号"),
    "产业": ("制作公司", "厂牌", "经纪公司", "协会"),
    "资料": ("奖项", "活动", "排名", "法律", "术语"),
}
ROW_ORDER = tuple("あかさたなはまやらわ")
FRONT_MATTER = re.compile(r"\A---\n(.*?)\n---\n", re.S)
NAV_BLOCK = re.compile(r"# BEGIN GENERATED NAV\n.*?# END GENERATED NAV\n", re.S)
LABELS = {
    "zh": (
        "制作集团与公司",
        "制作厂牌",
        "名称",
        "类型",
        "关系",
        "集团",
        "公司",
        "品牌",
        "制作系谱",
        "发行方",
    ),
    "ja": (
        "制作グループと会社",
        "制作ブランド",
        "名称",
        "区分",
        "関係",
        "グループ",
        "会社",
        "ブランド",
        "制作系譜",
        "発売元",
    ),
    "en": (
        "Production groups and companies",
        "Production brands",
        "Name",
        "Type",
        "Relationship",
        "Group",
        "Company",
        "Brand",
        "Production lineage",
        "Publisher",
    ),
}


def metadata(page: Path) -> dict:
    match = FRONT_MATTER.match(page.read_text(encoding="utf-8"))
    return yaml.safe_load(match.group(1)) if match else {}


def title(page: Path) -> str:
    text = page.read_text(encoding="utf-8")
    data = metadata(page)
    if data.get("title"):
        return data["title"]
    match = re.search(r"^# (.+)$", text, re.M)
    if not match:
        raise ValueError(f"No page title: {page}")
    return match.group(1)


def organization_index(base: Path, directory: str, language: str) -> str:
    labels = LABELS[language]
    heading = labels[0 if directory == "制作公司" else 1]
    lines = [f"---\ntitle: {heading}\n---", "", f"# {heading}", ""]
    intro = {
        "zh": "按条目的法人与品牌类型整理。关系仅表示条目来源支持的制作系谱或发行关系。",
        "ja": "法人・ブランドの区分で整理する。関係は各項目の出典が裏づける制作系譜または発売関係を示す。",
        "en": "Organized by corporate or brand identity. Relationships describe the production lineage or publishing connection supported by each article's sources.",
    }
    lines += [
        intro[language],
        "",
        f"| {labels[2]} | {labels[3]} | {labels[4]} |",
        "| --- | --- | --- |",
    ]
    types = dict(zip(("group", "company", "brand"), labels[5:8], strict=True))
    relation_labels = {"production_lineage": labels[8], "published_by": labels[9]}
    folder = base / "产业" / directory
    for page in sorted(folder.glob("*.md")):
        if page.name == "index.md":
            continue
        data = metadata(page)
        relations = []
        for relation in data.get("relationships", []):
            target = (page.parent / relation["target"]).resolve()
            relations.append(
                f"{relation_labels[relation['type']]}: "
                f"[{title(target)}]({quote(relation['target'], safe='/.')})"
            )
        lines.append(
            f"| [{title(page)}]({quote(page.name)}) | {types[data['entity_type']]} | "
            + ("; ".join(relations) if relations else "—")
            + " |"
        )
    return "\n".join(lines) + "\n"


def navigation(base: Path, folder: Path | None = None) -> list:
    folder = base if folder is None else folder
    entries: list = []
    index = folder / "index.md"
    if index.is_file():
        entries.append(index.relative_to(base).as_posix())
    preferred = SECTION_ORDER if folder == base else CHILD_ORDER.get(folder.name, ())
    if folder.name == "女优":
        preferred = ROW_ORDER
    order = {name: number for number, name in enumerate(preferred)}
    for child in sorted(
        folder.iterdir(), key=lambda p: (order.get(p.name, len(order)), p.name)
    ):
        if child.is_dir():
            entries.append({title(child / "index.md"): navigation(base, child)})
        elif child.suffix == ".md" and child.name != "index.md":
            entries.append(child.relative_to(base).as_posix())
    return entries


def toml_nav(entries: list, indent: int = 0) -> str:
    prefix = " " * indent
    lines = ["["]
    for entry in entries:
        if isinstance(entry, str):
            lines.append(prefix + "  " + json.dumps(entry, ensure_ascii=False) + ",")
        else:
            label, children = next(iter(entry.items()))
            lines.append(
                prefix
                + "  { "
                + json.dumps(label, ensure_ascii=False)
                + " = "
                + toml_nav(children, indent + 2)
                + " },"
            )
    lines.append(prefix + "]")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Report generated-file drift without writing",
    )
    args = parser.parse_args()
    changed = []
    for language, config_name in LANGUAGES.items():
        base = ROOT / "docs" / language
        for directory in ("制作公司", "厂牌"):
            path = base / "产业" / directory / "index.md"
            content = organization_index(base, directory, language)
            if not path.exists() or path.read_text(encoding="utf-8") != content:
                changed.append(path)
                if not args.check:
                    path.write_text(content, encoding="utf-8")
        path = ROOT / config_name
        text = NAV_BLOCK.sub("", path.read_text(encoding="utf-8"))
        block = (
            "# BEGIN GENERATED NAV\nnav = "
            + toml_nav(navigation(base))
            + "\n# END GENERATED NAV\n"
        )
        text = text.replace("[project]\n", "[project]\n" + block, 1)
        if path.read_text(encoding="utf-8") != text:
            changed.append(path)
            if not args.check:
                path.write_text(text, encoding="utf-8")
    if changed:
        print("Generated files " + ("need updating:" if args.check else "updated:"))
        for path in changed:
            print(f"  {path.relative_to(ROOT)}")
    return 1 if args.check and changed else 0


if __name__ == "__main__":
    raise SystemExit(main())
