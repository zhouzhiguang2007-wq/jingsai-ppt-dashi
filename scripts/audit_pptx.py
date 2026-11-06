"""Screen an edited PPTX for slide-count, text-character and chart-value changes.

This does not detect reordered text or prove that every item is visible. Review
the rendered slides and inspect any intentionally rearranged content as well.
"""

from __future__ import annotations

import argparse
from collections import Counter
import json
import posixpath
import re
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile


A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
C = "{http://schemas.openxmlformats.org/drawingml/2006/chart}"
SLIDE_RE = re.compile(r"^ppt/slides/slide(\d+)\.xml$")
CHART_RE = re.compile(r"^ppt/charts/chart\d+\.xml$")


def slide_names(zf: ZipFile) -> list[tuple[int, str]]:
    found = []
    for name in zf.namelist():
        match = SLIDE_RE.match(name)
        if match:
            found.append((int(match.group(1)), name))
    return sorted(found)


def slide_chars(zf: ZipFile, name: str) -> Counter[str]:
    root = ET.fromstring(zf.read(name))
    fragments = [node.text or "" for node in root.iter(A + "t")]

    # SmartArt words may live in a drawing part rather than the slide XML.
    if any(node.tag.endswith("}relIds") for node in root.iter()):
        rel_name = posixpath.join(
            posixpath.dirname(name), "_rels", posixpath.basename(name) + ".rels"
        )
        if rel_name in zf.namelist():
            rels = ET.fromstring(zf.read(rel_name))
            for rel in rels:
                if not (rel.attrib.get("Type", "").endswith("/diagramDrawing")):
                    continue
                target = posixpath.normpath(
                    posixpath.join(posixpath.dirname(name), rel.attrib["Target"])
                )
                if target in zf.namelist():
                    diagram = ET.fromstring(zf.read(target))
                    fragments.extend(node.text or "" for node in diagram.iter(A + "t"))
    return Counter(char for char in "".join(fragments) if not char.isspace())


def chart_values(zf: ZipFile) -> list[tuple[str, ...]]:
    values = []
    for name in zf.namelist():
        if CHART_RE.match(name):
            root = ET.fromstring(zf.read(name))
            one = tuple(
                node.text or ""
                for cache in root.iter(C + "numCache")
                for point in cache.iter(C + "pt")
                for node in point.iter(C + "v")
            )
            values.append(one)
    return sorted(values)


def inspect(source: Path, candidate: Path) -> dict:
    with ZipFile(source) as original, ZipFile(candidate) as edited:
        src_slides = slide_names(original)
        dst_slides = slide_names(edited)
        src_ids = [number for number, _ in src_slides]
        dst_ids = [number for number, _ in dst_slides]
        dst_map = dict(dst_slides)
        text_changes = []
        for number, src_name in src_slides:
            dst_name = dst_map.get(number)
            if not dst_name:
                continue
            before = slide_chars(original, src_name)
            after = slide_chars(edited, dst_name)
            if before != after:
                missing = before - after
                added = after - before
                text_changes.append(
                    {
                        "slide": number,
                        "missing_characters": sum(missing.values()),
                        "added_characters": sum(added.values()),
                        "missing_sample": dict(list(missing.items())[:8]),
                        "added_sample": dict(list(added.items())[:8]),
                    }
                )
        src_charts = chart_values(original)
        dst_charts = chart_values(edited)
        return {
            "source_slides": len(src_ids),
            "candidate_slides": len(dst_ids),
            "slide_numbers_match": src_ids == dst_ids,
            "text_character_changes": text_changes,
            "chart_values_match": src_charts == dst_charts,
            "source_chart_values": src_charts,
            "candidate_chart_values": dst_charts,
            "screening_passed": src_ids == dst_ids
            and not text_changes
            and src_charts == dst_charts,
            "limit": "Character sets cannot detect reordering or hidden/overlapped text; inspect each rendered slide.",
        }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("candidate", type=Path)
    args = parser.parse_args()
    report = inspect(args.source, args.candidate)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["screening_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
