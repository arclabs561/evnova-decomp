"""Pixel and coordinate checks for the optional visual scenario action."""

import io
import json
from pathlib import Path
import tempfile
import unittest

try:
    from PIL import Image
except ImportError:
    Image = None

from scenario_visual import compare_screenshot, element_box


class ElementBoxTest(unittest.TestCase):
    def test_scaled_playfield_with_rounded_edge(self):
        ui = {"window": "port", "playfield": [203, 126, 618, 517],
              "rects": {"launch": [674, 581.5, 145, 25], "window": [203, 125.5, 618, 517]}}
        self.assertEqual(element_box(ui, "launch", (1236, 1034)), (942, 911, 1232, 961))
        self.assertEqual(element_box(ui, "window", (618, 517)), (0, 0, 618, 517))
        with self.assertRaisesRegex(ValueError, "absent"):
            element_box(ui, "unknown", (618, 517))


@unittest.skipUnless(Image, "visual checks require Pillow")
class ComparisonTest(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.path = Path(temp.name)
        self.expected = Image.new("RGB", (4, 2), (0, 0, 0))
        self.expected.save(self.path / "saved.png")
        self.actual = self.expected.copy()
        self.step = {"reference": "saved.png", "element": "button"}

    def get(self, path):
        return {"window": "test", "playfield": [4, 5, 4, 2], "rects": {"button": [5, 5, 2, 2]}}

    def screenshot(self):
        data = io.BytesIO()
        self.actual.save(data, "BMP")
        return data.getvalue()

    def compare(self, **options):
        compare_screenshot(self, self.step | options, self.path, self.path)

    def test_crop_threshold_and_change_budget(self):
        self.actual.putpixel((0, 0), (255, 255, 255))  # Outside the button.
        self.actual.putpixel((1, 0), (0, 7, 0))
        self.compare(channel_tolerance=7)
        self.compare(max_changed_pixels=1)
        with self.assertRaisesRegex(ValueError, "1 pixels differ"):
            self.compare(channel_tolerance=6)
        report = json.loads((self.path / "visual-diff.json").read_text())
        self.assertEqual(report["changed_bounds"], [0, 0, 1, 1])
        self.assertEqual(report["crop"], [1, 0, 3, 2])
        with Image.open(self.path / "visual-diff.png") as diff:
            self.assertEqual(diff.getpixel((0, 0)), (255, 0, 255))

    def test_resolution_and_vacuous_budget(self):
        with self.assertRaisesRegex(ValueError, "entire region"):
            self.compare(max_changed_pixels=4)
        self.actual = self.actual.resize((8, 4))
        with self.assertRaisesRegex(ValueError, "captured frame"):
            self.compare()
