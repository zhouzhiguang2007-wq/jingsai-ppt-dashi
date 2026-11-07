"""Inspect native PPTX design and compare retained picture assets.

The relationship resolution and resource ownership approach is adapted from
PPT Master (https://github.com/hugohe3/ppt-master), MIT licensed, copyright
(c) 2025-2026 Hugo He. See THIRD_PARTY_NOTICES.md.

This is a diagnostic. Image re-encoding or intentional replacement can change
hashes, so every reported media difference needs visual review.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
import posixpath
import re
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile


P = "{http://schemas.openxmlformats.org/presentationml/2006/main}"
A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
R = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
REL = "{http://schemas.openxmlformats.org/package/2006/relationships}Relationship"
SLIDE_RE = re.compile(r"^ppt/slides/slide(\d+)\.xml$")


def source_part_for_relationships(rels_path: str) -> str | None:
    """Map a .rels package part to the part that owns it."""
    if rels_path == "_rels/.rels":
        return None
    marker = "/_rels/"
    if marker not in rels_path or not rels_path.endswith(".rels"):
        return None
    parent, filename = rels_path.split(marker, 1)
    return f"{parent}/{filename[:-5]}"


def resolve_relationship_target(source_part: str | None, target: str) -> str:
    """Resolve an internal OPC relationship against its owning part."""
    normalized = target.replace("\\", "/")
    if normalized.startswith("/"):
        return normalized.lstrip("/")
    base_dir = posixpath.dirname(source_part or "")
    return posixpath.normpath(posixpath.join(base_dir, normalized)).lstrip("/")


def relationship_maps(zf: ZipFile) -> tuple[dict[str, list[dict]], dict[str, dict[str, str]]]:
    edges: dict[str, list[dict]] = defaultdict(list)
    by_id: dict[str, dict[str, str]] = defaultdict(dict)
    for rels_path in sorted(name for name in zf.namelist() if name.endswith(".rels")):
        source = source_part_for_relationships(rels_path)
        if source is None:
            continue
        try:
            root = ET.fromstring(zf.read(rels_path))
        except ET.ParseError:
            continue
        for rel in root.iter(REL):
            if rel.get("TargetMode") == "External":
                continue
            target = rel.get("Target")
            if not target:
                continue
            resolved = resolve_relationship_target(source, target)
            row = {"target": resolved, "type": rel.get("Type", "")}
            edges[source].append(row)
            if rel.get("Id"):
                by_id[source][rel.get("Id", "")] = resolved
    return edges, by_id


def sha256_part(zf: ZipFile, part: str, cache: dict[str, str]) -> str | None:
    if part not in zf.namelist():
        return None
    if part not in cache:
        cache[part] = hashlib.sha256(zf.read(part)).hexdigest()
    return cache[part]


def inherited_media(
    slide_part: str,
    edges: dict[str, list[dict]],
    zf: ZipFile,
    cache: dict[str, str],
) -> list[str]:
    """Follow Slide -> Layout -> Master links to inherited image assets."""
    found: set[str] = set()
    visited = {slide_part}
    pending = [slide_part]
    while pending:
        current = pending.pop()
        for rel in edges.get(current, []):
            target = rel["target"]
            if target.startswith("ppt/media/") and current != slide_part:
                digest = sha256_part(zf, target, cache)
                if digest:
                    found.add(digest)
            if target.startswith(("ppt/slideLayouts/", "ppt/slideMasters/")) and target not in visited:
                visited.add(target)
                pending.append(target)
    return sorted(found)


def theme_identity(zf: ZipFile) -> dict:
    theme_part = "ppt/theme/theme1.xml"
    if theme_part not in zf.namelist():
        return {"colors": {}, "fonts": {}}
    root = ET.fromstring(zf.read(theme_part))
    colors: dict[str, str] = {}
    scheme = root.find(f".//{A}clrScheme")
    if scheme is not None:
        for slot in scheme:
            for color in slot:
                value = color.get("val") or color.get("lastClr")
                if value:
                    colors[slot.tag.rsplit("}", 1)[-1]] = value.upper()
                    break
    fonts: dict[str, str] = {}
    scheme = root.find(f".//{A}fontScheme")
    if scheme is not None:
        for role in ("majorFont", "minorFont"):
            node = scheme.find(f"{A}{role}/{A}latin")
            if node is not None and node.get("typeface"):
                fonts[role] = node.get("typeface", "")
    return {"colors": colors, "fonts": fonts}


def analyze(path: Path) -> dict:
    with ZipFile(path) as zf:
        names = set(zf.namelist())
        edges, by_id = relationship_maps(zf)
        cache: dict[str, str] = {}
        presentation = ET.fromstring(zf.read("ppt/presentation.xml"))
        size = presentation.find(f"{P}sldSz")
        canvas = None
        if size is not None:
            width, height = int(size.get("cx", "0")), int(size.get("cy", "0"))
            canvas = {"width_emu": width, "height_emu": height, "aspect": round(width / height, 6) if height else None}
        slides = []
        for number, slide_part in sorted((int(m.group(1)), n) for n in names if (m := SLIDE_RE.match(n))):
            root = ET.fromstring(zf.read(slide_part))
            shape_types = Counter()
            presets = Counter()
            colors = Counter()
            for node in root.iter():
                if node.tag in {P + "sp", P + "cxnSp", P + "pic", P + "graphicFrame", P + "grpSp"}:
                    shape_types[node.tag.rsplit("}", 1)[-1]] += 1
                if node.tag == A + "prstGeom" and node.get("prst"):
                    presets[node.get("prst", "")] += 1
                if node.tag == A + "srgbClr" and node.get("val"):
                    colors[node.get("val", "").upper()] += 1
            picture_hashes = []
            for blip in root.iter(A + "blip"):
                target = by_id.get(slide_part, {}).get(blip.get(R + "embed", ""))
                if target and target.startswith("ppt/media/"):
                    digest = sha256_part(zf, target, cache)
                    if digest:
                        picture_hashes.append(digest)
            chart_count = sum(1 for rel in edges.get(slide_part, []) if rel["type"].endswith("/chart"))
            slides.append({
                "slide": number,
                "part": slide_part,
                "shape_types": dict(sorted(shape_types.items())),
                "presets": dict(presets.most_common(12)),
                "observed_colors": dict(colors.most_common(12)),
                "text_characters": sum(len(node.text or "") for node in root.iter(A + "t")),
                "native_tables": sum(1 for _ in root.iter(A + "tbl")),
                "native_charts": chart_count,
                "picture_hashes": sorted(picture_hashes),
                "inherited_media_hashes": inherited_media(slide_part, edges, zf, cache),
            })
        return {"file": str(path), "canvas": canvas, "theme": theme_identity(zf), "slide_count": len(slides), "slides": slides}


def compare(source: dict, candidate: dict) -> dict:
    dst = {slide["slide"]: slide for slide in candidate["slides"]}
    changes = []
    for slide in source["slides"]:
        other = dst.get(slide["slide"])
        if other is None:
            continue
        pictures_before = Counter(slide["picture_hashes"])
        pictures_after = Counter(other["picture_hashes"])
        missing_pictures = sum((pictures_before - pictures_after).values())
        missing_background = sorted(set(slide["inherited_media_hashes"]) - set(other["inherited_media_hashes"]))
        if missing_pictures or missing_background:
            changes.append({"slide": slide["slide"], "missing_picture_occurrences": missing_pictures, "missing_inherited_media": len(missing_background)})
    return {
        "slide_count_match": source["slide_count"] == candidate["slide_count"],
        "canvas_match": source["canvas"] == candidate["canvas"],
        "media_changes_needing_visual_review": changes,
        "note": "Hashes flag missing or re-encoded assets; compare rendered slides before deciding whether content was lost.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("candidate", nargs="?", type=Path)
    parser.add_argument("--output", type=Path, help="Write the full JSON report to this file")
    args = parser.parse_args()
    report = {"source": analyze(args.source)}
    if args.candidate:
        report["candidate"] = analyze(args.candidate)
        report["comparison"] = compare(report["source"], report["candidate"])
    encoded = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
        print(json.dumps({"report": str(args.output), "source_slides": report["source"]["slide_count"], "comparison": report.get("comparison")}, ensure_ascii=False))
    else:
        print(encoded)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
