"""Select one visible hull and check the highlight against a reviewed frame."""
import argparse
import json
from pathlib import Path

from scenario_runner import Probe
from scenario_visual import compare_screenshot


def target_row(ui, label):
    if ui.get("window") != "shipyard":
        raise ValueError("expected an open shipyard")
    rows = [row for row in ui["items"] if row.get("label") == label]
    if len(rows) != 1 or rows[0]["name"] not in ui["rects"]:
        raise ValueError(f"expected one visible, clickable {label!r}")
    return rows[0]


def play(probe, label, reference, artifacts):
    trace = []
    artifacts.mkdir(parents=True, exist_ok=False)
    try:
        before = probe.get("/probe/ui")
        trace.append({"before": before})
        target = target_row(before, label)
        if target.get("selected") is True:
            raise ValueError(f"{label!r} is already selected; start with a different hull")
        action = {"element": target["name"]}
        trace.append({"click": action})
        probe.post("/probe/click", action)
        after = probe.get("/probe/ui")
        trace.append({"after": after})
        row = target_row(after, label)
        selected = [item["name"] for item in after["items"] if item.get("selected") is True]
        if selected != [row["name"]]:
            raise ValueError(f"expected {label!r} alone to be highlighted, saw {selected}")
        compare_screenshot(probe, {"reference": reference.name, "element": row["name"]},
                           reference.parent, artifacts)
        trace.append({"result": "passed"})
    except Exception as error:
        trace.append({"error": str(error)})
        raise
    finally:
        (artifacts / "trace.json").write_text(json.dumps(trace, indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("label")
    parser.add_argument("reference", type=Path, help="reviewed full-frame image at the same layout")
    parser.add_argument("artifacts", type=Path, help="new directory for this attempt")
    parser.add_argument("--port", default=8190, type=int)
    args = parser.parse_args()
    play(Probe(f"http://127.0.0.1:{args.port}"), args.label, args.reference, args.artifacts)
