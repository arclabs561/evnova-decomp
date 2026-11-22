import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from play_shipyard import play


class ShipyardTest(unittest.TestCase):
    def test_selection_must_change_before_comparing_frame(self):
        def ui(selected):
            return {"window": "shipyard", "items": [{"label": "Shuttle", "name": "row",
                    "selected": selected}], "rects": {"row": [0, 0, 2, 2]}}
        with tempfile.TemporaryDirectory() as tmp, patch("play_shipyard.compare_screenshot") as compare:
            root = Path(tmp)
            for start, end, result in [(True, True, False), (False, False, False), (False, True, True)]:
                probe = Mock()
                probe.get.side_effect = [ui(start), ui(end)]
                out = root / f"{start}-{end}"
                if result:
                    play(probe, "Shuttle", root / "ref.png", out)
                    self.assertEqual(json.loads((out / "trace.json").read_text())[-1], {"result": "passed"})
                    compare.assert_called_once()
                else:
                    with self.assertRaises(ValueError):
                        play(probe, "Shuttle", root / "ref.png", out)
                    compare.assert_not_called()
                self.assertEqual(probe.post.call_count, int(not start))
