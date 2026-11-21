"""Compare a live probe frame with a full-frame reference image."""

from __future__ import annotations

import io
import json
import math
from pathlib import Path


def element_box(ui, element, size):
    """Map a probe rectangle in window points to screenshot pixels."""
    if element not in ui["rects"]:
        raise ValueError(f"{element!r} is absent from {ui['window']!r}")
    x, y, width, height = ui["rects"][element]
    left, top, w, h = ui["playfield"]
    x -= left
    y -= top
    # Published button bounds can straddle the rounded viewport edge by half
    # a point. Intersect with what SDL actually captured.
    if w <= 0 or h <= 0 or width <= 0 or height <= 0:
        raise ValueError(f"invalid playfield or element size for {element!r}")
    box = (max(0, math.floor(x * size[0] / w)),
           max(0, math.floor(y * size[1] / h)),
           min(size[0], math.ceil((x + width) * size[0] / w)),
           min(size[1], math.ceil((y + height) * size[1] / h)))
    if box[0] >= box[2] or box[1] >= box[3]:
        raise ValueError(f"{element!r} is outside the captured playfield")
    return box


def compare_screenshot(probe, step, base_dir: Path, artifacts: Path):
    try:
        from PIL import Image, ImageChops
    except ImportError as error:
        raise ValueError("compare_screenshot requires Pillow") from error

    reference = step.get("reference")
    if not isinstance(reference, str) or not reference:
        raise ValueError("compare_screenshot requires a reference image path")
    tolerance = step.get("channel_tolerance", 0)
    budget = step.get("max_changed_pixels", 0)
    if type(tolerance) is not int or not 0 <= tolerance < 255:
        raise ValueError("channel_tolerance must be an integer from 0 to 254")
    if type(budget) is not int or budget < 0:
        raise ValueError("max_changed_pixels must be a nonnegative integer")

    with Image.open(base_dir / reference) as source:
        expected = source.convert("RGB")
    element = step.get("element")
    if element is not None and (not isinstance(element, str) or not element):
        raise ValueError("element must be a nonempty name")
    ui = probe.get("/probe/ui") if element else None
    with Image.open(io.BytesIO(probe.screenshot())) as source:
        actual = source.convert("RGB")
    if actual.size != expected.size:
        artifacts.mkdir(parents=True, exist_ok=True)
        actual.save(artifacts / "visual-actual.png")
        raise ValueError(f"reference is {expected.size}, captured frame is {actual.size}")
    box = element_box(ui, element, actual.size) if element else (0, 0, *actual.size)
    if element:
        latest = probe.get("/probe/ui")
        if (latest["window"] != ui["window"] or
                element_box(latest, element, actual.size) != box):
            raise ValueError(f"layout changed while capturing {element!r}")
    actual = actual.crop(box)
    expected = expected.crop(box)
    if budget >= actual.width * actual.height:
        raise ValueError("max_changed_pixels would allow the entire region to differ")
    red, green, blue = ImageChops.difference(expected, actual).split()
    delta = ImageChops.lighter(ImageChops.lighter(red, green), blue)
    mask = delta.point(lambda value: 255 if value > tolerance else 0)
    changed = mask.histogram()[255]
    if changed > budget:
        artifacts.mkdir(parents=True, exist_ok=True)
        expected.save(artifacts / "visual-reference.png")
        actual.save(artifacts / "visual-actual.png")
        overlay = actual.copy()
        overlay.paste((255, 0, 255), mask=mask)
        overlay.save(artifacts / "visual-diff.png")
        report = dict(reference=reference, element=element, crop=box,
                      changed_pixels=changed, max_changed_pixels=budget,
                      channel_tolerance=tolerance, changed_bounds=mask.getbbox())
        (artifacts / "visual-diff.json").write_text(json.dumps(report, indent=2) + "\n")
        raise ValueError(f"{changed} pixels differ from {reference!r} (allowed {budget})")
    print(f"visual check: {changed} changed pixels in {actual.width}x{actual.height}", flush=True)
