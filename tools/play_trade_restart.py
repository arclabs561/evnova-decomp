"""Buy ten tons of Food, quit in the Trade Center, and inspect the reloaded pilot."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import resource
import signal
import subprocess
import sys
import time

from scenario_runner import Probe, click_when_available, wait_for

PORTS = {"Kania": "Port Kane", "Fomalhaut": "Snowmelt",
         "Moonrise": "Moonview", "Porto Rillia": "Ryll"}


def digest(path):
    return {"bytes": path.stat().st_size, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("binary", type=Path)
    parser.add_argument("install", type=Path, help="directory containing Nova.rez")
    parser.add_argument("output", type=Path, help="new disposable run directory")
    parser.add_argument("--port", default=18219, type=int)
    parser.add_argument("--fail-save", action="store_true",
                        help="Linux: limit the game process to 4096-byte file writes immediately before quit")
    args = parser.parse_args()
    binary, install, output = (p.resolve() for p in (args.binary, args.install, args.output))
    if not (install / "Nova.rez").is_file() or not binary.is_file():
        parser.error("missing executable or Nova.rez")
    output.mkdir(parents=True, exist_ok=False)
    (output / "EV Nova").symlink_to(install, target_is_directory=True)
    profile = output / "profile"
    env = dict(os.environ, XDG_DATA_HOME=str(profile), HOME=str(output), EVN_PROBE="1",
               EVN_PROBE_PORT=str(args.port), SDL_VIDEO_DRIVER="dummy", SDL_AUDIO_DRIVER="dummy",
               SDL_RENDER_DRIVER="software")
    probe = Probe(f"http://127.0.0.1:{args.port}")
    report = {"fault": args.fail_save, "binary": digest(binary)}
    def wait(**conditions):
        wait_for(probe, conditions, 45000)
    def click(name):
        click_when_available(probe, name, None, 5000)
    def cargo():
        data = probe.get("/probe/state?query=cargo")
        return {"credits": data["credits"], "bins": [row["tons"] for row in data["bins"]]}
    def launch():
        proc = subprocess.Popen([binary], cwd=output, env=env, stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL, preexec_fn=lambda: signal.signal(signal.SIGXFSZ, signal.SIG_IGN))
        try:
            deadline = time.monotonic() + 45
            while time.monotonic() < deadline and proc.poll() is None:
                try:
                    if probe.get("/probe/ui").get("window") == "main_menu":
                        return proc
                except OSError:
                    pass
                time.sleep(.1)
            raise RuntimeError(f"main menu unavailable (exit={proc.poll()})")
        except BaseException:
            proc.kill()
            proc.wait()
            raise
    proc = launch()
    try:
        tools = Path(__file__).resolve().parent
        subprocess.run([sys.executable, tools/"scenario_runner.py",
                        tools.parent/"tests/scenarios/fragments/new_pilot.toml",
                        "--base-url", probe.base_url, "--artifacts", output/"diagnostics"],
                       check=True, timeout=150)
        report["initial"] = cargo()
        system = probe.get("/probe/state?query=summary")["system"]
        report["port"] = PORTS[system]
        probe.post("/probe/command", {"cmd":"land_at", "target":PORTS[system], "timeout_ms":45000})
        wait(**{"ui.window":"mission_offer"})
        click("accept")
        wait(**{"ui.window":"text_reader"})
        click("done")
        wait(**{"ui.window":"spaceport"})
        click("trade_center")
        wait(**{"ui.window":"trade_center"})
        click("trade.row.0")
        ui = probe.get("/probe/ui")
        row, = [i for i in ui["items"] if i.get("selected") is True]
        assert row["label"] == "Food" and row["name"] == "trade.row.0" and row["price"] > 0, row
        report["price"] = row["price"]
        before = report["before"] = cargo()
        click("buy")
        after = report["purchased"] = cargo()
        expected = before["bins"].copy()
        expected[0] += 10
        assert after == {"credits":before["credits"]-10*row["price"], "bins":expected}, after
        (output/"purchased.bmp").write_bytes(probe.screenshot())
        pilot, = profile.rglob("*.plt")
        report["save_before_quit"] = digest(pilot)
        if args.fail_save:
            resource.prlimit(proc.pid, resource.RLIMIT_FSIZE, (4096, resource.RLIM_INFINITY))
        probe.post("/probe/command", {"cmd":"quit"})
        report["exit"] = proc.wait(timeout=15)
        assert report["exit"] == 0
        report["save_after_quit"] = digest(pilot)
        proc = launch()
        summary = probe.get("/probe/state?query=summary")
        report["loaded"] = summary["game_active"]
        report["restart"] = cargo() if report["loaded"] else None
        (output/"restart.bmp").write_bytes(probe.screenshot())
        if args.fail_save:
            assert report["save_after_quit"] == report["save_before_quit"] and report["restart"] == report["initial"], "previous save lost"
        else:
            assert report["loaded"] and report["restart"] == after, "purchase did not survive restart"
    finally:
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()
        (output/"result.json").write_text(json.dumps(report, indent=2)+"\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
